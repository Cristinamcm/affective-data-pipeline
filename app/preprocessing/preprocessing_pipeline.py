from app.preprocessing.text_cleaner import clean_text
from app.preprocessing.emoji_processor import extract_emojis, convert_emojis_to_text


def preprocess_record(record: dict) -> dict:
    original_text = record.get("text", "")

    emojis = extract_emojis(original_text)
    text_with_emojis_as_words = convert_emojis_to_text(original_text)
    cleaned_text = clean_text(text_with_emojis_as_words)

    return {
        **record,
        "cleaned_text": cleaned_text,
        "emojis": " ".join(emojis),
        "emoji_count": len(emojis)
    }

# próximas implementações:
# deteção de idioma, extração de emojis, normalização de hashtags, etc.