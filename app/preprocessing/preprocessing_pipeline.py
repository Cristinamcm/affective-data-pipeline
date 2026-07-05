from app.preprocessing.emoji_processor import (
    convert_emojis_to_text,
    extract_emojis
)
from app.preprocessing.text_cleaner import clean_text
from app.preprocessing.text_metrics import compute_text_metrics


def extract_emotion_labels(record: dict) -> list[str]:
    emotion_columns = [
        "anger",
        "anticipation",
        "disgust",
        "fear",
        "joy",
        "love",
        "optimism",
        "pessimism",
        "sadness",
        "surprise",
        "trust"
    ]

    labels = []

    for emotion in emotion_columns:
        value = record.get(emotion)

        if value in [1, "1", True, "true", "True"]:
            labels.append(emotion)

    if not labels and record.get("label"):
        labels.append(str(record.get("label")))

    return labels


def preprocess_record(record: dict) -> dict:
    original_text = record.get("text", "")

    emojis = extract_emojis(original_text)
    text_with_emojis_as_words = convert_emojis_to_text(original_text)
    cleaned_text = clean_text(text_with_emojis_as_words)

    metrics = compute_text_metrics(
        original_text=original_text,
        cleaned_text=cleaned_text
    )

    return {
        **record,
        "cleaned_text": cleaned_text,
        "text_with_emojis_as_words": text_with_emojis_as_words,
        "language": "unknown",
        "emojis": " ".join(emojis),
        "emoji_count": len(emojis),
        "emotion_labels": extract_emotion_labels(record),
        "processing_version": "v1",
        **metrics
    }

# próximas implementações:
# deteção de idioma, extração de emojis, normalização de hashtags, etc.