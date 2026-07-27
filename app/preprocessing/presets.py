"""
Configuração das operações suportadas pelo pipeline de pré-processamento.

Este módulo define:

- o catálogo de operações disponíveis;
- os valores utilizados por omissão;
- configurações predefinidas;
- a normalização das configurações recebidas.

Apesar da existência de presets, o sistema permite que o utilizador selecione
individualmente cada operação, construindo uma configuração adequada às
características do dataset em análise.
"""


# Catálogo das operações reconhecidas pelo pipeline.
#
# A chave corresponde ao identificador interno utilizado pelo backend e o valor
# corresponde à designação apresentada ao utilizador no frontend.
SUPPORTED_OPERATIONS = {
    "normalize_unicode": "Normalização Unicode",
    "lowercase": "Conversão para minúsculas",
    "normalize_spaces": "Normalização de espaços",
    "replace_urls": "Substituição de URLs por [URL]",
    "anonymize_mentions": "Anonimização de menções por [USER]",
    "extract_hashtags": "Extração de hashtags",
    "normalize_hashtags": "Normalização de hashtags",
    "extract_emojis": "Extração de emojis",
    "convert_emojis_to_text": "Conversão de emojis para texto",
    "expand_abbreviations": "Expansão de abreviações",
    "reduce_repeated_characters": "Redução de caracteres repetidos",
    "remove_special_characters": "Remoção de caracteres especiais",
    "remove_selected_punctuation": "Remoção de pontuação selecionada",
    "tokenize": "Tokenização",
    "remove_stopwords": "Remoção de stopwords",
    "stemming": "Stemming",
    "lemmatization": "Lematização"
}

# Configuração base em que todas as operações estão desativadas.
#
# Esta estrutura é utilizada para garantir que qualquer configuração possui
# explicitamente um valor booleano para todas as operações suportadas.
DEFAULT_CONFIG = {
    operation: False
    for operation in SUPPORTED_OPERATIONS
}

# Configurações predefinidas que podem ser utilizadas como ponto de partida.
#
# O operador ** cria uma cópia dos valores de DEFAULT_CONFIG em cada preset,
# evitando que as configurações partilhem o mesmo dicionário interno.
PREPROCESSING_PRESETS = {
    "minimal": {
        **DEFAULT_CONFIG,

        # Operações de normalização e proteção de identificadores.
        "normalize_unicode": True,
        "lowercase": True,
        "normalize_spaces": True,
        "replace_urls": True,
        "anonymize_mentions": True
    },
    "intermediate": {
        **DEFAULT_CONFIG,

        # Operações incluídas no nível mínimo.
        "normalize_unicode": True,
        "lowercase": True,
        "normalize_spaces": True,
        "replace_urls": True,
        "anonymize_mentions": True,

        # Preservação e normalização de elementos potencialmente afetivos.
        "extract_hashtags": True,
        "normalize_hashtags": True,
        "extract_emojis": True,
        "convert_emojis_to_text": True,

        # Redução de ruído e preparação linguística.
        "expand_abbreviations": True,
        "reduce_repeated_characters": True,
        "tokenize": True
    },
    "aggressive": {
        **DEFAULT_CONFIG,

        # Normalização geral.
        "normalize_unicode": True,
        "lowercase": True,
        "normalize_spaces": True,
        "replace_urls": True,
        "anonymize_mentions": True,

        # Tratamento de hashtags e emojis.
        "extract_hashtags": True,
        "normalize_hashtags": True,
        "extract_emojis": True,
        "convert_emojis_to_text": True,

        # Redução de ruído.
        "expand_abbreviations": True,
        "reduce_repeated_characters": True,
        "remove_special_characters": True,
        "remove_selected_punctuation": True,

        # Transformações linguísticas.
        "tokenize": True,
        "remove_stopwords": True,
        "stemming": True
    }
}


def normalize_config(config: dict | None) -> dict:
    """
    Normaliza uma configuração de pré-processamento.

    A função cria uma nova configuração com todas as operações suportadas.
    As opções recebidas são convertidas para valores booleanos e as operações
    ausentes permanecem desativadas.

    Chaves desconhecidas são ignoradas, impedindo que operações não suportadas
    sejam enviadas para o pipeline.

    Args:
        config: Configuração parcial recebida da API ou da camada de serviço.

    Returns:
        dict[str, bool]: Configuração completa e normalizada.
    """    
    if config is None:
        config = {}

    # Cria uma cópia para evitar alterações diretas em DEFAULT_CONFIG.
    normalized = DEFAULT_CONFIG.copy()

    # Apenas as operações existentes no catálogo são consideradas.
    for operation in SUPPORTED_OPERATIONS:
        normalized[operation] = bool(config.get(operation, False))

    return normalized