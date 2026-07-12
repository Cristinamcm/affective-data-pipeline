import re


BASIC_ABBREVIATIONS = {
    "can't": "cannot",
    "won't": "will not",
    "don't": "do not",
    "doesn't": "does not",
    "didn't": "did not",
    "i'm": "i am",
    "it's": "it is",
    "that's": "that is",
    "you're": "you are",
    "u": "you",
    "ur": "your",
    "idk": "i do not know",
    "lol": "laughing",
    "omg": "oh my god"
}


STOPWORDS_EN = {
    "a", "an", "the", "and", "or", "but", "if", "while",
    "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "in", "on", "for", "with", "as", "by",
    "at", "from", "this", "that", "these", "those",
    "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their"
}


def expand_abbreviations(text: str) -> str:
    if not isinstance(text, str):
        return ""

    words = text.split()
    expanded_words = [
        BASIC_ABBREVIATIONS.get(word.lower(), word)
        for word in words
    ]

    return " ".join(expanded_words)


def tokenize_text(text: str) -> list[str]:
    if not isinstance(text, str):
        return []

    return re.findall(r"\[URL\]|\[USER\]|\b\w+\b", text)


def remove_stopwords(tokens: list[str]) -> list[str]:
    return [
        token
        for token in tokens
        if token.lower() not in STOPWORDS_EN
    ]


def stem_tokens(tokens: list[str]) -> list[str]:
    """
    Aplica stemming simples com NLTK.
    Caso o NLTK não esteja instalado, devolve os tokens originais.
    """
    try:
        from nltk.stem import PorterStemmer
    except ImportError:
        return tokens

    stemmer = PorterStemmer()

    return [
        stemmer.stem(token)
        for token in tokens
        if token not in ["[URL]", "[USER]"]
    ]