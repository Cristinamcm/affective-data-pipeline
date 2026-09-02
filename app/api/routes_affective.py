"""
Endpoints associados ao módulo de enriquecimento afetivo.

Este módulo permite:

- executar o enriquecimento afetivo;
- consultar características extraídas;
- consultar estatísticas agregadas.
"""

import json

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query
)

from sqlalchemy.orm import Session

from app.database import get_db

from app.repositories.affective_repository import (
    get_affective_features_by_run,
    get_affective_summary_by_run
)

from app.repositories.preprocessing_repository import (
    get_processing_run_by_id
)

from app.schemas.affective_schema import (
    AffectiveEnrichmentRequest
)

from app.services.affective_service import (
    AFFECTIVE_EXTRACTOR_VERSION,
    enrich_processing_run
)


router = APIRouter(
    prefix="/affective",
    tags=["Affective Enrichment"]
)


def _load_json_list(
    value: str | None
) -> list:
    """
    Desserializa uma lista armazenada em JSON.
    """

    if not value:
        return []

    try:
        result = json.loads(
            value
        )

        return (
            result
            if isinstance(
                result,
                list
            )
            else []
        )

    except (
        TypeError,
        json.JSONDecodeError
    ):
        return []


# =============================================================================
# EXECUTAR ENRIQUECIMENTO
# =============================================================================

@router.post(
    "/runs/{processing_run_id}/enrich"
)
def enrich_run(
    processing_run_id: int,
    request: AffectiveEnrichmentRequest,
    db: Session = Depends(get_db)
):
    """
    Executa o enriquecimento afetivo de uma execução de pré-processamento.
    """

    try:

        return enrich_processing_run(
            db=db,
            processing_run_id=processing_run_id,
            language=request.language
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# =============================================================================
# RESUMO
# =============================================================================

@router.get(
    "/runs/{processing_run_id}/summary"
)
def get_affective_summary(
    processing_run_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtém o resumo das características afetivas de uma execução.
    """

    run = get_processing_run_by_id(
        db=db,
        processing_run_id=processing_run_id
    )

    if run is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Execução de pré-processamento "
                "não encontrada."
            )
        )

    summary = get_affective_summary_by_run(
        db=db,
        processing_run_id=processing_run_id
    )

    return {
        "processing_run_id": (
            processing_run_id
        ),

        "dataset_id": (
            run.dataset_id
        ),

        "extractor_version": (
            AFFECTIVE_EXTRACTOR_VERSION
        ),

        "summary": summary
    }


# =============================================================================
# CARACTERÍSTICAS INDIVIDUAIS
# =============================================================================

@router.get(
    "/runs/{processing_run_id}/features"
)
def list_affective_features(
    processing_run_id: int,
    limit: int = Query(
        default=100,
        ge=1,
        le=1000
    ),
    offset: int = Query(
        default=0,
        ge=0
    ),
    db: Session = Depends(get_db)
):
    """
    Obtém uma página das características afetivas extraídas.
    """

    run = get_processing_run_by_id(
        db=db,
        processing_run_id=processing_run_id
    )

    if run is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Execução de pré-processamento "
                "não encontrada."
            )
        )

    rows = get_affective_features_by_run(
        db=db,
        processing_run_id=processing_run_id,
        limit=limit,
        offset=offset
    )

    return [
        {
            "id": feature.id,

            "processed_post_id": (
                processed_post.id
            ),

            "post_id": (
                processed_post.post_id
            ),

            "original_text": (
                processed_post.original_text
            ),

            "processed_text": (
                processed_post.processed_text
            ),

            "emojis": _load_json_list(
                feature.emojis
            ),

            "emoji_count": (
                feature.emoji_count
            ),

            "hashtags": _load_json_list(
                feature.hashtags
            ),

            "hashtag_count": (
                feature.hashtag_count
            ),

            "affective_terms": (
                _load_json_list(
                    feature.affective_terms
                )
            ),

            "affective_term_count": (
                feature.affective_term_count
            ),

            "uppercase_ratio": (
                feature.uppercase_ratio
            ),

            "exclamation_count": (
                feature.exclamation_count
            ),

            "question_count": (
                feature.question_count
            ),

            "repeated_characters_count": (
                feature.repeated_characters_count
            ),

            "intensity_score": (
                feature.intensity_score
            ),

            "created_at": (
                feature.created_at
            )
        }

        for (
            feature,
            processed_post
        ) in rows
    ]