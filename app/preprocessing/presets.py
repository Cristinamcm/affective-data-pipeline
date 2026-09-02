"""
Configuração das operações suportadas pelo pipeline de pré-processamento.

Este módulo define:

- o catálogo de operações disponíveis;
- a ordem de execução das operações;
- os valores utilizados por omissão;
- configurações predefinidas opcionais;
- a normalização e validação das configurações recebidas.

O sistema utiliza um pipeline modular e configurável. As configurações
predefinidas constituem apenas pontos de partida opcionais, podendo o
utilizador selecionar individualmente as operações adequadas às
características do conjunto de dados em análise.
"""


# =============================================================================
# OPERAÇÕES SUPORTADAS
# =============================================================================

SUPPORTED_OPERATIONS = {
    "extract_emojis": "Extração de emojis",
    "extract_hashtags": "Extração de hashtags",

    "normalize_unicode": "Normalização Unicode",
    "lowercase": "Conversão para minúsculas",
    "replace_urls": "Substituição de URLs por [URL]",
    "anonymize_mentions": "Anonimização de menções por [USER]",
    "normalize_hashtags": "Normalização de hashtags",
    "convert_emojis_to_text": "Conversão de emojis para texto",

    "expand_abbreviations": "Expansão de abreviações",
    "reduce_repeated_characters": "Redução de caracteres repetidos",
    "remove_special_characters": "Remoção de caracteres de controlo",
    "remove_selected_punctuation": "Remoção de pontuação selecionada",
    "normalize_spaces": "Normalização de espaços",

    "tokenize": "Tokenização",
    "remove_stopwords": "Remoção de stopwords",
    "stemming": "Stemming",
    "lemmatization": "Lematização"
}


# =============================================================================
# ORDEM DO PIPELINE
# =============================================================================

# A ordem é declarada explicitamente para garantir que:
#
# - o pipeline executa sempre as operações pela mesma ordem;
# - a tabela etapas_processamento apresenta a ordem real de execução;
# - alterações futuras no dicionário SUPPORTED_OPERATIONS não modificam
#   inadvertidamente o comportamento do pipeline.
PIPELINE_OPERATION_ORDER = tuple(
    SUPPORTED_OPERATIONS.keys()
)


# =============================================================================
# CONFIGURAÇÃO POR OMISSÃO
# =============================================================================

DEFAULT_CONFIG = {
    operation: False
    for operation in PIPELINE_OPERATION_ORDER
}


# =============================================================================
# CONFIGURAÇÕES PREDEFINIDAS
# =============================================================================

# Os presets são apenas configurações opcionais.
#
# Não constituem níveis obrigatórios de processamento. O utilizador pode
# construir livremente uma configuração através da seleção individual das
# operações disponíveis.
PREPROCESSING_PRESETS = {
    "minimal": {
        **DEFAULT_CONFIG,

        "normalize_unicode": True,
        "lowercase": True,
        "normalize_spaces": True,
        "replace_urls": True,
        "anonymize_mentions": True
    },

    "intermediate": {
        **DEFAULT_CONFIG,

        "extract_hashtags": True,
        "extract_emojis": True,

        "normalize_unicode": True,
        "lowercase": True,
        "replace_urls": True,
        "anonymize_mentions": True,
        "normalize_hashtags": True,
        "convert_emojis_to_text": True,

        "expand_abbreviations": True,
        "reduce_repeated_characters": True,
        "normalize_spaces": True,

        "tokenize": True
    },

    "aggressive": {
        **DEFAULT_CONFIG,

        "extract_hashtags": True,
        "extract_emojis": True,

        "normalize_unicode": True,
        "lowercase": True,
        "replace_urls": True,
        "anonymize_mentions": True,
        "normalize_hashtags": True,
        "convert_emojis_to_text": True,

        "expand_abbreviations": True,
        "reduce_repeated_characters": True,
        "remove_special_characters": True,
        "remove_selected_punctuation": True,
        "normalize_spaces": True,

        "tokenize": True,
        "remove_stopwords": True,
        "stemming": True
    }
}


# =============================================================================
# NORMALIZAÇÃO DA CONFIGURAÇÃO
# =============================================================================

def normalize_config(
    config: dict | None
) -> dict[str, bool]:
    """
    Normaliza e valida uma configuração de pré-processamento.

    Todas as operações suportadas ficam explicitamente representadas através
    de valores booleanos.

    Operações desconhecidas são ignoradas.

    Algumas dependências técnicas são resolvidas automaticamente. Por exemplo,
    remoção de stopwords, stemming e lematização necessitam de tokenização.

    Args:
        config:
            Configuração parcial recebida da API.

    Returns:
        dict[str, bool]:
            Configuração completa utilizada efetivamente pelo pipeline.

    Raises:
        ValueError:
            Quando são selecionadas simultaneamente operações incompatíveis.
    """

    if config is None:
        config = {}

    normalized = DEFAULT_CONFIG.copy()

    for operation in PIPELINE_OPERATION_ORDER:
        normalized[operation] = bool(
            config.get(
                operation,
                False
            )
        )

    # ---------------------------------------------------------------------
    # Dependências
    # ---------------------------------------------------------------------

    requires_tokenization = (
        normalized["remove_stopwords"]
        or normalized["stemming"]
        or normalized["lemmatization"]
    )

    if requires_tokenization:
        normalized["tokenize"] = True

    # ---------------------------------------------------------------------
    # Incompatibilidades
    # ---------------------------------------------------------------------

    # Stemming e lematização representam estratégias linguísticas
    # alternativas. Aplicar lematização sobre palavras previamente reduzidas
    # por stemming produz resultados difíceis de interpretar.
    if (
        normalized["stemming"]
        and normalized["lemmatization"]
    ):
        raise ValueError(
            "Stemming e lematização não podem ser aplicados "
            "simultaneamente. Selecione apenas uma das operações."
        )

    return normalized