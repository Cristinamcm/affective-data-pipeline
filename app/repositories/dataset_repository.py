"""
Operações de persistência e consulta relacionadas com conjuntos de dados
e registos originais.

Este módulo centraliza o acesso à base de dados para:

- criar conjuntos de dados;
- armazenar os registos originais importados;
- preservar o conteúdo bruto recebido;
- listar os conjuntos de dados disponíveis;
- consultar um conjunto de dados específico;
- obter páginas de registos associados a um conjunto de dados.

As operações relacionadas com execuções e resultados do processamento
permanecem no módulo preprocessing_repository.py.
"""

import json
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.models.models import Dataset, Post


def _normalize_value(value: Any):
    """
    Converte valores provenientes do pandas para tipos que possam ser
    serializados de forma segura.

    Valores nulos são convertidos para None e valores NumPy são convertidos
    para os respetivos tipos Python sempre que possível.
    """

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, AttributeError):
            pass

    return value


def _serialize_row(row: pd.Series) -> str:
    """
    Serializa uma linha completa do DataFrame para JSON.

    Esta representação permite preservar o conteúdo original recebido,
    mesmo quando o conjunto de dados contém colunas que não são utilizadas
    diretamente pelo modelo normalizado do sistema.
    """

    payload = {
        str(column): _normalize_value(value)
        for column, value in row.to_dict().items()
    }

    return json.dumps(
        payload,
        ensure_ascii=False,
        default=str
    )


def create_dataset_with_posts(
    db: Session,
    name: str,
    source: str,
    original_filename: str,
    id_column: str | None,
    text_column: str,
    df: pd.DataFrame,
    raw_file_path: str | None = None,
    file_hash: str | None = None,
    label_column: str | None = None,
    encoding: str | None = None,
    delimiter: str | None = None,
    language: str | None = None,
    batch_size: int = 1000
) -> Dataset:
    """
    Cria um conjunto de dados e armazena os respetivos registos originais.

    Cada linha do DataFrame é transformada num registo da tabela 'registos'.

    Para além dos campos normalizados, é preservada uma representação JSON
    da linha original, permitindo manter informação proveniente de conjuntos
    de dados heterogéneos.

    Args:
        db:
            Sessão SQLAlchemy.

        name:
            Nome atribuído ao conjunto de dados.

        source:
            Origem dos dados.

        original_filename:
            Nome original do ficheiro.

        id_column:
            Coluna utilizada como identificador externo.

        text_column:
            Coluna que contém o texto.

        df:
            DataFrame importado.

        raw_file_path:
            Caminho do ficheiro bruto armazenado.

        file_hash:
            Hash do ficheiro original.

        label_column:
            Coluna que contém o rótulo original, quando existente.

        encoding:
            Codificação utilizada na leitura do ficheiro.

        delimiter:
            Delimitador utilizado.

        language:
            Idioma predominante do conjunto de dados, quando conhecido.

        batch_size:
            Número de registos adicionados à sessão por lote.

    Returns:
        Dataset:
            Conjunto de dados criado.
    """

    if batch_size < 1:
        raise ValueError("O tamanho do lote deve ser superior a zero.")

    dataset = Dataset(
        name=name,
        source=source,
        original_filename=original_filename,
        raw_file_path=raw_file_path,
        file_hash=file_hash,
        rows_count=len(df),
        id_column=id_column,
        text_column=text_column,
        label_column=label_column,
        encoding=encoding,
        delimiter=delimiter,
        language=language
    )

    try:
        db.add(dataset)

        # Obtém o identificador do conjunto de dados antes de criar
        # os registos associados.
        db.flush()

        posts_batch: list[Post] = []

        for index, row in df.iterrows():

            # -------------------------------------------------------------
            # Identificador externo
            # -------------------------------------------------------------

            if id_column and id_column in df.columns:
                external_id = _normalize_value(row[id_column])

                if external_id is None:
                    external_id = index + 1

            else:
                external_id = index + 1

            # -------------------------------------------------------------
            # Texto original
            # -------------------------------------------------------------

            original_text = _normalize_value(row[text_column])

            if original_text is None:
                original_text = ""

            # -------------------------------------------------------------
            # Rótulo original
            # -------------------------------------------------------------

            original_label = None

            if label_column and label_column in df.columns:
                label_value = _normalize_value(row[label_column])

                if label_value is not None:
                    if isinstance(label_value, (dict, list, tuple)):
                        original_label = json.dumps(
                            label_value,
                            ensure_ascii=False,
                            default=str
                        )
                    else:
                        original_label = str(label_value)

            # -------------------------------------------------------------
            # Conteúdo bruto
            # -------------------------------------------------------------

            raw_payload = _serialize_row(row)

            post = Post(
                dataset_id=dataset.id,
                external_id=str(external_id),
                original_text=str(original_text),
                original_label=original_label,
                raw_payload=raw_payload
            )

            posts_batch.append(post)

            # Evita manter todos os objetos ORM em memória até ao final
            # quando são importados conjuntos de dados maiores.
            if len(posts_batch) >= batch_size:
                db.add_all(posts_batch)
                db.flush()
                posts_batch.clear()

        # Guarda os últimos registos que não completaram um lote inteiro.
        if posts_batch:
            db.add_all(posts_batch)
            db.flush()

        db.commit()
        db.refresh(dataset)

        return dataset

    except Exception:
        db.rollback()
        raise


def get_datasets(
    db: Session
) -> list[Dataset]:
    """
    Obtém todos os conjuntos de dados registados.

    Os resultados são ordenados do mais recente para o mais antigo.
    """

    return (
        db.query(Dataset)
        .order_by(Dataset.created_at.desc())
        .all()
    )


def get_dataset_by_id(
    db: Session,
    dataset_id: int
) -> Dataset | None:
    """
    Obtém um conjunto de dados através do respetivo identificador.
    """

    return (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id)
        .first()
    )


def get_posts_by_dataset(
    db: Session,
    dataset_id: int,
    limit: int = 100,
    offset: int = 0
) -> list[Post]:
    """
    Obtém uma página de registos pertencentes a um conjunto de dados.

    A paginação evita devolver todos os registos de conjuntos de dados
    potencialmente grandes num único pedido.
    """

    if limit < 1:
        raise ValueError("O limite deve ser superior a zero.")

    if offset < 0:
        raise ValueError("O offset não pode ser negativo.")

    return (
        db.query(Post)
        .filter(Post.dataset_id == dataset_id)
        .order_by(Post.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )