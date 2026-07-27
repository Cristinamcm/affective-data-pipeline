"""
Operações de persistência e consulta do módulo de pré-processamento.

Este módulo é responsável por:

- obter as publicações utilizadas pelo pipeline;
- criar execuções de pré-processamento;
- guardar resultados individuais;
- finalizar execuções;
- consultar resultados;
- calcular métricas agregadas.

As consultas base de Dataset e Post encontram-se centralizadas no
dataset_repository.py. Este módulo reutiliza essas operações para evitar
duplicação de código.
"""

import json
from datetime import datetime
from typing import Any

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.models import Post, ProcessedPost, ProcessingRun
from app.repositories.dataset_repository import get_posts_by_dataset


def get_posts_by_dataset_page(
    db: Session,
    dataset_id: int,
    limit: int = 100,
    offset: int = 0
) -> list[Post]:
    """
    Obtém uma página de publicações para utilização pelo módulo de processamento.

    Esta função delega a consulta ao dataset_repository, evitando repetir
    instruções SQLAlchemy em diferentes repositórios.

    Args:
        db: Sessão SQLAlchemy utilizada na consulta.
        dataset_id: Identificador do dataset.
        limit: Número máximo de publicações da página.
        offset: Número de publicações anteriores a ignorar.

    Returns:
        list[Post]: Página de publicações solicitada.
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
    Obtém todas as publicações pertencentes a um dataset.

    As publicações são consultadas através de páginas para evitar uma única
    consulta potencialmente demasiado extensa. No entanto, o resultado final
    continua a ser reunido numa lista e permanece em memória.

    Para datasets muito grandes, esta função deverá futuramente ser substituída
    por um iterador ou por processamento integral em lotes.

    Args:
        db: Sessão SQLAlchemy utilizada na consulta.
        dataset_id: Identificador do dataset.
        page_size: Número de publicações consultadas em cada página.

    Returns:
        list[Post]: Todas as publicações pertencentes ao dataset.

    Raises:
        ValueError: Quando page_size é inferior a 1.
    """

    if page_size < 1:
        raise ValueError("The page size must be greater than zero")

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

        # Quando a página contém menos registos do que o limite solicitado,
        # significa que foi alcançada a última página.
        if len(posts_page) < page_size:
            break

        offset += page_size

    return all_posts

def create_processing_run(
    db: Session,
    dataset_id: int,
    configuration_name: str,
    configuration_json: dict,
    total_posts: int
) -> ProcessingRun:
    """
    Cria o registo de uma nova execução de pré-processamento.

    A configuração aplicada é serializada em JSON para preservar as operações
    selecionadas pelo utilizador e garantir a rastreabilidade da execução.

    Args:
        db: Sessão SQLAlchemy utilizada na persistência.
        dataset_id: Identificador do dataset processado.
        configuration_name: Nome atribuído à configuração.
        configuration_json: Configuração normalizada do pipeline.
        total_posts: Número total de publicações existentes no dataset.

    Returns:
        ProcessingRun: Execução criada com o estado inicial ``started``.
    """
    
    run = ProcessingRun(
        dataset_id=dataset_id,
        configuration_name=configuration_name,
        configuration_json=json.dumps(configuration_json, ensure_ascii=False),
        total_posts=total_posts,
        status="started"
    )

    try:
        db.add(run)

        # O commit inicial garante que a execução fica registada antes de o
        # processamento das publicações começar.
        db.commit()
        db.refresh(run)

        return run

    except Exception:
        db.rollback()
        raise



def save_processed_post(
    db: Session,
    post: Post,
    run: ProcessingRun,
    processed_data: dict[str, Any],
    is_duplicate: bool = False
) -> None:
    """
    Adiciona à sessão o resultado do pré-processamento de uma publicação.

    O resultado é associado à publicação original e à execução que o produziu.
    Esta função não executa commit. A confirmação dos dados é realizada quando
    a execução termina.

    Args:
        db: Sessão SQLAlchemy utilizada na persistência.
        post: Publicação original que foi processada.
        run: Execução responsável pelo resultado.
        processed_data: Texto, elementos extraídos e métricas do pipeline.
        is_duplicate: Indica se a publicação foi identificada como duplicada.
    """

    processed_post = ProcessedPost(
        post_id=post.id,
        processing_run_id=run.id,

        # Conteúdo textual.
        original_text=processed_data["original_text"],
        processed_text=processed_data["processed_text"],

        # Estruturas serializadas em JSON.
        tokens=json.dumps(
            processed_data["tokens"],
            ensure_ascii=False
        ),
        emojis=json.dumps(
            processed_data["emojis"],
            ensure_ascii=False
        ),
        hashtags=json.dumps(
            processed_data["hashtags"],
            ensure_ascii=False
        ),
        applied_steps=json.dumps(
            processed_data["applied_steps"],
            ensure_ascii=False
        ),

        # Métricas gerais de dimensão e tokenização.
        original_length=processed_data["original_length"],
        processed_length=processed_data["processed_length"],
        word_count=processed_data["word_count"],
        token_count=processed_data["token_count"],

        # Elementos identificados no texto original.
        emoji_count=processed_data["emoji_count"],
        hashtag_count=processed_data["hashtag_count"],
        url_count=processed_data["url_count"],
        mention_count=processed_data["mention_count"],

        has_url=processed_data["has_url"],
        has_mention=processed_data["has_mention"],
        has_hashtag=processed_data["has_hashtag"],

        # Métricas específicas das transformações aplicadas.
        #
        # O método get() assegura compatibilidade temporária caso uma versão
        # anterior do pipeline ainda não devolva algum destes campos.
        urls_removed_count=processed_data.get(
            "urls_removed_count",
            0
        ),
        urls_replaced_count=processed_data.get(
            "urls_replaced_count",
            0
        ),
        mentions_anonymized_count=processed_data.get(
            "mentions_anonymized_count",
            0
        ),
        hashtags_removed_count=processed_data.get(
            "hashtags_removed_count",
            0
        ),
        emojis_preserved_count=processed_data.get(
            "emojis_preserved_count",
            0
        ),

        # Indicadores de qualidade.
        is_duplicate=is_duplicate,
        is_empty_after_processing=processed_data[
            "is_empty_after_processing"
        ]
    )

    db.add(processed_post)


def finish_processing_run(
    db: Session,
    run: ProcessingRun,
    processed_posts_count: int,
    duplicate_posts: int,
    empty_after_processing: int,
    status: str = "finished",
    error_message: str | None = None
) -> ProcessingRun:
    """
    Finaliza uma execução de pré-processamento.

    Atualiza as métricas agregadas, o estado, a eventual mensagem de erro
    e o momento de conclusão.

    O commit confirma também os ProcessedPost que tenham sido adicionados
    anteriormente à sessão.

    Args:
        db: Sessão SQLAlchemy utilizada na persistência.
        run: Execução que será finalizada.
        processed_posts_count: Número de publicações processadas.
        duplicate_posts: Número de publicações duplicadas.
        empty_after_processing: Número de textos que ficaram vazios.
        status: Estado final da execução.
        error_message: Mensagem do erro ocorrido, quando aplicável.

    Returns:
        ProcessingRun: Execução atualizada.
    """

    run.processed_posts_count = processed_posts_count
    run.duplicate_posts = duplicate_posts
    run.empty_after_processing = empty_after_processing
    run.status = status
    run.error_message = error_message
    run.finished_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(run)

        return run

    except Exception:
        db.rollback()
        raise



def get_processing_runs_by_dataset(
    db: Session,
    dataset_id: int
) -> list[ProcessingRun]:
    """
    Obtém o histórico de execuções de pré-processamento de um dataset.

    As execuções são ordenadas da mais recente para a mais antiga.

    Args:
        db: Sessão SQLAlchemy utilizada na consulta.
        dataset_id: Identificador do dataset.

    Returns:
        list[ProcessingRun]: Execuções encontradas.
    """

    return (
        db.query(ProcessingRun)
        .filter(ProcessingRun.dataset_id == dataset_id)
        .order_by(ProcessingRun.started_at.desc())
        .all()
    )


def get_processing_run_by_id(
    db: Session,
    processing_run_id: int
) -> ProcessingRun | None:
    """
    Obtém uma execução de pré-processamento através do respetivo identificador.

    Args:
        db: Sessão SQLAlchemy utilizada na consulta.
        processing_run_id: Identificador da execução.

    Returns:
        ProcessingRun | None: Execução encontrada ou ``None``.
    """

    return (
        db.query(ProcessingRun)
        .filter(ProcessingRun.id == processing_run_id)
        .first()
    )


def get_processed_posts_by_run(
    db: Session,
    processing_run_id: int,
    limit: int = 100,
    offset: int = 0
) -> list[ProcessedPost]:
    """
    Obtém uma página dos resultados produzidos por uma execução.

    Args:
        db: Sessão SQLAlchemy utilizada na consulta.
        processing_run_id: Identificador da execução.
        limit: Número máximo de resultados devolvidos.
        offset: Número de resultados ignorados antes da página atual.

    Returns:
        list[ProcessedPost]: Resultados processados encontrados.
    """

    if limit < 1:
        raise ValueError("The limit must be greater than zero")

    if offset < 0:
        raise ValueError("The offset cannot be negative")

    return (
        db.query(ProcessedPost)
        .filter(
            ProcessedPost.processing_run_id == processing_run_id
        )
        .order_by(ProcessedPost.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_processing_run_summary(
    db: Session,
    processing_run_id: int
) -> dict[str, Any] | None:
    """
    Calcula o resumo e as métricas agregadas de uma execução.

    As métricas são calculadas diretamente na base de dados através de funções
    SQL de agregação, evitando carregar todos os registos processados para a
    memória da aplicação.

    Args:
        db: Sessão SQLAlchemy utilizada na consulta.
        processing_run_id: Identificador da execução.

    Returns:
        dict[str, Any] | None: Resumo da execução ou ``None`` quando não existe.
    """

    run = get_processing_run_by_id(db, processing_run_id)

    if run is None:
        return None

    summary = (
        db.query(
            # 0 — Número de resultados armazenados.
            func.count(ProcessedPost.id),

            # 1 a 4 — Médias relacionadas com o conteúdo textual.
            func.avg(ProcessedPost.original_length),
            func.avg(ProcessedPost.processed_length),
            func.avg(ProcessedPost.word_count),
            func.avg(ProcessedPost.token_count),

            # 5 a 8 — Totais de elementos identificados.
            func.sum(ProcessedPost.emoji_count),
            func.sum(ProcessedPost.url_count),
            func.sum(ProcessedPost.mention_count),
            func.sum(ProcessedPost.hashtag_count),

            # 9 a 11 — Publicações que continham cada tipo de elemento.
            func.sum(
                case(
                    (ProcessedPost.has_url.is_(True), 1),
                    else_=0
                )
            ),
            func.sum(
                case(
                    (ProcessedPost.has_mention.is_(True), 1),
                    else_=0
                )
            ),
            func.sum(
                case(
                    (ProcessedPost.has_hashtag.is_(True), 1),
                    else_=0
                )
            ),

            # 12 e 13 — Indicadores de qualidade.
            func.sum(
                case(
                    (ProcessedPost.is_duplicate.is_(True), 1),
                    else_=0
                )
            ),
            func.sum(
                case(
                    (
                        ProcessedPost.is_empty_after_processing.is_(True),
                        1
                    ),
                    else_=0
                )
            ),

            # 14 a 18 — Totais das transformações efetuadas pelo pipeline.
            func.sum(ProcessedPost.urls_removed_count),
            func.sum(ProcessedPost.urls_replaced_count),
            func.sum(ProcessedPost.mentions_anonymized_count),
            func.sum(ProcessedPost.hashtags_removed_count),
            func.sum(ProcessedPost.emojis_preserved_count)
        )
        .filter(
            ProcessedPost.processing_run_id == processing_run_id
        )
        .first()
    )

    return {
        "processing_run_id": run.id,
        "dataset_id": run.dataset_id,
        "configuration_name": run.configuration_name,
        "configuration_json": json.loads(run.configuration_json),
        "status": run.status,
        "total_posts": run.total_posts,
        "processed_posts": run.processed_posts_count,
        "duplicate_posts": run.duplicate_posts,
        "empty_after_processing": run.empty_after_processing,
        "started_at": run.started_at,
        "finished_at": run.finished_at,

        "metrics": {
            "records": int(summary[0] or 0),

            "avg_original_length": float(summary[1] or 0),
            "avg_processed_length": float(summary[2] or 0),
            "avg_word_count": float(summary[3] or 0),
            "avg_token_count": float(summary[4] or 0),

            "total_emojis": int(summary[5] or 0),
            "total_urls": int(summary[6] or 0),
            "total_mentions": int(summary[7] or 0),
            "total_hashtags": int(summary[8] or 0),

            "posts_with_url": int(summary[9] or 0),
            "posts_with_mention": int(summary[10] or 0),
            "posts_with_hashtag": int(summary[11] or 0),

            "duplicate_posts": int(summary[12] or 0),
            "empty_after_processing": int(summary[13] or 0),

            "urls_removed_count": int(summary[14] or 0),
            "urls_replaced_count": int(summary[15] or 0),
            "mentions_anonymized_count": int(summary[16] or 0),
            "hashtags_removed_count": int(summary[17] or 0),
            "emojis_preserved_count": int(summary[18] or 0)
        }
    }