"""
Modelos ORM utilizados para representar os dados persistidos pelo sistema.

O modelo de dados suporta as principais fases do pipeline de recolha e
preparação de dados afetivos:

1. registo dos conjuntos de dados;
2. armazenamento dos registos originais;
3. registo das execuções de processamento;
4. registo das etapas executadas;
5. armazenamento dos dados processados;
6. armazenamento das métricas do pipeline;
7. armazenamento das características afetivas extraídas;
8. armazenamento das anotações emocionais.

Os nomes físicos das tabelas e colunas da base de dados são definidos em
português, mantendo-se os nomes das classes e atributos Python em inglês para
reduzir o impacto sobre os restantes módulos da aplicação.
"""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now():
    """
    Devolve a data e hora atual em UTC.

    É utilizada como valor por omissão nos campos temporais dos modelos.
    """
    return datetime.now(UTC)


# =============================================================================
# CONJUNTOS DE DADOS
# =============================================================================


class Dataset(Base):
    """
    Representa um conjunto de dados importado para o sistema.

    Um conjunto de dados pode resultar do carregamento de um ficheiro público,
    de uma API ou de outra fonte suportada pelo sistema.

    O registo mantém informação relativa à origem dos dados, ao ficheiro
    original e ao mapeamento das colunas relevantes.
    """

    __tablename__ = "conjuntos_dados"

    # Identificador interno do conjunto de dados.
    id = Column(
        "id",
        Integer,
        primary_key=True,
        index=True,
    )

    # Nome atribuído ao conjunto de dados.
    name = Column(
        "nome",
        String(255),
        nullable=False,
    )

    # Origem dos dados.
    #
    # Exemplos:
    # - Kaggle
    # - SemEval
    # - YouTube
    # - carregamento_manual
    source = Column(
        "origem",
        String(100),
        nullable=True,
    )

    # Nome original do ficheiro importado.
    original_filename = Column(
        "nome_ficheiro_original",
        String(255),
        nullable=False,
    )

    # Caminho do ficheiro bruto armazenado pelo sistema.
    raw_file_path = Column(
        "caminho_ficheiro_bruto",
        String(500),
        nullable=True,
    )

    # Hash do ficheiro original.
    #
    # Pode ser utilizado para verificar integridade e identificar
    # ficheiros importados repetidamente.
    file_hash = Column(
        "hash_ficheiro",
        String(128),
        nullable=True,
    )

    # Número total de registos existentes no conjunto de dados.
    rows_count = Column(
        "numero_registos",
        Integer,
        nullable=True,
    )

    # Nome da coluna original utilizada como identificador.
    id_column = Column(
        "coluna_identificador",
        String(255),
        nullable=True,
    )

    # Nome da coluna que contém o texto.
    text_column = Column(
        "coluna_texto",
        String(255),
        nullable=False,
    )

    # Nome da coluna que contém o rótulo original, quando aplicável.
    #
    # Por exemplo:
    # - sentiment
    # - label
    # - emotion
    label_column = Column(
        "coluna_rotulo",
        String(255),
        nullable=True,
    )

    # Codificação identificada ou selecionada para o ficheiro.
    encoding = Column(
        "codificacao",
        String(50),
        nullable=True,
    )

    # Delimitador utilizado no ficheiro.
    delimiter = Column(
        "delimitador",
        String(10),
        nullable=True,
    )

    # Idioma predominante do conjunto de dados, quando conhecido.
    language = Column(
        "idioma",
        String(20),
        nullable=True,
    )

    # Data e hora de registo do conjunto de dados.
    created_at = Column(
        "criado_em",
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Registos originais pertencentes ao conjunto de dados.
    posts = relationship(
        "Post",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )

    # Execuções de processamento realizadas sobre o conjunto de dados.
    processing_runs = relationship(
        "ProcessingRun",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )


# =============================================================================
# REGISTOS ORIGINAIS
# =============================================================================


class Post(Base):
    """
    Representa um registo original pertencente a um conjunto de dados.

    O termo "registo" é utilizado de forma genérica porque os dados podem
    corresponder a tweets, comentários, publicações, mensagens ou outras
    unidades provenientes de diferentes fontes.

    O conteúdo original é preservado antes de qualquer transformação.
    """

    __tablename__ = "registos"

    # Identificador interno do registo.
    id = Column(
        "id",
        Integer,
        primary_key=True,
        index=True,
    )

    # Conjunto de dados ao qual o registo pertence.
    dataset_id = Column(
        "conjunto_dados_id",
        Integer,
        ForeignKey("conjuntos_dados.id"),
        nullable=False,
        index=True,
    )

    # Identificador existente no ficheiro ou sistema de origem.
    external_id = Column(
        "id_externo",
        String(255),
        nullable=True,
    )

    # Texto original, preservado sem alterações.
    original_text = Column(
        "texto_original",
        Text,
        nullable=False,
    )

    # Rótulo existente no conjunto de dados original.
    #
    # É Text porque pode representar:
    # - um rótulo simples;
    # - vários rótulos serializados em JSON;
    # - categorias provenientes de diferentes datasets.
    original_label = Column(
        "rotulo_original",
        Text,
        nullable=True,
    )

    # Representação serializada da linha original completa.
    #
    # Permite preservar campos que não façam parte do modelo normalizado,
    # sendo particularmente útil perante conjuntos de dados heterogéneos.
    raw_payload = Column(
        "conteudo_bruto",
        Text,
        nullable=True,
    )

    # Data e hora de inserção.
    inserted_at = Column(
        "inserido_em",
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Conjunto de dados de origem.
    dataset = relationship(
        "Dataset",
        back_populates="posts",
    )

    # Resultados de processamento deste registo.
    processed_posts = relationship(
        "ProcessedPost",
        back_populates="post",
        cascade="all, delete-orphan",
    )


# =============================================================================
# EXECUÇÕES DE PROCESSAMENTO
# =============================================================================


class ProcessingRun(Base):
    """
    Representa uma execução do pipeline de processamento.

    Cada execução corresponde à aplicação de uma determinada configuração
    sobre um conjunto de dados.

    A configuração utilizada é preservada de forma a permitir rastreabilidade
    e reprodutibilidade das transformações realizadas.
    """

    __tablename__ = "execucoes_processamento"

    # Identificador interno da execução.
    id = Column(
        "id",
        Integer,
        primary_key=True,
        index=True,
    )

    # Conjunto de dados processado.
    dataset_id = Column(
        "conjunto_dados_id",
        Integer,
        ForeignKey("conjuntos_dados.id"),
        nullable=False,
        index=True,
    )

    # Nome atribuído à configuração.
    #
    # Pode continuar a assumir "custom" para uma configuração definida
    # pelo utilizador.
    configuration_name = Column(
        "nome_configuracao",
        String(100),
        nullable=False,
        default="custom",
    )

    # Configuração completa serializada em JSON.
    configuration_json = Column(
        "configuracao_json",
        Text,
        nullable=False,
    )

    # Versão do pipeline utilizada.
    #
    # Permite distinguir resultados produzidos por diferentes versões
    # do sistema.
    pipeline_version = Column(
        "versao_pipeline",
        String(50),
        nullable=True,
    )

    # Número total de registos considerados.
    total_posts = Column(
        "numero_total_registos",
        Integer,
        default=0,
        nullable=False,
    )

    # Número de registos processados com sucesso.
    processed_posts_count = Column(
        "numero_registos_processados",
        Integer,
        default=0,
        nullable=False,
    )

    # Número de registos que não puderam ser processados.
    failed_posts_count = Column(
        "numero_registos_com_erro",
        Integer,
        default=0,
        nullable=False,
    )

    # Número de registos identificados como duplicados.
    duplicate_posts = Column(
        "numero_registos_duplicados",
        Integer,
        default=0,
        nullable=False,
    )

    # Número de textos que ficaram vazios após o processamento.
    empty_after_processing = Column(
        "numero_textos_vazios",
        Integer,
        default=0,
        nullable=False,
    )

    # Estado atual da execução.
    #
    # Exemplos:
    # - started
    # - processing
    # - completed
    # - failed
    status = Column(
        "estado",
        String(50),
        default="started",
        nullable=False,
    )

    # Mensagem de erro geral, quando a execução falha.
    error_message = Column(
        "mensagem_erro",
        Text,
        nullable=True,
    )

    # Momento de início.
    started_at = Column(
        "iniciado_em",
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Momento de conclusão.
    finished_at = Column(
        "terminado_em",
        DateTime(timezone=True),
        nullable=True,
    )

    # Duração total da execução em milissegundos.
    duration_ms = Column(
        "duracao_ms",
        Integer,
        nullable=True,
    )

    # Conjunto de dados processado.
    dataset = relationship(
        "Dataset",
        back_populates="processing_runs",
    )

    # Etapas executadas.
    processing_steps = relationship(
        "ProcessingStep",
        back_populates="processing_run",
        cascade="all, delete-orphan",
        order_by="ProcessingStep.step_order",
    )

    # Registos processados produzidos.
    processed_records = relationship(
        "ProcessedPost",
        back_populates="processing_run",
        cascade="all, delete-orphan",
    )

    # Métricas produzidas durante a execução.
    metrics = relationship(
        "PipelineMetric",
        back_populates="processing_run",
        cascade="all, delete-orphan",
    )


# =============================================================================
# ETAPAS DE PROCESSAMENTO
# =============================================================================


class ProcessingStep(Base):
    """
    Representa uma operação concreta aplicada durante uma execução.

    Permite determinar:
    - quais as operações efetivamente executadas;
    - em que ordem foram executadas;
    - quantos registos foram afetados;
    - quanto tempo demorou cada operação.

    Exemplos:
    - normalize_unicode
    - lowercase
    - replace_urls
    - anonymize_mentions
    - remove_hashtags
    - tokenize
    - remove_stopwords
    """

    __tablename__ = "etapas_processamento"

    __table_args__ = (
        UniqueConstraint(
            "execucao_processamento_id",
            "ordem_etapa",
            name="uq_execucao_ordem_etapa",
        ),
    )

    # Identificador interno da etapa.
    id = Column(
        "id",
        Integer,
        primary_key=True,
        index=True,
    )

    # Execução à qual a etapa pertence.
    processing_run_id = Column(
        "execucao_processamento_id",
        Integer,
        ForeignKey("execucoes_processamento.id"),
        nullable=False,
        index=True,
    )

    # Nome da operação executada.
    step_name = Column(
        "nome_etapa",
        String(100),
        nullable=False,
    )

    # Posição da operação no pipeline.
    step_order = Column(
        "ordem_etapa",
        Integer,
        nullable=False,
    )

    # Configuração específica da etapa, quando necessária.
    #
    # Exemplo:
    #
    # {
    #     "replacement": "[URL]"
    # }
    configuration_json = Column(
        "configuracao_json",
        Text,
        nullable=True,
    )

    # Estado da execução desta etapa.
    status = Column(
        "estado",
        String(50),
        default="started",
        nullable=False,
    )

    # Número de registos recebidos pela etapa.
    rows_received = Column(
        "numero_registos_recebidos",
        Integer,
        default=0,
        nullable=False,
    )

    # Número de registos modificados pela operação.
    rows_changed = Column(
        "numero_registos_alterados",
        Integer,
        default=0,
        nullable=False,
    )

    # Número de registos nos quais ocorreu erro.
    rows_failed = Column(
        "numero_registos_com_erro",
        Integer,
        default=0,
        nullable=False,
    )

    # Duração da operação em milissegundos.
    duration_ms = Column(
        "duracao_ms",
        Integer,
        nullable=True,
    )

    # Momento de início da etapa.
    started_at = Column(
        "iniciado_em",
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Momento de conclusão da etapa.
    finished_at = Column(
        "terminado_em",
        DateTime(timezone=True),
        nullable=True,
    )

    # Execução à qual a etapa pertence.
    processing_run = relationship(
        "ProcessingRun",
        back_populates="processing_steps",
    )

    # Métricas associadas especificamente a esta etapa.
    metrics = relationship(
        "PipelineMetric",
        back_populates="processing_step",
    )


# =============================================================================
# REGISTOS PROCESSADOS
# =============================================================================


class ProcessedPost(Base):
    """
    Representa o resultado do processamento de um registo original.

    Esta tabela contém apenas informação diretamente relacionada com a
    preparação do texto.

    Os indicadores afetivos são armazenados separadamente em
    caracteristicas_afetivas e as classificações emocionais em
    anotacoes_emocionais.
    """

    __tablename__ = "registos_processados"

    __table_args__ = (
        UniqueConstraint(
            "registo_id",
            "execucao_processamento_id",
            name="uq_registo_execucao_processamento",
        ),
    )

    # Identificador interno.
    id = Column(
        "id",
        Integer,
        primary_key=True,
        index=True,
    )

    # Registo original processado.
    post_id = Column(
        "registo_id",
        Integer,
        ForeignKey("registos.id"),
        nullable=False,
        index=True,
    )

    # Execução que produziu este resultado.
    processing_run_id = Column(
        "execucao_processamento_id",
        Integer,
        ForeignKey("execucoes_processamento.id"),
        nullable=False,
        index=True,
    )

    # Cópia do texto original utilizado na execução.
    original_text = Column(
        "texto_original",
        Text,
        nullable=False,
    )

    # Texto obtido após a aplicação do pipeline.
    processed_text = Column(
        "texto_processado",
        Text,
        nullable=False,
    )

    # Tokens obtidos após tokenização.
    #
    # Deve ser armazenado como JSON serializado.
    tokens = Column(
        "tokens",
        Text,
        nullable=True,
    )

    # Número de caracteres no texto original.
    original_length = Column(
        "comprimento_original",
        Integer,
        default=0,
        nullable=False,
    )

    # Número de caracteres no texto processado.
    processed_length = Column(
        "comprimento_processado",
        Integer,
        default=0,
        nullable=False,
    )

    # Número de palavras no texto original.
    original_word_count = Column(
        "numero_palavras_original",
        Integer,
        default=0,
        nullable=False,
    )

    # Número de palavras no texto processado.
    processed_word_count = Column(
        "numero_palavras_processado",
        Integer,
        default=0,
        nullable=False,
    )

    # Número de tokens produzidos.
    token_count = Column(
        "numero_tokens",
        Integer,
        default=0,
        nullable=False,
    )

    # Indica se o registo foi identificado como duplicado.
    is_duplicate = Column(
        "esta_duplicado",
        Boolean,
        default=False,
        nullable=False,
    )

    # Indica se o texto ficou vazio após o processamento.
    is_empty_after_processing = Column(
        "esta_vazio",
        Boolean,
        default=False,
        nullable=False,
    )

    # Data e hora de produção do resultado.
    processed_at = Column(
        "processado_em",
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Registo original.
    post = relationship(
        "Post",
        back_populates="processed_posts",
    )

    # Execução responsável pelo resultado.
    processing_run = relationship(
        "ProcessingRun",
        back_populates="processed_records",
    )

    # Características afetivas extraídas.
    #
    # Nesta versão assume-se uma estrutura de características por registo
    # processado.
    affective_features = relationship(
        "AffectiveFeature",
        back_populates="processed_post",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # Anotações emocionais atribuídas ao registo.
    #
    # A relação é 1:N porque o mesmo texto pode possuir várias emoções.
    emotion_annotations = relationship(
        "EmotionAnnotation",
        back_populates="processed_post",
        cascade="all, delete-orphan",
    )


# =============================================================================
# MÉTRICAS DE PROCESSAMENTO
# =============================================================================


class PipelineMetric(Base):
    """
    Representa uma métrica calculada durante a execução do pipeline.

    Uma métrica pode estar associada:

    1. à execução completa;
    2. a uma etapa específica do processamento.

    O armazenamento do numerador e denominador permite apresentar proporções
    sem perder as contagens que deram origem ao valor.
    """

    __tablename__ = "metricas_processamento"

    # Identificador da métrica.
    id = Column(
        "id",
        Integer,
        primary_key=True,
        index=True,
    )

    # Execução à qual pertence.
    processing_run_id = Column(
        "execucao_processamento_id",
        Integer,
        ForeignKey("execucoes_processamento.id"),
        nullable=False,
        index=True,
    )

    # Etapa específica associada à métrica.
    #
    # Pode ficar nulo quando a métrica representa o pipeline completo.
    processing_step_id = Column(
        "etapa_processamento_id",
        Integer,
        ForeignKey("etapas_processamento.id"),
        nullable=True,
        index=True,
    )

    # Identificador lógico da métrica.
    #
    # Exemplos:
    # - proportion_urls_replaced
    # - proportion_mentions_anonymized
    # - empty_text_ratio
    # - mean_length_change
    # - throughput
    metric_name = Column(
        "nome_metrica",
        String(150),
        nullable=False,
    )

    # Valor final da métrica.
    metric_value = Column(
        "valor_metrica",
        Float,
        nullable=False,
    )

    # Numerador utilizado no cálculo da proporção.
    numerator = Column(
        "numerador",
        Integer,
        nullable=True,
    )

    # Denominador utilizado no cálculo da proporção.
    denominator = Column(
        "denominador",
        Integer,
        nullable=True,
    )

    # Unidade da métrica.
    #
    # Exemplos:
    # - proportion
    # - ms
    # - records_per_second
    # - characters
    unit = Column(
        "unidade",
        String(50),
        nullable=True,
    )

    # Descrição opcional.
    description = Column(
        "descricao",
        Text,
        nullable=True,
    )

    # Data de criação da métrica.
    created_at = Column(
        "criado_em",
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Execução associada.
    processing_run = relationship(
        "ProcessingRun",
        back_populates="metrics",
    )

    # Etapa associada, quando aplicável.
    processing_step = relationship(
        "ProcessingStep",
        back_populates="metrics",
    )


# =============================================================================
# CARACTERÍSTICAS AFETIVAS
# =============================================================================


class AffectiveFeature(Base):
    """
    Representa os indicadores afetivos identificados num registo processado.

    Esta tabela não representa necessariamente uma classificação emocional.
    Contém características observáveis que podem posteriormente apoiar análises
    afetivas.

    Exemplos:
    - emojis;
    - hashtags;
    - termos afetivos;
    - utilização de maiúsculas;
    - pontuação de intensidade;
    - caracteres repetidos.
    """

    __tablename__ = "caracteristicas_afetivas"

    # Identificador interno.
    id = Column(
        "id",
        Integer,
        primary_key=True,
        index=True,
    )

    # Registo processado ao qual pertencem as características.
    processed_post_id = Column(
        "registo_processado_id",
        Integer,
        ForeignKey("registos_processados.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Emojis encontrados.
    #
    # Armazenados como lista JSON serializada.
    emojis = Column(
        "emojis",
        Text,
        nullable=True,
    )

    # Número de emojis encontrados.
    emoji_count = Column(
        "numero_emojis",
        Integer,
        default=0,
        nullable=False,
    )

    # Hashtags encontradas.
    #
    # Armazenadas como lista JSON serializada.
    hashtags = Column(
        "hashtags",
        Text,
        nullable=True,
    )

    # Número de hashtags encontradas.
    hashtag_count = Column(
        "numero_hashtags",
        Integer,
        default=0,
        nullable=False,
    )

    # Termos com possível relevância afetiva.
    #
    # Armazenados como lista JSON serializada.
    affective_terms = Column(
        "termos_afetivos",
        Text,
        nullable=True,
    )

    # Número de termos afetivos encontrados.
    affective_term_count = Column(
        "numero_termos_afetivos",
        Integer,
        default=0,
        nullable=False,
    )

    # Proporção de caracteres ou palavras em maiúsculas.
    uppercase_ratio = Column(
        "proporcao_maiusculas",
        Float,
        default=0.0,
        nullable=False,
    )

    # Número de pontos de exclamação.
    exclamation_count = Column(
        "numero_exclamacoes",
        Integer,
        default=0,
        nullable=False,
    )

    # Número de pontos de interrogação.
    question_count = Column(
        "numero_interrogacoes",
        Integer,
        default=0,
        nullable=False,
    )

    # Número de ocorrências de caracteres repetidos identificadas.
    repeated_characters_count = Column(
        "numero_caracteres_repetidos",
        Integer,
        default=0,
        nullable=False,
    )

    # Índice agregado de intensidade afetiva.
    #
    # Permanece nulo enquanto esta funcionalidade não for implementada.
    intensity_score = Column(
        "indice_intensidade",
        Float,
        nullable=True,
    )

    # Data de criação.
    created_at = Column(
        "criado_em",
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Registo processado associado.
    processed_post = relationship(
        "ProcessedPost",
        back_populates="affective_features",
    )


# =============================================================================
# ANOTAÇÕES EMOCIONAIS
# =============================================================================


class EmotionAnnotation(Base):
    """
    Representa uma emoção associada a um registo processado.

    Um registo pode possuir várias anotações emocionais, permitindo suportar
    classificação multi-label.

    A anotação pode resultar de diferentes métodos, como:
    - regras;
    - léxicos;
    - modelos pré-treinados;
    - modelos de aprendizagem automática.
    """

    __tablename__ = "anotacoes_emocionais"

    # Identificador interno.
    id = Column(
        "id",
        Integer,
        primary_key=True,
        index=True,
    )

    # Registo processado ao qual a anotação pertence.
    processed_post_id = Column(
        "registo_processado_id",
        Integer,
        ForeignKey("registos_processados.id"),
        nullable=False,
        index=True,
    )

    # Categoria emocional.
    #
    # Exemplos:
    # - alegria
    # - tristeza
    # - raiva
    # - medo
    # - surpresa
    # - repulsa
    emotion = Column(
        "emocao",
        String(100),
        nullable=False,
    )

    # Pontuação produzida pelo método utilizado.
    #
    # Pode representar probabilidade, confiança ou outro score, consoante
    # o método aplicado.
    score = Column(
        "pontuacao",
        Float,
        nullable=True,
    )

    # Método utilizado para gerar a anotação.
    #
    # Exemplos:
    # - lexicon
    # - rules
    # - pretrained_model
    method = Column(
        "metodo",
        String(100),
        nullable=False,
    )

    # Nome do modelo ou recurso utilizado.
    model_name = Column(
        "nome_modelo",
        String(255),
        nullable=True,
    )

    # Versão do modelo ou recurso utilizado.
    model_version = Column(
        "versao_modelo",
        String(100),
        nullable=True,
    )

    # Data de criação da anotação.
    created_at = Column(
        "criado_em",
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Registo processado associado.
    processed_post = relationship(
        "ProcessedPost",
        back_populates="emotion_annotations",
    )