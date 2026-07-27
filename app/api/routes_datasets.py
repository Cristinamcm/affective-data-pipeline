"""
Endpoints associados à gestão e consulta de datasets.

Este módulo disponibiliza operações para:

- pré-visualizar ficheiros CSV existentes na área de armazenamento bruto;
- importar um ficheiro CSV para a base de dados;
- listar os datasets registados;
- consultar os metadados de um dataset;
- consultar as publicações originais de um dataset.

A camada de API valida os parâmetros recebidos e delega as operações de
persistência ao dataset_repository.
"""

from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.dataset_repository import (
    create_dataset_with_posts,
    get_dataset_by_id,
    get_datasets,
    get_posts_by_dataset
)


# Router responsável pelos endpoints relacionados com datasets.
#
# Todos os endpoints definidos neste módulo ficam acessíveis através
# do prefixo /datasets e agrupados sob a etiqueta "Datasets" na
# documentação automática do FastAPI.
router = APIRouter(prefix="/datasets", tags=["Datasets"])

# Diretório utilizado para armazenar os ficheiros CSV na sua forma original,
# antes da importação e estruturação na base de dados.
RAW_DATA_DIR = Path("data/raw")

# rota para fazer o preview do csv
@router.get("/csv/preview")
def preview_csv(
    input_filename: str = Query(...)
):
    input_path = RAW_DATA_DIR / input_filename

    if not input_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Ficheiro não encontrado: {input_path}"
        )

    df = pd.read_csv(input_path)

    return {
        "input_filename": input_filename,
        "rows_count": len(df),
        "columns": list(df.columns),
        "preview": df.head(5).to_dict(orient="records")
    }


#importação do dataset csv para a base de dados
@router.post("/import-csv")
def import_csv_dataset(
    input_filename: str = Query(...),
    dataset_name: str = Query(...),
    source: str = Query(default="Kaggle"),
    text_column: str = Query(...),
    id_column: str | None = Query(default=None),
    db: Session = Depends(get_db)
):
    input_path = RAW_DATA_DIR / input_filename

    if not input_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Ficheiro não encontrado: {input_path}"
        )

    df = pd.read_csv(input_path)

    if text_column not in df.columns:
        raise HTTPException(
            status_code=400,
            detail=f"A coluna de texto '{text_column}' não existe no ficheiro."
        )

    if id_column and id_column not in df.columns:
        raise HTTPException(
            status_code=400,
            detail=f"A coluna de ID '{id_column}' não existe no ficheiro."
        )

    dataset = create_dataset_with_posts(
        db=db,
        name=dataset_name,
        source=source,
        original_filename=input_filename,
        id_column=id_column,
        text_column=text_column,
        df=df
    )

    return {
        "dataset_id": dataset.id,
        "name": dataset.name,
        "source": dataset.source,
        "original_filename": dataset.original_filename,
        "rows_count": dataset.rows_count,
        "id_column": dataset.id_column,
        "text_column": dataset.text_column,
        "created_at": dataset.created_at
    }


@router.get("")
def list_datasets(
    db: Session = Depends(get_db)
):
    """
    Lista todos os datasets registados no sistema.

    Os resultados são devolvidos do dataset mais recente para o mais antigo.

    Args:
        db: Sessão SQLAlchemy disponibilizada pelo FastAPI.

    Returns:
        list[dict]: Lista com os metadados dos datasets registados.
    """    
    datasets = get_datasets(db)
    # Converte cada modelo ORM numa estrutura serializável para JSON.
    return [
        {
            "id": dataset.id,
            "name": dataset.name,
            "source": dataset.source,
            "original_filename": dataset.original_filename,
            "rows_count": dataset.rows_count,
            "id_column": dataset.id_column,
            "text_column": dataset.text_column,
            "created_at": dataset.created_at
        }
        for dataset in datasets
    ]


@router.get("/{dataset_id}")
def get_dataset(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtém os metadados de um dataset específico.

    Args:
        dataset_id: Identificador interno do dataset.
        db: Sessão SQLAlchemy disponibilizada pelo FastAPI.

    Returns:
        dict: Metadados do dataset encontrado.

    Raises:
        HTTPException: Quando não existe um dataset com o ID indicado.
    """    
    dataset = get_dataset_by_id(db, dataset_id)

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset não encontrado."
        )

    return {
        "id": dataset.id,
        "name": dataset.name,
        "source": dataset.source,
        "original_filename": dataset.original_filename,
        "rows_count": dataset.rows_count,
        "id_column": dataset.id_column,
        "text_column": dataset.text_column,
        "created_at": dataset.created_at
    }


@router.get("/{dataset_id}/posts")
def list_dataset_posts(
    dataset_id: int,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Obtém uma página das publicações originais de um dataset.

    A paginação evita devolver todas as publicações de datasets grandes num
    único pedido HTTP.

    Args:
        dataset_id: Identificador do dataset.
        limit: Número máximo de publicações devolvidas.
        offset: Número de publicações ignoradas antes da página atual.
        db: Sessão SQLAlchemy disponibilizada pelo FastAPI.

    Returns:
        list[dict]: Publicações originais da página solicitada.

    Raises:
        HTTPException: Quando o dataset não existe.
    """
    dataset = get_dataset_by_id(db, dataset_id)

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset não encontrado."
        )

    posts = get_posts_by_dataset(
        db=db,
        dataset_id=dataset_id,
        limit=limit,
        offset=offset
    )

    return [
        {
            "id": post.id,
            "dataset_id": post.dataset_id,
            "external_id": post.external_id,
            "original_text": post.original_text,
            "inserted_at": post.inserted_at
        }
        for post in posts
    ]