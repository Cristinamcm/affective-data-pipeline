def compute_text_metrics(original_text: str, cleaned_text: str) -> dict:
    if not isinstance(original_text, str):
        original_text = ""

    if not isinstance(cleaned_text, str):
        cleaned_text = ""

    return {
        "original_text_length": len(original_text),
        "cleaned_text_length": len(cleaned_text),
        "word_count": len(cleaned_text.split()),
        "has_url": "http://" in original_text
        or "https://" in original_text
        or "www." in original_text,
        "has_mention": "@" in original_text,
        "has_hashtag": "#" in original_text
    }