import emoji


def extract_emojis(text: str) -> list[str]:
    if not isinstance(text, str):
        return []

    return [char for char in text if char in emoji.EMOJI_DATA]


def convert_emojis_to_text(text: str) -> str:
    if not isinstance(text, str):
        return ""

    return emoji.demojize(text, language="en")