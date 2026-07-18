import re
import unicodedata


def normalize_unicode(text: str) -> str:
    if not isinstance(text, str):
        return ""

    return unicodedata.normalize("NFKC", text)


def lowercase_text(text: str) -> str:
    if not isinstance(text, str):
        return ""

    return text.lower()


def normalize_spaces(text: str) -> str:
    if not isinstance(text, str):
        return ""

    return re.sub(r"\s+", " ", text).strip()


def replace_urls(text: str) -> str:
    if not isinstance(text, str):
        return ""

    return re.sub(
        r"(https?://\S+|www\.\S+)",
        " [URL] ",
        text
    )


def anonymize_mentions(text: str) -> str:
    if not isinstance(text, str):
        return ""

    return re.sub(
        r"@\w+",
        " [USER] ",
        text
    )


def extract_hashtags(text: str) -> list[str]:
    if not isinstance(text, str):
        return []

    return re.findall(r"#(\w+)", text)


def normalize_hashtags(text: str) -> str:
    if not isinstance(text, str):
        return ""

    return re.sub(r"#(\w+)", r"\1", text)


def reduce_repeated_characters(text: str) -> str:
    if not isinstance(text, str):
        return ""

    return re.sub(r"(.)\1{2,}", r"\1\1", text)


def remove_special_characters(text: str) -> str:
    if not isinstance(text, str):
        return ""

    return re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", text)


def remove_selected_punctuation(text: str) -> str:
    if not isinstance(text, str):
        return ""

    text = re.sub(r"[^\w\s\[\]]", " ", text)

    return normalize_spaces(text)


def count_urls(text: str) -> int:
    if not isinstance(text, str):
        return 0

    return len(re.findall(r"(https?://\S+|www\.\S+)", text))


def count_mentions(text: str) -> int:
    if not isinstance(text, str):
        return 0

    return len(re.findall(r"@\w+", text))


def count_hashtags(text: str) -> int:
    if not isinstance(text, str):
        return 0

    return len(re.findall(r"#\w+", text))


def detect_social_markers(text: str) -> dict:
    return {
        "url_count": count_urls(text),
        "mention_count": count_mentions(text),
        "hashtag_count": count_hashtags(text),
        "has_url": count_urls(text) > 0,
        "has_mention": count_mentions(text) > 0,
        "has_hashtag": count_hashtags(text) > 0
    }