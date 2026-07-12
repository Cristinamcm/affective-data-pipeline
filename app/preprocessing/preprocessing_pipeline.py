from app.preprocessing.emoji_processing import (
    convert_emojis_to_text,
    extract_emojis
)


from app.preprocessing.text_cleaning import (
    anonymize_mentions,
    detect_social_markers,
    lowercase_text,
    normalize_hashtags,
    normalize_spaces,
    normalize_unicode,
    reduce_repeated_characters,
    remove_selected_punctuation,
    replace_urls
)
from app.preprocessing.text_transformation import (
    expand_abbreviations,
    remove_stopwords,
    stem_tokens,
    tokenize_text
)


def preprocess_text(
    text: str,
    variant: str = "intermediate"
) -> dict:
    if not isinstance(text, str):
        text = ""

    variant = variant.lower()

    original_text = text
    social_markers = detect_social_markers(original_text)
    emojis = extract_emojis(original_text)

    applied_steps = []

    processed_text = normalize_unicode(original_text)
    applied_steps.append("normalize_unicode")

    processed_text = lowercase_text(processed_text)
    applied_steps.append("lowercase")

    processed_text = replace_urls(processed_text)
    applied_steps.append("replace_urls")

    processed_text = anonymize_mentions(processed_text)
    applied_steps.append("anonymize_mentions")

    processed_text = normalize_spaces(processed_text)
    applied_steps.append("normalize_spaces")

    tokens = tokenize_text(processed_text)

    if variant in ["intermediate", "aggressive"]:
        processed_text = normalize_hashtags(processed_text)
        applied_steps.append("normalize_hashtags")

        processed_text = convert_emojis_to_text(processed_text)
        applied_steps.append("convert_emojis_to_text")

        processed_text = expand_abbreviations(processed_text)
        applied_steps.append("expand_abbreviations")

        processed_text = reduce_repeated_characters(processed_text)
        applied_steps.append("reduce_repeated_characters")

        processed_text = normalize_spaces(processed_text)
        tokens = tokenize_text(processed_text)
        applied_steps.append("tokenize")

    if variant == "aggressive":
        processed_text = remove_selected_punctuation(processed_text)
        applied_steps.append("remove_selected_punctuation")

        tokens = tokenize_text(processed_text)

        tokens = remove_stopwords(tokens)
        applied_steps.append("remove_stopwords")

        tokens = stem_tokens(tokens)
        applied_steps.append("stemming")

        processed_text = " ".join(tokens)
        processed_text = normalize_spaces(processed_text)

    return {
        "original_text": original_text,
        "processed_text": processed_text,
        "tokens": tokens,
        "emojis": emojis,
        "emoji_count": len(emojis),
        "original_length": len(original_text),
        "processed_length": len(processed_text),
        "word_count": len(processed_text.split()),
        "has_url": social_markers["has_url"],
        "has_mention": social_markers["has_mention"],
        "has_hashtag": social_markers["has_hashtag"],
        "applied_steps": applied_steps
    }