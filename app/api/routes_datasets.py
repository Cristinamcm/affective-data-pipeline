"""
Endpoints associados à gestão e consulta de conjuntos de dados.

Este módulo disponibiliza operações para:

- pré-visualizar ficheiros CSV existentes na área de armazenamento bruto;
- importar ficheiros CSV para a base de dados;
- registar metadados relativos à origem do ficheiro;
- listar os conjuntos de dados;
- consultar os respetivos metadados;
- consultar os registos originais.

A camada de API valida os parâmetros recebidos e delega as operações de
persistência ao dataset_repository.
"""

import hashlib
from pathlib import Path

import pandas as pd
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.dataset_repository import (
    create_dataset_with_posts,
    get_dataset_by_id,
    get_datasets,
    get_posts_by_dataset
)


router = APIRouter(
    prefix="/datasets",
    tags=["Datasets"]
)


RAW_DATA_DIR = Path(
    "data/raw"
)


def _resolve_raw_file(
    input_filename: str
) -> Path:
    """
    Obtém o caminho absoluto de um ficheiro existente na área de dados brutos.

    Impede que sejam consultados caminhos externos ao diretório data/raw.
    """

    raw_directory = RAW_DATA_DIR.resolve()

    input_path = (
        raw_directory
        / input_filename
    ).resolve()

    if (
        input_path != raw_directory
        and raw_directory
        not in input_path.parents
    ):
        raise HTTPException(
            status_code=400,
            detail="Caminho de ficheiro inválido."
        )

    if not input_path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Ficheiro não encontrado: "
                f"{input_filename}"
            )
        )

    return input_path


def _calculate_file_hash(
    file_path: Path
) -> str:
    """
    Calcula o hash SHA-256 de um ficheiro.
    """

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        while True:
            chunk = file.read(
                1024 * 1024
            )

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def _normalize_delimiter(
    delimiter: str
) -> str:
    """
    Converte a representação textual de tabulação para o carácter real.
    """

    if delimiter == "\\t":
        return "\t"

    return delimiter


@router.get("/csv/preview")
def preview_csv(
    input_filename: str = Query(...),
    encoding: str = Query(
        default="utf-8"
    ),
    delimiter: str = Query(
        default=","
    )
):
    """
    Pré-visualiza um ficheiro CSV antes da importação.
    """

    input_path = _resolve_raw_file(
        input_filename
    )

    separator = _normalize_delimiter(
        delimiter
    )

    try:
        df = pd.read_csv(
            input_path,
            encoding=encoding,
            sep=separator
        )

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=(
                "Não foi possível ler o ficheiro CSV: "
                f"{error}"
            )
        )

    return {
        "input_filename": input_filename,
        "rows_count": len(df),
        "columns": list(df.columns),
        "encoding": encoding,
        "delimiter": delimiter,
        "preview": (
            df.head(5)
            .where(
                pd.notna(df.head(5)),
                None
            )
            .to_dict(
                orient="records"
            )
        )
    }


@router.post("/import-csv")
def import_csv_dataset(
    input_filename: str = Query(...),
    dataset_name: str = Query(...),
    source: str = Query(
        default="Kaggle"
    ),
    text_column: str = Query(...),
    id_column: str | None = Query(
        default=None
    ),
    label_column: str | None = Query(
        default=None
    ),
    language: str | None = Query(
        default=None
    ),
    encoding: str = Query(
        default="utf-8"
    ),
    delimiter: str = Query(
        default=","
    ),
    db: Session = Depends(get_db)
):
    """
    Importa um ficheiro CSV para a base de dados.
    """

    input_path = _resolve_raw_file(
        input_filename
    )

    separator = _normalize_delimiter(
        delimiter
    )

    try:
        df = pd.read_csv(
            input_path,
            encoding=encoding,
            sep=separator
        )

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=(
                "Não foi possível ler o ficheiro CSV: "
                f"{error}"
            )
        )

    # ------------------------------------------------------------------
    # Validar mapeamento
    # ------------------------------------------------------------------

    if text_column not in df.columns:
        raise HTTPException(
            status_code=400,
            detail=(
                f"A coluna de texto '{text_column}' "
                "não existe no ficheiro."
            )
        )

    if (
        id_column
        and id_column not in df.columns
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                f"A coluna de ID '{id_column}' "
                "não existe no ficheiro."
            )
        )

    if (
        label_column
        and label_column not in df.columns
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                f"A coluna de rótulo '{label_column}' "
                "não existe no ficheiro."
            )
        )

    file_hash = _calculate_file_hash(
        input_path
    )

    # ------------------------------------------------------------------
    # Persistir
    # ------------------------------------------------------------------

    dataset = create_dataset_with_posts(
        db=db,
        name=dataset_name,
        source=source,
        original_filename=input_filename,
        raw_file_path=str(input_path),
        file_hash=file_hash,
        id_column=id_column,
        text_column=text_column,
        label_column=label_column,
        encoding=encoding,
        delimiter=delimiter,
        language=language,
        df=df
    )

    return {
        "dataset_id": dataset.id,
        "name": dataset.name,
        "source": dataset.source,
        "original_filename": (
            dataset.original_filename
        ),
        "raw_file_path": (
            dataset.raw_file_path
        ),
        "file_hash": dataset.file_hash,
        "rows_count": dataset.rows_count,
        "id_column": dataset.id_column,
        "text_column": dataset.text_column,
        "label_column": (
            dataset.label_column
        ),
        "encoding": dataset.encoding,
        "delimiter": dataset.delimiter,
        "language": dataset.language,
        "created_at": dataset.created_at
    }


@router.get("")
def list_datasets(
    db: Session = Depends(get_db)
):
    """
    Lista todos os conjuntos de dados registados.
    """

    datasets = get_datasets(
        db
    )

    return [
        {
            "id": dataset.id,
            "name": dataset.name,
            "source": dataset.source,
            "original_filename": (
                dataset.original_filename
            ),
            "rows_count": (
                dataset.rows_count
            ),
            "id_column": (
                dataset.id_column
            ),
            "text_column": (
                dataset.text_column
            ),
            "label_column": (
                dataset.label_column
            ),
            "encoding": (
                dataset.encoding
            ),
            "delimiter": (
                dataset.delimiter
            ),
            "language": (
                dataset.language
            ),
            "created_at": (
                dataset.created_at
            )
        }
        for dataset in datasets
    ]


@router.get("/{dataset_id}")
def get_dataset(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtém os metadados de um conjunto de dados específico.
    """

    dataset = get_dataset_by_id(
        db,
        dataset_id
    )

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Conjunto de dados não encontrado."
            )
        )

    return {
        "id": dataset.id,
        "name": dataset.name,
        "source": dataset.source,
        "original_filename": (
            dataset.original_filename
        ),
        "raw_file_path": (
            dataset.raw_file_path
        ),
        "file_hash": dataset.file_hash,
        "rows_count": dataset.rows_count,
        "id_column": dataset.id_column,
        "text_column": dataset.text_column,
        "label_column": (
            dataset.label_column
        ),
        "encoding": dataset.encoding,
        "delimiter": dataset.delimiter,
        "language": dataset.language,
        "created_at": dataset.created_at
    }


@router.get("/{dataset_id}/posts")
def list_dataset_posts(
    dataset_id: int,
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
    Obtém uma página dos registos originais de um conjunto de dados.
    """

    dataset = get_dataset_by_id(
        db,
        dataset_id
    )

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Conjunto de dados não encontrado."
            )
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
            "dataset_id": (
                post.dataset_id
            ),
            "external_id": (
                post.external_id
            ),
            "original_text": (
                post.original_text
            ),
            "original_label": (
                post.original_label
            ),
            "inserted_at": (
                post.inserted_at
            )
        }
        for post in posts
    ]