import re
import unicodedata


def normalize_unicode(text: str) -> str:
    if not isinstance(text, str):
        return ""

    return unicodedata.normalize("NFKC", text)


def lowercase_text(text: str) -> str:
    return text.lower()


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def replace_urls(text: str) -> str:
    return re.sub(
        r"(https?://\S+|www\.\S+)",
        " [URL] ",
        text
    )


def anonymize_mentions(text: str) -> str:
    return re.sub(
        r"@\w+",
        " [USER] ",
        text
    )


def normalize_hashtags(text: str) -> str:
    """
    Remove o símbolo #, mas preserva o conteúdo textual da hashtag.
    Exemplo: #happy -> happy
    """
    return re.sub(r"#(\w+)", r"\1", text)


def reduce_repeated_characters(text: str) -> str:
    """
    Reduz repetições longas de caracteres.
    Exemplo: missssssssss -> miss
    """
    return re.sub(r"(.)\1{2,}", r"\1\1", text)


def remove_selected_punctuation(text: str) -> str:
    """
    Remove pontuação selecionada, mas preserva tokens anonimizados como URL e USER.
    """
    text = re.sub(r"[^\w\s\[\]]", " ", text)
    return normalize_spaces(text)


def detect_social_markers(text: str) -> dict:
    if not isinstance(text, str):
        text = ""

    return {
        "has_url": bool(re.search(r"https?://\S+|www\.\S+", text)),
        "has_mention": bool(re.search(r"@\w+", text)),
        "has_hashtag": "#" in text
    }