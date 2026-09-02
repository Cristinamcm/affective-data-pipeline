"""
Serviço responsável pela coordenação do enriquecimento afetivo.

O serviço recebe uma execução de pré-processamento concluída e extrai
características afetivas dos respetivos registos processados.

As características produzidas são persistidas na tabela
caracteristicas_afetivas.
"""

from sqlalchemy.orm import Session

from app.preprocessing.affective_feature_extractor import (
    extract_affective_features,
    normalize_language
)

from app.repositories.affective_repository import (
    get_affective_summary_by_run,
    get_processed_posts_for_affective_enrichment,
    save_or_update_affective_feature
)

from app.repositories.preprocessing_repository import (
    get_processing_run_by_id
)


AFFECTIVE_EXTRACTOR_VERSION = "1.0"


def enrich_processing_run(
    db: Session,
    processing_run_id: int,
    language: str | None = None,
    page_size: int = 1000
) -> dict:
    """
    Executa o enriquecimento afetivo sobre todos os resultados pertencentes
    a uma execução de pré-processamento.

    O processamento é efetuado por páginas para evitar carregar todos os
    registos simultaneamente em memória.
    """

    if page_size < 1:
        raise ValueError(
            "O tamanho da página deve ser superior a zero."
        )

    # =========================================================================
    # VALIDAR EXECUÇÃO
    # =========================================================================

    run = get_processing_run_by_id(
        db=db,
        processing_run_id=processing_run_id
    )

    if run is None:
        raise ValueError(
            "Execução de pré-processamento não encontrada."
        )

    # Compatibilidade com eventuais execuções antigas que utilizem "finished".
    if run.status not in {
        "completed",
        "finished"
    }:
        raise ValueError(
            "O enriquecimento afetivo apenas pode ser executado "
            "sobre uma execução de pré-processamento concluída."
        )

    # =========================================================================
    # IDIOMA
    # =========================================================================

    requested_language = (
        language
        or getattr(
            run.dataset,
            "language",
            None
        )
    )

    normalized_language = normalize_language(
        requested_language
    )

    # Um idioma não suportado não impede a extração dos restantes indicadores.
    # Apenas a extração lexical ficará vazia.
    lexical_language = (
        normalized_language
    )

    # =========================================================================
    # PROCESSAMENTO
    # =========================================================================

    offset = 0

    enriched_records = 0
    created_records = 0
    updated_records = 0

    try:

        while True:

            processed_posts = (
                get_processed_posts_for_affective_enrichment(
                    db=db,
                    processing_run_id=processing_run_id,
                    limit=page_size,
                    offset=offset
                )
            )

            if not processed_posts:
                break

            for processed_post in processed_posts:

                feature_data = (
                    extract_affective_features(
                        original_text=(
                            processed_post.original_text
                            or ""
                        ),
                        processed_text=(
                            processed_post.processed_text
                            or ""
                        ),
                        language=lexical_language
                    )
                )

                _, created = (
                    save_or_update_affective_feature(
                        db=db,
                        processed_post_id=(
                            processed_post.id
                        ),
                        feature_data=feature_data
                    )
                )

                if created:
                    created_records += 1

                else:
                    updated_records += 1

                enriched_records += 1

            # Envia os dados do lote para a base de dados sem concluir
            # ainda a transação global.
            db.flush()

            if len(
                processed_posts
            ) < page_size:
                break

            offset += page_size

        if enriched_records == 0:
            raise ValueError(
                "A execução selecionada não possui registos processados."
            )

        db.commit()

    except Exception:

        db.rollback()
        raise

    # =========================================================================
    # RESUMO
    # =========================================================================

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

        "language": (
            lexical_language
        ),

        "extractor_version": (
            AFFECTIVE_EXTRACTOR_VERSION
        ),

        "enriched_records": (
            enriched_records
        ),

        "created_records": (
            created_records
        ),

        "updated_records": (
            updated_records
        ),

        "summary": summary
    }