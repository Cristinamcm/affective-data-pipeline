"""
Operações de transformação linguística aplicadas ao texto e aos tokens.

Este módulo disponibiliza funções para:

- expandir abreviações frequentes;
- tokenizar o texto;
- remover stopwords;
- aplicar stemming;
- aplicar lematização.

Os recursos linguísticos atualmente implementados estão orientados para
conteúdos em inglês. Esta limitação deve ser considerada quando são
processados conjuntos de dados noutros idiomas.
"""

import re


# =============================================================================
# MARCADORES PROTEGIDOS
# =============================================================================

PROTECTED_TOKENS = {
    "[URL]",
    "[USER]"
}


def _normalize_protected_token(
    token: str
) -> str:
    """
    Normaliza marcadores protegidos para a respetiva forma canónica.

    Exemplos:

        [url]  -> [URL]
        [user] -> [USER]
    """

    token_upper = token.upper()

    if token_upper in PROTECTED_TOKENS:
        return token_upper

    return token


def _is_protected_token(
    token: str
) -> bool:
    """
    Indica se um token corresponde a um marcador estrutural protegido.
    """

    if not isinstance(token, str):
        return False

    return (
        token.upper()
        in PROTECTED_TOKENS
    )


# =============================================================================
# ABREVIAÇÕES
# =============================================================================

BASIC_ABBREVIATIONS = {
    "can't": "cannot",
    "won't": "will not",
    "don't": "do not",
    "doesn't": "does not",
    "didn't": "did not",
    "i'm": "i am",
    "it's": "it is",
    "that's": "that is",
    "you're": "you are",

    "u": "you",
    "ur": "your",
    "idk": "i do not know",
    "lol": "laughing",
    "omg": "oh my god"
}


ABBREVIATION_PATTERN = re.compile(
    r"(?<!\w)("
    + "|".join(
        re.escape(abbreviation)
        for abbreviation in sorted(
            BASIC_ABBREVIATIONS,
            key=len,
            reverse=True
        )
    )
    + r")(?!\w)",
    flags=re.IGNORECASE
)


# =============================================================================
# TOKENIZAÇÃO
# =============================================================================

# Os marcadores [URL] e [USER] são reconhecidos antes dos restantes tokens.
#
# IGNORECASE garante que versões como [url] também são identificadas.
TOKEN_PATTERN = re.compile(
    r"\[(?:URL|USER)\]|\b\w+\b",
    flags=re.IGNORECASE
)


# =============================================================================
# STOPWORDS
# =============================================================================

STOPWORDS_EN = {
    "a", "an", "the", "and", "or", "but", "if", "while",

    "is", "are", "was", "were",
    "be", "been", "being",

    "to", "of", "in", "on", "for", "with",
    "as", "by", "at", "from",

    "this", "that", "these", "those",

    "i", "you", "he", "she", "it", "we", "they",

    "me", "him", "her", "us", "them",

    "my", "your", "his", "its", "our", "their"
}


# =============================================================================
# NLTK
# =============================================================================

try:
    from nltk.stem import (
        PorterStemmer,
        WordNetLemmatizer
    )

except ImportError:
    PorterStemmer = None
    WordNetLemmatizer = None


PORTER_STEMMER = (
    PorterStemmer()
    if PorterStemmer is not None
    else None
)


WORDNET_LEMMATIZER = (
    WordNetLemmatizer()
    if WordNetLemmatizer is not None
    else None
)


# =============================================================================
# EXPANSÃO DE ABREVIAÇÕES
# =============================================================================

def expand_abbreviations(
    text: str
) -> str:
    """
    Expande abreviações e contrações frequentes em inglês.
    """

    if not isinstance(text, str):
        return ""

    normalized_text = text.replace(
        "’",
        "'"
    )

    def replace_abbreviation(
        match: re.Match
    ) -> str:

        abbreviation = (
            match.group(0)
            .lower()
        )

        return BASIC_ABBREVIATIONS[
            abbreviation
        ]

    return ABBREVIATION_PATTERN.sub(
        replace_abbreviation,
        normalized_text
    )


# =============================================================================
# TOKENIZAÇÃO
# =============================================================================

def tokenize_text(
    text: str
) -> list[str]:
    """
    Divide um texto numa sequência de tokens.

    Os marcadores [URL] e [USER] são preservados e normalizados para a
    respetiva forma canónica.
    """

    if not isinstance(text, str):
        return []

    raw_tokens = TOKEN_PATTERN.findall(
        text
    )

    return [
        _normalize_protected_token(token)
        for token in raw_tokens
    ]


# =============================================================================
# STOPWORDS
# =============================================================================

def remove_stopwords(
    tokens: list[str]
) -> list[str]:
    """
    Remove stopwords inglesas.

    Os marcadores estruturais são sempre preservados.

    A palavra negativa ``not`` não integra a lista de stopwords, uma vez que
    a sua remoção pode alterar significativamente o significado afetivo.
    """

    if not isinstance(tokens, list):
        return []

    return [
        _normalize_protected_token(token)
        for token in tokens
        if (
            _is_protected_token(token)
            or token.lower()
            not in STOPWORDS_EN
        )
    ]


# =============================================================================
# STEMMING
# =============================================================================

def stem_tokens(
    tokens: list[str]
) -> list[str]:
    """
    Aplica Porter Stemmer aos tokens.

    Os marcadores [URL] e [USER] são preservados.
    """

    if not isinstance(tokens, list):
        return []

    if PORTER_STEMMER is None:
        raise RuntimeError(
            "Não foi possível aplicar stemming porque "
            "a biblioteca NLTK não está instalada."
        )

    stemmed_tokens: list[str] = []

    for token in tokens:

        if _is_protected_token(token):

            stemmed_tokens.append(
                _normalize_protected_token(token)
            )

        else:

            stemmed_tokens.append(
                PORTER_STEMMER.stem(
                    token
                )
            )

    return stemmed_tokens


# =============================================================================
# LEMATIZAÇÃO
# =============================================================================

def lemmatize_tokens(
    tokens: list[str]
) -> list[str]:
    """
    Aplica lematização através do WordNetLemmatizer.

    Os marcadores [URL] e [USER] são preservados.
    """

    if not isinstance(tokens, list):
        return []

    if WORDNET_LEMMATIZER is None:
        raise RuntimeError(
            "Não foi possível aplicar lematização porque "
            "a biblioteca NLTK não está instalada."
        )

    lemmatized_tokens: list[str] = []

    try:

        for token in tokens:

            if _is_protected_token(token):

                lemmatized_tokens.append(
                    _normalize_protected_token(
                        token
                    )
                )

            else:

                lemmatized_tokens.append(
                    WORDNET_LEMMATIZER.lemmatize(
                        token
                    )
                )

        return lemmatized_tokens

    except LookupError as error:

        raise RuntimeError(
            "Os recursos WordNet necessários para a "
            "lematização não estão instalados."
        ) from error