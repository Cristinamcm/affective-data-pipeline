"""
Endpoints associados ao módulo de processamento.

Este módulo disponibiliza operações para:

- consultar as operações suportadas;
- iniciar o processamento de um conjunto de dados;
- consultar o histórico de execuções;
- obter o resumo de uma execução;
- consultar as etapas executadas;
- consultar as métricas;
- consultar os resultados individuais.

A camada de API recebe e valida os pedidos, enquanto a camada de serviço
coordena a execução do pipeline.
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
from app.preprocessing.presets import (
    PREPROCESSING_PRESETS,
    SUPPORTED_OPERATIONS
)
from app.repositories.preprocessing_repository import (
    get_pipeline_metrics_by_run,
    get_processed_posts_by_run,
    get_processing_run_by_id,
    get_processing_run_summary,
    get_processing_runs_by_dataset,
    get_processing_steps_by_run
)
from app.schemas.preprocessing_schema import (
    PreprocessingRequest
)
from app.services.preprocessing_service import (
    preprocess_dataset
)


router = APIRouter(
    prefix="/preprocessing",
    tags=["Preprocessing"]
)


@router.get("/presets")
def list_preprocessing_presets():
    """
    Devolve as operações suportadas e as configurações predefinidas.
    """

    return {
        "supported_operations": (
            SUPPORTED_OPERATIONS
        ),
        "presets": (
            PREPROCESSING_PRESETS
        )
    }


@router.post("/datasets/{dataset_id}/run")
def run_preprocessing(
    dataset_id: int,
    request: PreprocessingRequest,
    db: Session = Depends(get_db)
):
    """
    Inicia uma execução de processamento sobre um conjunto de dados.
    """

    try:
        return preprocess_dataset(
            db=db,
            dataset_id=dataset_id,
            configuration_name=(
                request.configuration_name
            ),
            config=request.config
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


@router.get("/datasets/{dataset_id}/runs")
def list_dataset_processing_runs(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtém o histórico de execuções de processamento de um conjunto de dados.
    """

    runs = get_processing_runs_by_dataset(
        db=db,
        dataset_id=dataset_id
    )

    return [
        {
            "id": run.id,
            "dataset_id": (
                run.dataset_id
            ),
            "configuration_name": (
                run.configuration_name
            ),
            "configuration_json": (
                json.loads(
                    run.configuration_json
                )
                if run.configuration_json
                else {}
            ),
            "pipeline_version": (
                run.pipeline_version
            ),
            "total_posts": (
                run.total_posts
            ),
            "processed_posts": (
                run.processed_posts_count
            ),
            "failed_posts": (
                run.failed_posts_count
            ),
            "duplicate_posts": (
                run.duplicate_posts
            ),
            "empty_after_processing": (
                run.empty_after_processing
            ),
            "duration_ms": (
                run.duration_ms
            ),
            "status": (
                run.status
            ),
            "error_message": (
                run.error_message
            ),
            "started_at": (
                run.started_at
            ),
            "finished_at": (
                run.finished_at
            )
        }
        for run in runs
    ]


@router.get("/runs/{processing_run_id}/summary")
def get_run_summary(
    processing_run_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtém o resumo e as métricas de uma execução.
    """

    summary = get_processing_run_summary(
        db=db,
        processing_run_id=(
            processing_run_id
        )
    )

    if summary is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Execução de processamento "
                "não encontrada."
            )
        )

    return summary


@router.get("/runs/{processing_run_id}/steps")
def list_processing_steps(
    processing_run_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtém as etapas executadas numa determinada execução.
    """

    run = get_processing_run_by_id(
        db=db,
        processing_run_id=(
            processing_run_id
        )
    )

    if run is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Execução de processamento "
                "não encontrada."
            )
        )

    steps = get_processing_steps_by_run(
        db=db,
        processing_run_id=(
            processing_run_id
        )
    )

    return [
        {
            "id": step.id,
            "processing_run_id": (
                step.processing_run_id
            ),
            "step_name": (
                step.step_name
            ),
            "step_order": (
                step.step_order
            ),
            "configuration_json": (
                json.loads(
                    step.configuration_json
                )
                if step.configuration_json
                else {}
            ),
            "status": (
                step.status
            ),
            "rows_received": (
                step.rows_received
            ),
            "rows_changed": (
                step.rows_changed
            ),
            "rows_failed": (
                step.rows_failed
            ),
            "duration_ms": (
                step.duration_ms
            ),
            "started_at": (
                step.started_at
            ),
            "finished_at": (
                step.finished_at
            )
        }
        for step in steps
    ]


@router.get("/runs/{processing_run_id}/metrics")
def list_processing_metrics(
    processing_run_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtém as métricas calculadas numa execução.
    """

    run = get_processing_run_by_id(
        db=db,
        processing_run_id=(
            processing_run_id
        )
    )

    if run is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Execução de processamento "
                "não encontrada."
            )
        )

    metrics = get_pipeline_metrics_by_run(
        db=db,
        processing_run_id=(
            processing_run_id
        )
    )

    return [
        {
            "id": metric.id,
            "processing_run_id": (
                metric.processing_run_id
            ),
            "processing_step_id": (
                metric.processing_step_id
            ),
            "metric_name": (
                metric.metric_name
            ),
            "metric_value": (
                metric.metric_value
            ),
            "numerator": (
                metric.numerator
            ),
            "denominator": (
                metric.denominator
            ),
            "unit": (
                metric.unit
            ),
            "description": (
                metric.description
            ),
            "created_at": (
                metric.created_at
            )
        }
        for metric in metrics
    ]


@router.get("/runs/{processing_run_id}/posts")
def list_processed_posts_by_run(
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
    Obtém uma página dos resultados individuais produzidos por uma execução.
    """

    run = get_processing_run_by_id(
        db=db,
        processing_run_id=(
            processing_run_id
        )
    )

    if run is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Execução de processamento "
                "não encontrada."
            )
        )

    processed_posts = (
        get_processed_posts_by_run(
            db=db,
            processing_run_id=(
                processing_run_id
            ),
            limit=limit,
            offset=offset
        )
    )

    return [
        {
            "id": post.id,

            "post_id": (
                post.post_id
            ),

            "processing_run_id": (
                post.processing_run_id
            ),

            "original_text": (
                post.original_text
            ),

            "processed_text": (
                post.processed_text
            ),

            "tokens": (
                json.loads(post.tokens)
                if post.tokens
                else []
            ),

            "original_length": (
                post.original_length
            ),

            "processed_length": (
                post.processed_length
            ),

            "original_word_count": (
                post.original_word_count
            ),

            "processed_word_count": (
                post.processed_word_count
            ),

            "token_count": (
                post.token_count
            ),

            "is_duplicate": (
                post.is_duplicate
            ),

            "is_empty_after_processing": (
                post.is_empty_after_processing
            ),

            "processed_at": (
                post.processed_at
            )
        }
        for post in processed_posts
    ]