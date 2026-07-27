"""
Modelos ORM utilizados para representar os dados persistidos pelo sistema.

Este módulo define a estrutura relacional da base de dados para suportar as
principais fases do pipeline:

1. registo dos conjuntos de dados;
2. armazenamento das publicações originais;
3. registo das execuções de pré-processamento;
4. armazenamento dos resultados e métricas de cada publicação processada.

Os modelos são implementados através do SQLAlchemy ORM.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text
)
from sqlalchemy.orm import relationship

from app.database import Base


class Dataset(Base):
    """
    Representa um conjunto de dados importado para o sistema.

    Um dataset corresponde a um ficheiro ou fonte de dados contendo publicações
    provenientes de redes sociais ou de datasets públicos.

    O registo mantém informação sobre a origem do dataset, o ficheiro original
    e o mapeamento das colunas selecionadas pelo utilizador.
    """

    __tablename__ = "datasets"

    # Identificador interno do conjunto de dados.
    id = Column(Integer, primary_key=True, index=True)

    # Nome atribuído ao conjunto de dados dentro da aplicação.
    name = Column(String(255), nullable=False)

    # Origem dos dados, como Kaggle, YouTube, Twitter/X ou carregamento manual.
    source = Column(String(100), nullable=True)

    # Nome original do ficheiro submetido pelo utilizador.
    original_filename = Column(String(255), nullable=False)

    # Número total de registos existentes no conjunto de dados.
    rows_count = Column(Integer, nullable=True)

    # Nome da coluna do ficheiro original utilizada como identificador externo.
    #
    # Este campo é opcional porque alguns datasets podem não disponibilizar
    # uma coluna identificadora.
    id_column = Column(String(255), nullable=True)

    # Nome da coluna do ficheiro original que contém o texto das publicações.
    text_column = Column(String(255), nullable=False)

    # Data e hora em que o conjunto de dados foi registado no sistema.
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relação entre o dataset e as publicações originais nele armazenadas.
    #
    # Um dataset pode conter várias publicações.
    # A eliminação do dataset remove também as publicações associadas.
    posts = relationship(
        "Post",
        back_populates="dataset",
        cascade="all, delete-orphan"
    )

    # Relação entre o dataset e as diferentes execuções de pré-processamento.
    #
    # O mesmo dataset pode ser processado várias vezes, utilizando configurações
    # distintas definidas pelo utilizador.
    processing_runs = relationship(
        "ProcessingRun",
        back_populates="dataset",
        cascade="all, delete-orphan"
    )


class Post(Base):
    """
    Representa uma publicação original pertencente a um dataset.

    Esta tabela preserva o texto original antes da aplicação de qualquer
    operação de limpeza, normalização ou enriquecimento. A preservação dos dados
    originais permite repetir o processamento com diferentes configurações e
    comparar os respetivos resultados.
    """

    __tablename__ = "posts"

    # Identificador interno da publicação.
    id = Column(Integer, primary_key=True, index=True)

    # Identificador do dataset ao qual a publicação pertence.
    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id"),
        nullable=False,
        index=True
    )

    # Identificador da publicação na fonte ou no ficheiro original.
    #
    # Pode corresponder, por exemplo, ao identificador de um comentário numa
    # rede social ou ao valor de uma coluna identificadora do dataset.
    external_id = Column(String(255), nullable=True)

    # Texto original da publicação, preservado sem alterações.
    original_text = Column(Text, nullable=False)

    # Data e hora em que a publicação foi inserida na base de dados.
    inserted_at = Column(DateTime, default=datetime.utcnow)

    # Referência ao dataset ao qual a publicação pertence.
    dataset = relationship(
        "Dataset",
        back_populates="posts"
    )

    # Resultados de pré-processamento produzidos para esta publicação.
    #
    # Uma publicação pode possuir vários resultados porque pode ser processada
    # em diferentes execuções e com configurações distintas.
    processed_posts = relationship(
        "ProcessedPost",
        back_populates="post",
        cascade="all, delete-orphan"
    )


class ProcessingRun(Base):
    """
    Representa uma execução do pipeline de pré-processamento.

    Cada execução está associada a um dataset e regista a configuração escolhida
    pelo utilizador, o estado do processamento, eventuais erros e métricas
    agregadas sobre os resultados obtidos.

    Este modelo permite manter rastreabilidade e reprodutibilidade sobre as
    transformações aplicadas aos dados.
    """

    __tablename__ = "processing_runs"

    # Identificador interno da execução.
    id = Column(Integer, primary_key=True, index=True)

    # Dataset sobre o qual foi executado o pré-processamento.
    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id"),
        nullable=False,
        index=True
    )

    # Nome atribuído à configuração utilizada.
    #
    # O valor "custom" representa uma configuração personalizada pelo utilizador.
    configuration_name = Column(
        String(100),
        nullable=False,
        default="custom"
    )

    # Representação serializada da configuração aplicada.
    #
    # Este campo pode guardar, por exemplo, uma estrutura JSON com as operações
    # selecionadas: normalização de URLs, anonimização de menções, tratamento de
    # hashtags, tokenização ou remoção de pontuação.
    configuration_json = Column(Text, nullable=False)

    # Número total de publicações consideradas nesta execução.
    total_posts = Column(Integer, default=0)

    # Número de publicações processadas com sucesso.
    processed_posts_count = Column(Integer, default=0)

    # Número de publicações identificadas como duplicadas.
    duplicate_posts = Column(Integer, default=0)

    # Número de publicações cujo texto ficou vazio após o pré-processamento.
    empty_after_processing = Column(Integer, default=0)

    # Estado atual da execução.
    #
    # Poderá assumir valores como:
    # - started;
    # - processing;
    # - completed;
    # - failed.
    status = Column(String(50), default="started")

    # Mensagem com informação sobre o erro ocorrido, quando aplicável.
    error_message = Column(Text, nullable=True)

    # Data e hora de início da execução.
    started_at = Column(DateTime, default=datetime.utcnow)

    # Data e hora de conclusão da execução.
    #
    # Permanece nulo enquanto o processamento não estiver concluído.
    finished_at = Column(DateTime, nullable=True)

    # Dataset processado nesta execução.
    dataset = relationship(
        "Dataset",
        back_populates="processing_runs"
    )

    # Resultados individuais produzidos durante a execução.
    processed_records = relationship(
        "ProcessedPost",
        back_populates="processing_run",
        cascade="all, delete-orphan"
    )


class ProcessedPost(Base):
    """
    Representa o resultado do pré-processamento de uma publicação.

    Este modelo mantém o texto original, o texto transformado, os elementos
    afetivos e linguísticos extraídos e as métricas calculadas durante o
    processamento.

    Cada registo está associado simultaneamente à publicação original e à
    execução de pré-processamento que produziu o resultado.
    """

    __tablename__ = "processed_posts"

    # Identificador interno do resultado processado.
    id = Column(Integer, primary_key=True, index=True)

    # Publicação original que foi processada.
    post_id = Column(
        Integer,
        ForeignKey("posts.id"),
        nullable=False,
        index=True
    )

    # Execução de pré-processamento responsável por este resultado.
    processing_run_id = Column(
        Integer,
        ForeignKey("processing_runs.id"),
        nullable=False,
        index=True
    )

    # Cópia do texto original no momento do processamento.
    #
    # Apesar de o texto também existir na tabela posts, esta cópia facilita a
    # consulta e preserva o contexto exato utilizado durante a execução.
    original_text = Column(Text, nullable=False)

    # Texto resultante após a aplicação das operações selecionadas.
    processed_text = Column(Text, nullable=False)

    # Representação serializada dos tokens extraídos do texto.
    tokens = Column(Text, nullable=True)

    # Representação serializada dos emojis identificados na publicação.
    emojis = Column(Text, nullable=True)

    # Representação serializada das hashtags identificadas na publicação.
    hashtags = Column(Text, nullable=True)

    # Representação serializada das etapas de pré-processamento aplicadas.
    applied_steps = Column(Text, nullable=True)

    # Número de caracteres existentes no texto original.
    original_length = Column(Integer, default=0)

    # Número de caracteres existentes depois do pré-processamento.
    processed_length = Column(Integer, default=0)

    # Número de palavras identificadas no texto processado.
    word_count = Column(Integer, default=0)

    # Número de tokens produzidos pelo processo de tokenização.
    token_count = Column(Integer, default=0)

    # Indica se o texto original continha pelo menos um URL.
    has_url = Column(Boolean, default=False)

    # Indica se o texto original continha pelo menos uma menção a um utilizador.
    has_mention = Column(Boolean, default=False)

    # Indica se o texto original continha pelo menos uma hashtag.
    has_hashtag = Column(Boolean, default=False)

    # Número de URLs encontrados na publicação.
    url_count = Column(Integer, default=0)

    # Número de menções a utilizadores encontradas na publicação.
    mention_count = Column(Integer, default=0)

    # Número de hashtags encontradas na publicação.
    hashtag_count = Column(Integer, default=0)

    # Número de emojis encontrados na publicação.
    emoji_count = Column(Integer, default=0)

    # Indica se a publicação foi identificada como duplicada.
    is_duplicate = Column(Boolean, default=False)

    # Indica se o texto ficou vazio depois da aplicação do pré-processamento.
    is_empty_after_processing = Column(Boolean, default=False)

    # Quantidades de transformações efetivamente realizadas.
    urls_removed_count = Column(Integer, default=0)
    urls_replaced_count = Column(Integer, default=0)
    mentions_anonymized_count = Column(Integer, default=0)
    hashtags_removed_count = Column(Integer, default=0)
    emojis_preserved_count = Column(Integer, default=0)

    # Data e hora em que o resultado foi produzido.
    processed_at = Column(DateTime, default=datetime.utcnow)

    # Publicação original associada ao resultado.
    post = relationship(
        "Post",
        back_populates="processed_posts"
    )

    # Execução de pré-processamento que produziu o resultado.
    processing_run = relationship(
        "ProcessingRun",
        back_populates="processed_records"
    )