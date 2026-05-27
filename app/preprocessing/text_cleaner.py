import re


def remove_urls(text: str) -> str:
    return re.sub(r"http\S+|www\S+", "", text)


def remove_mentions(text: str) -> str:
    return re.sub(r"@\w+", "", text)


def normalize_hashtags(text: str) -> str:
    return re.sub(r"#", "", text)


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""

    text = text.lower()
    text = remove_urls(text)
    text = remove_mentions(text)
    text = normalize_hashtags(text)
    text = normalize_spaces(text)

    return text