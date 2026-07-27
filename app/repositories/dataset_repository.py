"""
Operações de persistência e consulta relacionadas com datasets e publicações.

Este módulo centraliza o acesso à base de dados para:

- criar datasets;
- armazenar as publicações originais importadas;
- listar os datasets disponíveis;
- consultar um dataset específico;
- obter páginas de publicações associadas a um dataset.

As operações relacionadas com execuções e resultados do pré-processamento
permanecem no módulo preprocessing_repository.py.
"""

import pandas as pd
from sqlalchemy.orm import Session

from app.models.models import Dataset, Post


def create_dataset_with_posts(
    db: Session,
    name: str,
    source: str,
    original_filename: str,
    id_column: str | None,
    text_column: str,
    df: pd.DataFrame
) -> Dataset:
    """
    Cria um dataset e armazena as respetivas publicações originais.

    Cada linha do DataFrame recebido é transformada num registo da tabela
    'posts'. O texto original é preservado para permitir que o mesmo dataset
    seja posteriormente processado através de diferentes configurações.

    Args:
        db: Sessão SQLAlchemy utilizada para comunicar com a base de dados.
        name: Nome atribuído ao dataset na aplicação.
        source: Origem do dataset, como Kaggle, YouTube ou carregamento manual.
        original_filename: Nome original do ficheiro carregado.
        id_column: Nome da coluna que contém o identificador das publicações.
            Quando não é indicada, é gerado um identificador sequencial.
        text_column: Nome da coluna que contém o texto das publicações.
        df: DataFrame com os dados importados.

    Returns:
        Dataset: Dataset criado e persistido na base de dados.
    """

    # Cria o registo que contém os metadados gerais do dataset.
    dataset = Dataset(
        name=name,
        source=source,
        original_filename=original_filename,
        rows_count=len(df),
        id_column=id_column,
        text_column=text_column
    )


    try:
        # Adiciona o dataset à sessão.
        db.add(dataset)

        # Envia a inserção para a base de dados sem confirmar ainda a transação.
        # Isto permite obter o identificador gerado para o dataset.
        db.flush()

        # Percorre as linhas do DataFrame e cria uma publicação por linha.
        for index, row in df.iterrows():

            # Utiliza a coluna identificadora selecionada pelo utilizador,
            # quando esta existe e contém um valor válido.
            if id_column and id_column in df.columns:
                external_id = row[id_column]

                # Quando o identificador está vazio, é utilizado um valor
                # sequencial baseado na posição da linha.
                if pd.isna(external_id):
                    external_id = index + 1
            else:
                external_id = index + 1

            # Obtém o conteúdo da coluna textual selecionada.
            original_text = row[text_column]

            # Converte valores nulos para texto vazio, uma vez que a coluna
            # original_text não aceita valores nulos na base de dados.
            if pd.isna(original_text):
                original_text = ""

            post = Post(
                dataset_id=dataset.id,
                external_id=str(external_id),
                original_text=str(original_text)
            )

            db.add(post)

        # Confirma numa única transação a criação do dataset e dos posts.
        db.commit()
        db.refresh(dataset)

        return dataset

    except Exception:
        # Reverte todas as alterações pendentes caso ocorra um erro durante
        # a importação do dataset.
        db.rollback()
        raise


def get_datasets(db: Session):
    """
    Obtém todos os datasets registados no sistema.

    Os datasets são devolvidos do mais recente para o mais antigo.

    Args:
        db: Sessão SQLAlchemy utilizada na consulta.

    Returns:
        list[Dataset]: Lista de datasets existentes.
    """

    return (
        db.query(Dataset)
        .order_by(Dataset.created_at.desc())
        .all()
    )


def get_dataset_by_id(db: Session, dataset_id: int):
    """
    Obtém um dataset através do respetivo identificador interno.

    Args:
        db: Sessão SQLAlchemy utilizada na consulta.
        dataset_id: Identificador do dataset.

    Returns:
        Dataset | None: Dataset encontrado ou ``None`` quando não existe.
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
    Obtém uma página de publicações pertencentes a um dataset.

    A paginação evita devolver todas as publicações de datasets potencialmente
    grandes num único pedido.

    Esta função constitui a implementação central da consulta. As operações
    específicas do módulo de pré-processamento reutilizam esta função, evitando
    a duplicação da consulta SQLAlchemy.

    Args:
        db: Sessão SQLAlchemy utilizada na consulta.
        dataset_id: Identificador do dataset.
        limit: Número máximo de publicações a devolver.
        offset: Número de publicações a ignorar antes de iniciar o resultado.

    Returns:
        list[Post]: Publicações encontradas na página solicitada.

    Raises:
        ValueError: Quando limit é inferior a 1 ou offset é negativo.
    """

    if limit < 1:
        raise ValueError("The limit must be greater than zero")

    if offset < 0:
        raise ValueError("The offset cannot be negative")

    return (
        db.query(Post)
        .filter(Post.dataset_id == dataset_id)
        .order_by(Post.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )