"""
Endpoints associados ao módulo de pré-processamento.

Este módulo disponibiliza operações para:

- consultar as operações e configurações predefinidas;
- iniciar o pré-processamento de um dataset;
- consultar o histórico de execuções;
- obter o resumo e as métricas de uma execução;
- consultar os resultados individuais produzidos.

A camada de API recebe e valida os pedidos, enquanto a camada de serviço
coordena a execução do pipeline.
"""

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.preprocessing.presets import PREPROCESSING_PRESETS, SUPPORTED_OPERATIONS
from app.repositories.preprocessing_repository import (
    get_processed_posts_by_run,
    get_processing_run_summary,
    get_processing_runs_by_dataset
)
from app.schemas.preprocessing_schema import PreprocessingRequest
from app.services.preprocessing_service import preprocess_dataset

# Router responsável pelas operações de preparação textual.
#
# Todos os endpoints ficam agrupados sob o prefixo /preprocessing.
router = APIRouter(prefix="/preprocessing", tags=["Preprocessing"])


@router.get("/presets")
def list_preprocessing_presets():
    """
    Devolve as operações suportadas e as configurações predefinidas.

    Esta informação permite ao frontend construir dinamicamente a interface
    de configuração do pipeline, apresentando ao utilizador as operações
    disponíveis e os presets existentes.

    Returns:
        dict: Operações suportadas e configurações predefinidas.
    """
    return {
        "supported_operations": SUPPORTED_OPERATIONS,
        "presets": PREPROCESSING_PRESETS
    }


@router.post("/datasets/{dataset_id}/run")
def run_preprocessing(
    dataset_id: int,
    request: PreprocessingRequest,
    db: Session = Depends(get_db)
):
    """
    Inicia uma execução de pré-processamento sobre um dataset.

    A configuração recebida é validada pelo schema PreprocessingRequest e
    enviada para a camada de serviço, que coordena o pipeline, a deteção
    de duplicados, o cálculo de métricas e a persistência dos resultados.

    Args:
        dataset_id: Identificador do dataset que será processado.
        request: Nome e configuração das operações selecionadas.
        db: Sessão SQLAlchemy disponibilizada pelo FastAPI.

    Returns:
        dict: Resumo da execução concluída.

    Raises:
        HTTPException: Quando o pedido é inválido, o dataset não existe
        ou ocorre um erro interno durante o processamento.
    """    
    try:
        result = preprocess_dataset(
            db=db,
            dataset_id=dataset_id,
            configuration_name=request.configuration_name,
            config=request.config
        )

        return result

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
    Obtém o histórico de execuções de pré-processamento de um dataset.

    Cada execução contém a configuração aplicada, as métricas gerais,
    o estado e os momentos de início e conclusão.

    Args:
        dataset_id: Identificador do dataset.
        db: Sessão SQLAlchemy disponibilizada pelo FastAPI.

    Returns:
        list[dict]: Execuções do dataset, ordenadas da mais recente
        para a mais antiga.
    """    
    runs = get_processing_runs_by_dataset(
        db=db,
        dataset_id=dataset_id
    )

    return [
        {
            "id": run.id,
            "dataset_id": run.dataset_id,
            "configuration_name": run.configuration_name,
            "configuration_json": json.loads(run.configuration_json),
            "total_posts": run.total_posts,
            "processed_posts": run.processed_posts_count,
            "duplicate_posts": run.duplicate_posts,
            "empty_after_processing": run.empty_after_processing,
            "status": run.status,
            "error_message": run.error_message,
            "started_at": run.started_at,
            "finished_at": run.finished_at
        }
        for run in runs
    ]


@router.get("/runs/{processing_run_id}/summary")
def get_run_summary(
    processing_run_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtém o resumo e as métricas agregadas de uma execução.

    As métricas incluem a dimensão média dos textos, elementos identificados,
    transformações aplicadas, duplicados e textos vazios.

    Args:
        processing_run_id: Identificador da execução.
        db: Sessão SQLAlchemy disponibilizada pelo FastAPI.

    Returns:
        dict: Metadados e métricas agregadas da execução.

    Raises:
        HTTPException: Quando a execução não existe.
    """    
    summary = get_processing_run_summary(
        db=db,
        processing_run_id=processing_run_id
    )

    if summary is None:
        raise HTTPException(
            status_code=404,
            detail="Processing run not found"
        )

    return summary


@router.get("/runs/{processing_run_id}/posts")
def list_processed_posts_by_run(
    processing_run_id: int,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Obtém uma página dos resultados individuais de uma execução.

    Para cada publicação são devolvidos o texto original, o texto processado,
    os elementos extraídos, as operações aplicadas e as métricas calculadas.

    Args:
        processing_run_id: Identificador da execução.
        limit: Número máximo de resultados da página.
        offset: Número de resultados ignorados.
        db: Sessão SQLAlchemy disponibilizada pelo FastAPI.

    Returns:
        list[dict]: Resultados processados da execução.

    Raises:
        HTTPException: Quando a execução não existe.
    """    
    processed_posts = get_processed_posts_by_run(
        db=db,
        processing_run_id=processing_run_id,
        limit=limit,
        offset=offset
    )

    return [
        {
            "id": post.id,
            "post_id": post.post_id,
            "processing_run_id": post.processing_run_id,
            "original_text": post.original_text,
            "processed_text": post.processed_text,
            "tokens": json.loads(post.tokens) if post.tokens else [],
            "emojis": json.loads(post.emojis) if post.emojis else [],
            "hashtags": json.loads(post.hashtags) if post.hashtags else [],
            "applied_steps": json.loads(post.applied_steps) if post.applied_steps else [],
            "original_length": post.original_length,
            "processed_length": post.processed_length,
            "word_count": post.word_count,
            "token_count": post.token_count,
            "emoji_count": post.emoji_count,
            "hashtag_count": post.hashtag_count,
            "url_count": post.url_count,
            "mention_count": post.mention_count,
            "has_url": post.has_url,
            "has_mention": post.has_mention,
            "has_hashtag": post.has_hashtag,
            # Quantidades das transformações efetivamente realizadas.
            "urls_removed_count": post.urls_removed_count,
            "urls_replaced_count": post.urls_replaced_count,
            "mentions_anonymized_count": (
                post.mentions_anonymized_count
            ),
            "hashtags_removed_count": post.hashtags_removed_count,
            "emojis_preserved_count": post.emojis_preserved_count,            
            "is_duplicate": post.is_duplicate,
            "is_empty_after_processing": post.is_empty_after_processing,
            "processed_at": post.processed_at
        }
        for post in processed_posts
    ]