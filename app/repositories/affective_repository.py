"""
Operações de persistência e consulta associadas ao enriquecimento afetivo.

Este módulo é responsável por:

- obter registos processados;
- criar ou atualizar características afetivas;
- consultar características afetivas;
- calcular estatísticas agregadas por execução de pré-processamento.

Cada registo processado possui, na versão atual do modelo, no máximo um
conjunto de características afetivas associado.
"""

import json
from typing import Any

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.models import (
    AffectiveFeature,
    ProcessedPost
)


# =============================================================================
# REGISTOS PROCESSADOS
# =============================================================================

def get_processed_posts_for_affective_enrichment(
    db: Session,
    processing_run_id: int,
    limit: int = 1000,
    offset: int = 0
) -> list[ProcessedPost]:
    """
    Obtém uma página de registos processados para enriquecimento afetivo.
    """

    if limit < 1:
        raise ValueError(
            "O limite deve ser superior a zero."
        )

    if offset < 0:
        raise ValueError(
            "O offset não pode ser negativo."
        )

    return (
        db.query(
            ProcessedPost
        )
        .filter(
            ProcessedPost.processing_run_id
            == processing_run_id
        )
        .order_by(
            ProcessedPost.id.asc()
        )
        .offset(
            offset
        )
        .limit(
            limit
        )
        .all()
    )


# =============================================================================
# PERSISTÊNCIA
# =============================================================================

def save_or_update_affective_feature(
    db: Session,
    processed_post_id: int,
    feature_data: dict[str, Any]
) -> tuple[AffectiveFeature, bool]:
    """
    Cria ou atualiza as características afetivas de um registo processado.

    Como a relação atual é 1:1, uma nova execução do enriquecimento sobre
    o mesmo registo atualiza os valores existentes em vez de criar duplicados.

    Returns:
        tuple:
            - AffectiveFeature persistida;
            - True quando foi criado um novo registo;
            - False quando um registo existente foi atualizado.
    """

    feature = (
        db.query(
            AffectiveFeature
        )
        .filter(
            AffectiveFeature.processed_post_id
            == processed_post_id
        )
        .first()
    )

    created = False

    if feature is None:

        feature = AffectiveFeature(
            processed_post_id=(
                processed_post_id
            )
        )

        db.add(
            feature
        )

        created = True

    feature.emojis = json.dumps(
        feature_data.get(
            "emojis",
            []
        ),
        ensure_ascii=False
    )

    feature.emoji_count = int(
        feature_data.get(
            "emoji_count",
            0
        )
    )

    feature.hashtags = json.dumps(
        feature_data.get(
            "hashtags",
            []
        ),
        ensure_ascii=False
    )

    feature.hashtag_count = int(
        feature_data.get(
            "hashtag_count",
            0
        )
    )

    feature.affective_terms = json.dumps(
        feature_data.get(
            "affective_terms",
            []
        ),
        ensure_ascii=False
    )

    feature.affective_term_count = int(
        feature_data.get(
            "affective_term_count",
            0
        )
    )

    feature.uppercase_ratio = float(
        feature_data.get(
            "uppercase_ratio",
            0.0
        )
    )

    feature.exclamation_count = int(
        feature_data.get(
            "exclamation_count",
            0
        )
    )

    feature.question_count = int(
        feature_data.get(
            "question_count",
            0
        )
    )

    feature.repeated_characters_count = int(
        feature_data.get(
            "repeated_characters_count",
            0
        )
    )

    feature.intensity_score = float(
        feature_data.get(
            "intensity_score",
            0.0
        )
    )

    return feature, created


# =============================================================================
# CONSULTA DOS RESULTADOS
# =============================================================================

def get_affective_features_by_run(
    db: Session,
    processing_run_id: int,
    limit: int = 100,
    offset: int = 0
):
    """
    Obtém uma página das características afetivas de uma execução.

    É devolvido simultaneamente o registo processado associado para permitir
    apresentar os textos no frontend.
    """

    if limit < 1:
        raise ValueError(
            "O limite deve ser superior a zero."
        )

    if offset < 0:
        raise ValueError(
            "O offset não pode ser negativo."
        )

    return (
        db.query(
            AffectiveFeature,
            ProcessedPost
        )
        .join(
            ProcessedPost,
            AffectiveFeature.processed_post_id
            == ProcessedPost.id
        )
        .filter(
            ProcessedPost.processing_run_id
            == processing_run_id
        )
        .order_by(
            ProcessedPost.id.asc()
        )
        .offset(
            offset
        )
        .limit(
            limit
        )
        .all()
    )


# =============================================================================
# RESUMO
# =============================================================================

def get_affective_summary_by_run(
    db: Session,
    processing_run_id: int
) -> dict[str, Any]:
    """
    Calcula estatísticas agregadas das características afetivas.
    """

    summary = (
        db.query(

            # 0
            func.count(
                AffectiveFeature.id
            ),

            # 1-3
            func.sum(
                AffectiveFeature.emoji_count
            ),

            func.sum(
                AffectiveFeature.hashtag_count
            ),

            func.sum(
                AffectiveFeature.affective_term_count
            ),

            # 4-6
            func.avg(
                AffectiveFeature.uppercase_ratio
            ),

            func.avg(
                AffectiveFeature.intensity_score
            ),

            func.max(
                AffectiveFeature.intensity_score
            ),

            # 7-9
            func.sum(
                AffectiveFeature.exclamation_count
            ),

            func.sum(
                AffectiveFeature.question_count
            ),

            func.sum(
                AffectiveFeature.repeated_characters_count
            ),

            # 10
            func.sum(
                case(
                    (
                        AffectiveFeature.emoji_count > 0,
                        1
                    ),
                    else_=0
                )
            ),

            # 11
            func.sum(
                case(
                    (
                        AffectiveFeature.hashtag_count > 0,
                        1
                    ),
                    else_=0
                )
            ),

            # 12
            func.sum(
                case(
                    (
                        AffectiveFeature.affective_term_count > 0,
                        1
                    ),
                    else_=0
                )
            ),

            # 13
            func.sum(
                case(
                    (
                        AffectiveFeature.exclamation_count > 0,
                        1
                    ),
                    else_=0
                )
            ),

            # 14
            func.sum(
                case(
                    (
                        AffectiveFeature.question_count > 0,
                        1
                    ),
                    else_=0
                )
            ),

            # 15
            func.sum(
                case(
                    (
                        AffectiveFeature.repeated_characters_count > 0,
                        1
                    ),
                    else_=0
                )
            )
        )
        .join(
            ProcessedPost,
            AffectiveFeature.processed_post_id
            == ProcessedPost.id
        )
        .filter(
            ProcessedPost.processing_run_id
            == processing_run_id
        )
        .first()
    )

    return {
        "records": int(
            summary[0] or 0
        ),

        "total_emojis": int(
            summary[1] or 0
        ),

        "total_hashtags": int(
            summary[2] or 0
        ),

        "total_affective_terms": int(
            summary[3] or 0
        ),

        "avg_uppercase_ratio": float(
            summary[4] or 0.0
        ),

        "avg_intensity_score": float(
            summary[5] or 0.0
        ),

        "max_intensity_score": float(
            summary[6] or 0.0
        ),

        "total_exclamations": int(
            summary[7] or 0
        ),

        "total_questions": int(
            summary[8] or 0
        ),

        "total_repeated_characters": int(
            summary[9] or 0
        ),

        "records_with_emojis": int(
            summary[10] or 0
        ),

        "records_with_hashtags": int(
            summary[11] or 0
        ),

        "records_with_affective_terms": int(
            summary[12] or 0
        ),

        "records_with_exclamations": int(
            summary[13] or 0
        ),

        "records_with_questions": int(
            summary[14] or 0
        ),

        "records_with_repeated_characters": int(
            summary[15] or 0
        )
    }