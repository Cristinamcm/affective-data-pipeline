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


DEFAULT_CONFIG = {
    operation: False
    for operation in SUPPORTED_OPERATIONS
}


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
        "normalize_unicode": True,
        "lowercase": True,
        "normalize_spaces": True,
        "replace_urls": True,
        "anonymize_mentions": True,
        "extract_hashtags": True,
        "normalize_hashtags": True,
        "extract_emojis": True,
        "convert_emojis_to_text": True,
        "expand_abbreviations": True,
        "reduce_repeated_characters": True,
        "tokenize": True
    },
    "aggressive": {
        **DEFAULT_CONFIG,
        "normalize_unicode": True,
        "lowercase": True,
        "normalize_spaces": True,
        "replace_urls": True,
        "anonymize_mentions": True,
        "extract_hashtags": True,
        "normalize_hashtags": True,
        "extract_emojis": True,
        "convert_emojis_to_text": True,
        "expand_abbreviations": True,
        "reduce_repeated_characters": True,
        "remove_special_characters": True,
        "remove_selected_punctuation": True,
        "tokenize": True,
        "remove_stopwords": True,
        "stemming": True
    }
}


def normalize_config(config: dict | None) -> dict:
    if config is None:
        config = {}

    normalized = DEFAULT_CONFIG.copy()

    for operation in SUPPORTED_OPERATIONS:
        normalized[operation] = bool(config.get(operation, False))

    return normalized