"""
Operações de limpeza, normalização e deteção de elementos sociais.

Este módulo contém funções utilizadas pelo pipeline para:

- normalizar caracteres Unicode;
- converter texto para minúsculas;
- normalizar espaços;
- substituir URLs;
- anonimizar menções;
- extrair e normalizar hashtags;
- reduzir caracteres repetidos;
- remover caracteres de controlo;
- remover pontuação selecionada;
- detetar URLs, menções e hashtags.

As funções são independentes da base de dados. Recebem valores textuais
e devolvem o respetivo resultado transformado ou métricas calculadas.
"""

import re
import unicodedata
from typing import TypedDict


class SocialMarkerMetrics(TypedDict):
    """
    Estrutura das métricas associadas aos elementos característicos
    dos conteúdos provenientes de redes sociais.
    """

    url_count: int
    mention_count: int
    hashtag_count: int

    has_url: bool
    has_mention: bool
    has_hashtag: bool


# =============================================================================
# EXPRESSÕES REGULARES
# =============================================================================

WHITESPACE_PATTERN = re.compile(
    r"\s+"
)

URL_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+)",
    flags=re.IGNORECASE
)

MENTION_PATTERN = re.compile(
    r"(?<!\w)@\w+"
)

HASHTAG_PATTERN = re.compile(
    r"(?<!\w)#(\w+)"
)

# Identifica sequências em que o mesmo carácter ocorre pelo menos
# três vezes consecutivas.
REPEATED_CHARACTER_PATTERN = re.compile(
    r"(.)\1{2,}"
)

# Caracteres de controlo pertencentes aos intervalos C0 e C1.
CONTROL_CHARACTER_PATTERN = re.compile(
    r"[\x00-\x1f\x7f-\x9f]"
)

# Remove pontuação e símbolos, preservando:
#
# - caracteres alfanuméricos;
# - espaços;
# - parênteses retos utilizados em [URL] e [USER].
SELECTED_PUNCTUATION_PATTERN = re.compile(
    r"[^\w\s\[\]]"
)


# =============================================================================
# NORMALIZAÇÃO
# =============================================================================

def normalize_unicode(
    text: str
) -> str:
    """
    Normaliza a representação Unicode através da forma NFKC.
    """

    if not isinstance(text, str):
        return ""

    return unicodedata.normalize(
        "NFKC",
        text
    )


def lowercase_text(
    text: str
) -> str:
    """
    Converte o texto para minúsculas.
    """

    if not isinstance(text, str):
        return ""

    return text.lower()


def normalize_spaces(
    text: str
) -> str:
    """
    Reduz sequências de espaços, tabulações e mudanças de linha
    para um único espaço.
    """

    if not isinstance(text, str):
        return ""

    return WHITESPACE_PATTERN.sub(
        " ",
        text
    ).strip()


# =============================================================================
# URLS
# =============================================================================

def replace_urls(
    text: str
) -> str:
    """
    Substitui URLs por um marcador normalizado ``[URL]``.
    """

    if not isinstance(text, str):
        return ""

    return URL_PATTERN.sub(
        " [URL] ",
        text
    )


def count_urls(
    text: str
) -> int:
    """
    Conta os URLs existentes num texto.
    """

    if not isinstance(text, str):
        return 0

    return len(
        URL_PATTERN.findall(text)
    )


# =============================================================================
# MENÇÕES
# =============================================================================

def anonymize_mentions(
    text: str
) -> str:
    """
    Substitui menções a utilizadores pelo marcador ``[USER]``.
    """

    if not isinstance(text, str):
        return ""

    return MENTION_PATTERN.sub(
        " [USER] ",
        text
    )


def count_mentions(
    text: str
) -> int:
    """
    Conta as menções existentes num texto.
    """

    if not isinstance(text, str):
        return 0

    return len(
        MENTION_PATTERN.findall(text)
    )


# =============================================================================
# HASHTAGS
# =============================================================================

def extract_hashtags(
    text: str
) -> list[str]:
    """
    Extrai as hashtags de um texto, sem incluir o carácter ``#``.
    """

    if not isinstance(text, str):
        return []

    return HASHTAG_PATTERN.findall(
        text
    )


def normalize_hashtags(
    text: str
) -> str:
    """
    Remove o carácter ``#`` preservando o conteúdo textual da hashtag.

    Exemplo:

        #feliz -> feliz
    """

    if not isinstance(text, str):
        return ""

    return HASHTAG_PATTERN.sub(
        r"\1",
        text
    )


def count_hashtags(
    text: str
) -> int:
    """
    Conta as hashtags existentes num texto.
    """

    if not isinstance(text, str):
        return 0

    return len(
        HASHTAG_PATTERN.findall(text)
    )


# =============================================================================
# CARACTERES REPETIDOS
# =============================================================================

def reduce_repeated_characters(
    text: str
) -> str:
    """
    Reduz sequências de três ou mais caracteres iguais para duas ocorrências.

    Exemplos:

        felizzzzz -> felizz
        adorei!!!!! -> adorei!!
    """

    if not isinstance(text, str):
        return ""

    return REPEATED_CHARACTER_PATTERN.sub(
        r"\1\1",
        text
    )


def count_repeated_character_sequences(
    text: str
) -> int:
    """
    Conta sequências de caracteres repetidos suscetíveis de normalização.

    Uma sequência corresponde a três ou mais ocorrências consecutivas
    do mesmo carácter.
    """

    if not isinstance(text, str):
        return 0

    return len(
        REPEATED_CHARACTER_PATTERN.findall(text)
    )


# =============================================================================
# CARACTERES DE CONTROLO
# =============================================================================

def remove_special_characters(
    text: str
) -> str:
    """
    Remove caracteres de controlo existentes no texto.

    Os caracteres são substituídos por espaços para evitar a união
    indevida de palavras.
    """

    if not isinstance(text, str):
        return ""

    return CONTROL_CHARACTER_PATTERN.sub(
        " ",
        text
    )


def count_control_characters(
    text: str
) -> int:
    """
    Conta os caracteres de controlo existentes num texto.
    """

    if not isinstance(text, str):
        return 0

    return len(
        CONTROL_CHARACTER_PATTERN.findall(text)
    )


# =============================================================================
# PONTUAÇÃO
# =============================================================================

def remove_selected_punctuation(
    text: str
) -> str:
    """
    Remove pontuação e símbolos selecionados.

    São preservados:

    - caracteres alfanuméricos;
    - espaços;
    - os parênteses retos dos marcadores [URL] e [USER].

    Emojis podem ser removidos por esta operação. Caso seja necessário
    preservar o respetivo significado, podem ser convertidos para texto
    antes desta etapa.
    """

    if not isinstance(text, str):
        return ""

    cleaned_text = (
        SELECTED_PUNCTUATION_PATTERN.sub(
            " ",
            text
        )
    )

    return normalize_spaces(
        cleaned_text
    )


def count_selected_punctuation(
    text: str
) -> int:
    """
    Conta os caracteres que seriam removidos pela operação
    remove_selected_punctuation.
    """

    if not isinstance(text, str):
        return 0

    return len(
        SELECTED_PUNCTUATION_PATTERN.findall(
            text
        )
    )


# =============================================================================
# DETEÇÃO DOS ELEMENTOS SOCIAIS
# =============================================================================

def detect_social_markers(
    text: str
) -> SocialMarkerMetrics:
    """
    Identifica URLs, menções e hashtags existentes no texto.

    A função deve ser utilizada sobre o texto original, antes de qualquer
    transformação, para que as métricas descrevam corretamente os dados
    recebidos.
    """

    url_count = count_urls(
        text
    )

    mention_count = count_mentions(
        text
    )

    hashtag_count = count_hashtags(
        text
    )

    return {
        "url_count": url_count,
        "mention_count": mention_count,
        "hashtag_count": hashtag_count,

        "has_url": url_count > 0,
        "has_mention": mention_count > 0,
        "has_hashtag": hashtag_count > 0
    }