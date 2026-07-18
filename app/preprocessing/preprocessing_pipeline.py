from app.preprocessing.emoji_processing import (
    convert_emojis_to_text,
    extract_emojis
)
from app.preprocessing.presets import normalize_config
from app.preprocessing.text_cleaning import (
    anonymize_mentions,
    detect_social_markers,
    extract_hashtags,
    lowercase_text,
    normalize_hashtags,
    normalize_spaces,
    normalize_unicode,
    reduce_repeated_characters,
    remove_selected_punctuation,
    remove_special_characters,
    replace_urls
)
from app.preprocessing.text_transformation import (
    expand_abbreviations,
    lemmatize_tokens,
    remove_stopwords,
    stem_tokens,
    tokenize_text
)


def preprocess_text(text: str, config: dict | None = None) -> dict:
    config = normalize_config(config)

    if not isinstance(text, str):
        text = ""

    original_text = text

    original_social_markers = detect_social_markers(original_text)

    emojis = []
    hashtags = []
    tokens = []
    applied_steps = []

    if config.get("extract_emojis"):
        emojis = extract_emojis(original_text)
        applied_steps.append("extract_emojis")

    if config.get("extract_hashtags"):
        hashtags = extract_hashtags(original_text)
        applied_steps.append("extract_hashtags")

    processed_text = original_text

    if config.get("normalize_unicode"):
        processed_text = normalize_unicode(processed_text)
        applied_steps.append("normalize_unicode")

    if config.get("lowercase"):
        processed_text = lowercase_text(processed_text)
        applied_steps.append("lowercase")

    if config.get("replace_urls"):
        processed_text = replace_urls(processed_text)
        applied_steps.append("replace_urls")

    if config.get("anonymize_mentions"):
        processed_text = anonymize_mentions(processed_text)
        applied_steps.append("anonymize_mentions")

    if config.get("normalize_hashtags"):
        processed_text = normalize_hashtags(processed_text)
        applied_steps.append("normalize_hashtags")

    if config.get("convert_emojis_to_text"):
        processed_text = convert_emojis_to_text(processed_text)
        applied_steps.append("convert_emojis_to_text")

    if config.get("expand_abbreviations"):
        processed_text = expand_abbreviations(processed_text)
        applied_steps.append("expand_abbreviations")

    if config.get("reduce_repeated_characters"):
        processed_text = reduce_repeated_characters(processed_text)
        applied_steps.append("reduce_repeated_characters")

    if config.get("remove_special_characters"):
        processed_text = remove_special_characters(processed_text)
        applied_steps.append("remove_special_characters")

    if config.get("remove_selected_punctuation"):
        processed_text = remove_selected_punctuation(processed_text)
        applied_steps.append("remove_selected_punctuation")

    if config.get("normalize_spaces"):
        processed_text = normalize_spaces(processed_text)
        applied_steps.append("normalize_spaces")

    requires_tokens = (
        config.get("tokenize")
        or config.get("remove_stopwords")
        or config.get("stemming")
        or config.get("lemmatization")
    )

    if requires_tokens:
        tokens = tokenize_text(processed_text)
        applied_steps.append("tokenize")

    if config.get("remove_stopwords"):
        tokens = remove_stopwords(tokens)
        processed_text = " ".join(tokens)
        applied_steps.append("remove_stopwords")

    if config.get("stemming"):
        tokens = stem_tokens(tokens)
        processed_text = " ".join(tokens)
        applied_steps.append("stemming")

    if config.get("lemmatization"):
        tokens = lemmatize_tokens(tokens)
        processed_text = " ".join(tokens)
        applied_steps.append("lemmatization")

    processed_text = normalize_spaces(processed_text)

    if requires_tokens and not tokens:
        tokens = tokenize_text(processed_text)

    is_empty_after_processing = processed_text.strip() == ""

    return {
        "original_text": original_text,
        "processed_text": processed_text,
        "tokens": tokens,
        "emojis": emojis,
        "hashtags": hashtags,
        "applied_steps": applied_steps,
        "original_length": len(original_text),
        "processed_length": len(processed_text),
        "word_count": len(processed_text.split()),
        "token_count": len(tokens),
        "emoji_count": len(emojis),
        "hashtag_count": original_social_markers["hashtag_count"],
        "url_count": original_social_markers["url_count"],
        "mention_count": original_social_markers["mention_count"],
        "has_url": original_social_markers["has_url"],
        "has_mention": original_social_markers["has_mention"],
        "has_hashtag": original_social_markers["has_hashtag"],
        "is_empty_after_processing": is_empty_after_processing
    }