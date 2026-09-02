"""
Operações de persistência e consulta associadas ao módulo de processamento.

Este módulo é responsável por:

- obter os registos utilizados pelo pipeline;
- criar execuções de processamento;
- registar as etapas executadas;
- armazenar os resultados individuais;
- armazenar métricas agregadas;
- finalizar execuções;
- consultar execuções, etapas, métricas e resultados.

As consultas base relacionadas com Dataset e Post permanecem centralizadas
no dataset_repository.py.
"""

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import (
    PipelineMetric,
    Post,
    ProcessedPost,
    ProcessingRun,
    ProcessingStep
)
from app.repositories.dataset_repository import get_posts_by_dataset


def _utc_now():
    """
    Devolve a data e hora atual em UTC.
    """

    return datetime.now(UTC)


def _load_json(
    value: str | None,
    default: Any = None
):
    """
    Desserializa um valor JSON armazenado como texto.
    """

    if value is None:
        return default

    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


# =============================================================================
# CONSULTA DOS REGISTOS ORIGINAIS
# =============================================================================


def get_posts_by_dataset_page(
    db: Session,
    dataset_id: int,
    limit: int = 100,
    offset: int = 0
) -> list[Post]:
    """
    Obtém uma página de registos para processamento.
    """

    return get_posts_by_dataset(
        db=db,
        dataset_id=dataset_id,
        limit=limit,
        offset=offset
    )


def get_all_posts_by_dataset(
    db: Session,
    dataset_id: int,
    page_size: int = 1000
) -> list[Post]:
    """
    Obtém todos os registos pertencentes a um conjunto de dados.

    A consulta é efetuada por páginas, embora o resultado final ainda seja
    reunido numa lista.

    Futuramente esta função poderá ser substituída por processamento
    integral em lotes para conjuntos de dados muito grandes.
    """

    if page_size < 1:
        raise ValueError(
            "O tamanho da página deve ser superior a zero."
        )

    all_posts: list[Post] = []
    offset = 0

    while True:

        posts_page = get_posts_by_dataset_page(
            db=db,
            dataset_id=dataset_id,
            limit=page_size,
            offset=offset
        )

        if not posts_page:
            break

        all_posts.extend(posts_page)

        if len(posts_page) < page_size:
            break

        offset += page_size

    return all_posts


# =============================================================================
# EXECUÇÕES DE PROCESSAMENTO
# =============================================================================


def create_processing_run(
    db: Session,
    dataset_id: int,
    configuration_name: str,
    configuration_json: dict,
    total_posts: int,
    pipeline_version: str = "1.0"
) -> ProcessingRun:
    """
    Cria uma nova execução de processamento.

    A configuração é armazenada em JSON para garantir rastreabilidade
    e permitir reproduzir posteriormente o mesmo processamento.
    """

    run = ProcessingRun(
        dataset_id=dataset_id,
        configuration_name=configuration_name,
        configuration_json=json.dumps(
            configuration_json,
            ensure_ascii=False
        ),
        pipeline_version=pipeline_version,
        total_posts=total_posts,
        processed_posts_count=0,
        failed_posts_count=0,
        duplicate_posts=0,
        empty_after_processing=0,
        status="started"
    )

    try:
        db.add(run)

        # A execução é confirmada imediatamente para garantir que existe
        # um registo persistido mesmo que o processamento falhe depois.
        db.commit()
        db.refresh(run)

        return run

    except Exception:
        db.rollback()
        raise


def finish_processing_run(
    db: Session,
    run: ProcessingRun,
    processed_posts_count: int,
    failed_posts_count: int,
    duplicate_posts: int,
    empty_after_processing: int,
    duration_ms: int | None,
    status: str = "completed",
    error_message: str | None = None
) -> ProcessingRun:
    """
    Finaliza uma execução de processamento.

    O commit realizado nesta função confirma também os registos processados,
    etapas e métricas adicionados anteriormente à sessão.
    """

    run.processed_posts_count = processed_posts_count
    run.failed_posts_count = failed_posts_count
    run.duplicate_posts = duplicate_posts
    run.empty_after_processing = empty_after_processing
    run.duration_ms = duration_ms
    run.status = status
    run.error_message = error_message
    run.finished_at = _utc_now()

    try:
        db.commit()
        db.refresh(run)

        return run

    except Exception:
        db.rollback()
        raise


# =============================================================================
# ETAPAS DE PROCESSAMENTO
# =============================================================================


def create_processing_step(
    db: Session,
    processing_run_id: int,
    step_name: str,
    step_order: int,
    configuration_json: dict | None = None
) -> ProcessingStep:
    """
    Regista uma operação selecionada para uma determinada execução.
    """

    step = ProcessingStep(
        processing_run_id=processing_run_id,
        step_name=step_name,
        step_order=step_order,
        configuration_json=(
            json.dumps(
                configuration_json,
                ensure_ascii=False
            )
            if configuration_json is not None
            else None
        ),
        status="started"
    )

    db.add(step)

    # É necessário obter o ID antes do commit final.
    db.flush()

    return step


def finish_processing_step(
    db: Session,
    step: ProcessingStep,
    rows_received: int,
    rows_changed: int,
    rows_failed: int = 0,
    duration_ms: int | None = None,
    status: str = "completed"
) -> ProcessingStep:
    """
    Atualiza uma etapa após a respetiva execução.
    """

    step.rows_received = rows_received
    step.rows_changed = rows_changed
    step.rows_failed = rows_failed
    step.duration_ms = duration_ms
    step.status = status
    step.finished_at = _utc_now()

    db.flush()

    return step


# =============================================================================
# REGISTOS PROCESSADOS
# =============================================================================


def save_processed_post(
    db: Session,
    post: Post,
    run: ProcessingRun,
    processed_data: dict[str, Any],
    is_duplicate: bool = False
) -> ProcessedPost:
    """
    Adiciona à sessão o resultado do processamento de um registo.

    Esta tabela contém apenas informação diretamente relacionada com
    a preparação textual.

    Emojis, hashtags e outros indicadores afetivos deixam de ser persistidos
    nesta tabela, porque serão posteriormente armazenados no módulo de
    enriquecimento afetivo.
    """

    original_text = str(
        processed_data.get(
            "original_text",
            post.original_text
        )
    )

    processed_text = str(
        processed_data.get(
            "processed_text",
            ""
        )
    )

    tokens = processed_data.get("tokens", [])

    original_word_count = processed_data.get(
        "original_word_count"
    )

    if original_word_count is None:
        original_word_count = (
            len(original_text.split())
            if original_text
            else 0
        )

    processed_word_count = processed_data.get(
        "processed_word_count"
    )

    if processed_word_count is None:
        processed_word_count = processed_data.get(
            "word_count"
        )

    if processed_word_count is None:
        processed_word_count = (
            len(processed_text.split())
            if processed_text
            else 0
        )

    processed_post = ProcessedPost(
        post_id=post.id,
        processing_run_id=run.id,

        original_text=original_text,
        processed_text=processed_text,

        tokens=json.dumps(
            tokens,
            ensure_ascii=False
        ),

        original_length=processed_data.get(
            "original_length",
            len(original_text)
        ),

        processed_length=processed_data.get(
            "processed_length",
            len(processed_text)
        ),

        original_word_count=original_word_count,
        processed_word_count=processed_word_count,

        token_count=processed_data.get(
            "token_count",
            len(tokens)
        ),

        is_duplicate=is_duplicate,

        is_empty_after_processing=processed_data.get(
            "is_empty_after_processing",
            not bool(processed_text.strip())
        )
    )

    db.add(processed_post)

    return processed_post


# =============================================================================
# MÉTRICAS
# =============================================================================


def save_pipeline_metric(
    db: Session,
    processing_run_id: int,
    metric_name: str,
    metric_value: float,
    numerator: int | None = None,
    denominator: int | None = None,
    unit: str | None = None,
    description: str | None = None,
    processing_step_id: int | None = None
) -> PipelineMetric:
    """
    Guarda uma métrica calculada durante uma execução.

    O numerador e denominador são preservados quando a métrica representa
    uma proporção, permitindo manter os valores que deram origem ao resultado.
    """

    metric = PipelineMetric(
        processing_run_id=processing_run_id,
        processing_step_id=processing_step_id,
        metric_name=metric_name,
        metric_value=float(metric_value),
        numerator=numerator,
        denominator=denominator,
        unit=unit,
        description=description
    )

    db.add(metric)

    return metric


# =============================================================================
# CONSULTAS
# =============================================================================


def get_processing_runs_by_dataset(
    db: Session,
    dataset_id: int
) -> list[ProcessingRun]:
    """
    Obtém o histórico de execuções de um conjunto de dados.
    """

    return (
        db.query(ProcessingRun)
        .filter(
            ProcessingRun.dataset_id == dataset_id
        )
        .order_by(
            ProcessingRun.started_at.desc()
        )
        .all()
    )


def get_processing_run_by_id(
    db: Session,
    processing_run_id: int
) -> ProcessingRun | None:
    """
    Obtém uma execução através do respetivo identificador.
    """

    return (
        db.query(ProcessingRun)
        .filter(
            ProcessingRun.id == processing_run_id
        )
        .first()
    )


def get_processing_steps_by_run(
    db: Session,
    processing_run_id: int
) -> list[ProcessingStep]:
    """
    Obtém as etapas associadas a uma execução.
    """

    return (
        db.query(ProcessingStep)
        .filter(
            ProcessingStep.processing_run_id
            == processing_run_id
        )
        .order_by(
            ProcessingStep.step_order.asc()
        )
        .all()
    )


def get_pipeline_metrics_by_run(
    db: Session,
    processing_run_id: int,
    only_global: bool = False
) -> list[PipelineMetric]:
    """
    Obtém as métricas associadas a uma execução.

    Quando only_global=True, são devolvidas apenas as métricas que não estão
    associadas a uma etapa específica.
    """

    query = (
        db.query(PipelineMetric)
        .filter(
            PipelineMetric.processing_run_id
            == processing_run_id
        )
    )

    if only_global:
        query = query.filter(
            PipelineMetric.processing_step_id.is_(None)
        )

    return (
        query
        .order_by(PipelineMetric.id.asc())
        .all()
    )


def get_processed_posts_by_run(
    db: Session,
    processing_run_id: int,
    limit: int = 100,
    offset: int = 0
) -> list[ProcessedPost]:
    """
    Obtém uma página dos resultados produzidos por uma execução.
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
        db.query(ProcessedPost)
        .filter(
            ProcessedPost.processing_run_id
            == processing_run_id
        )
        .order_by(
            ProcessedPost.id.asc()
        )
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_processing_run_summary(
    db: Session,
    processing_run_id: int
) -> dict[str, Any] | None:
    """
    Obtém o resumo de uma execução.

    As métricas específicas do pipeline são obtidas da tabela
    metricas_processamento.

    As médias diretamente relacionadas com os textos são calculadas
    através da tabela registos_processados.
    """

    run = get_processing_run_by_id(
        db=db,
        processing_run_id=processing_run_id
    )

    if run is None:
        return None

    summary = (
        db.query(
            func.count(ProcessedPost.id),

            func.avg(
                ProcessedPost.original_length
            ),

            func.avg(
                ProcessedPost.processed_length
            ),

            func.avg(
                ProcessedPost.original_word_count
            ),

            func.avg(
                ProcessedPost.processed_word_count
            ),

            func.avg(
                ProcessedPost.token_count
            )
        )
        .filter(
            ProcessedPost.processing_run_id
            == processing_run_id
        )
        .first()
    )

    metrics = get_pipeline_metrics_by_run(
        db=db,
        processing_run_id=processing_run_id,
        only_global=True
    )

    metrics_dict = {}

    for metric in metrics:
        metrics_dict[metric.metric_name] = {
            "value": metric.metric_value,
            "numerator": metric.numerator,
            "denominator": metric.denominator,
            "unit": metric.unit,
            "description": metric.description
        }

    return {
        "processing_run_id": run.id,
        "dataset_id": run.dataset_id,

        "configuration_name": (
            run.configuration_name
        ),

        "configuration_json": _load_json(
            run.configuration_json,
            {}
        ),

        "pipeline_version": (
            run.pipeline_version
        ),

        "status": run.status,

        "total_posts": run.total_posts,

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

        "duration_ms": run.duration_ms,

        "started_at": run.started_at,
        "finished_at": run.finished_at,

        "text_statistics": {
            "records": int(
                summary[0] or 0
            ),

            "avg_original_length": float(
                summary[1] or 0
            ),

            "avg_processed_length": float(
                summary[2] or 0
            ),

            "avg_original_word_count": float(
                summary[3] or 0
            ),

            "avg_processed_word_count": float(
                summary[4] or 0
            ),

            "avg_token_count": float(
                summary[5] or 0
            )
        },

        "metrics": metrics_dict
    }