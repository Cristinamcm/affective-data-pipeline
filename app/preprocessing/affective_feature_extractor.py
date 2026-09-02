"""
Extração de características relevantes para análise afetiva.

Este módulo recebe o texto original e o texto resultante do pré-processamento
e extrai indicadores estruturados que poderão ser utilizados posteriormente
por modelos de análise afetiva.

São considerados:

- emojis;
- hashtags;
- termos afetivos;
- utilização de maiúsculas;
- pontos de exclamação;
- pontos de interrogação;
- caracteres repetidos;
- indicador estrutural de intensidade.

Este módulo não realiza classificação emocional. O objetivo consiste apenas
em identificar e estruturar sinais potencialmente relevantes para análises
posteriores.
"""

import re
from typing import Any

from app.preprocessing.emoji_processing import extract_emojis
from app.preprocessing.text_cleaning import extract_hashtags


# =============================================================================
# LÉXICOS AFETIVOS BASE
# =============================================================================

# Vocabulário lexical simples utilizado nesta primeira versão do protótipo.
#
# O objetivo não consiste em classificar emoções, mas apenas identificar
# palavras explicitamente associadas a estados ou expressões afetivas.
#
# Numa evolução futura esta lista poderá ser substituída por um recurso
# lexical validado e mais abrangente.
AFFECTIVE_TERMS_EN = {
    "happy",
    "happiness",
    "joy",
    "joyful",
    "sad",
    "sadness",
    "angry",
    "anger",
    "afraid",
    "fear",
    "scared",
    "surprise",
    "surprised",
    "disgust",
    "disgusted",
    "love",
    "loved",
    "loving",
    "hate",
    "hated",
    "excited",
    "anxious",
    "anxiety",
    "calm",
    "proud",
    "shame",
    "ashamed",
    "guilty",
    "frustrated",
    "frustration",
    "worried",
    "worry",
    "delighted",
    "upset"
}


AFFECTIVE_TERMS_PT = {
    "feliz",
    "felicidade",
    "alegre",
    "alegria",
    "triste",
    "tristeza",
    "zangado",
    "zangada",
    "raiva",
    "medo",
    "assustado",
    "assustada",
    "surpresa",
    "surpreso",
    "surpreendida",
    "nojo",
    "repulsa",
    "amor",
    "amar",
    "adoro",
    "odeio",
    "ódio",
    "entusiasmado",
    "entusiasmada",
    "ansioso",
    "ansiosa",
    "ansiedade",
    "calmo",
    "calma",
    "orgulhoso",
    "orgulhosa",
    "vergonha",
    "culpa",
    "frustrado",
    "frustrada",
    "preocupado",
    "preocupada"
}


AFFECTIVE_LEXICONS = {
    "en": AFFECTIVE_TERMS_EN,
    "pt": AFFECTIVE_TERMS_PT
}


# =============================================================================
# EXPRESSÕES REGULARES
# =============================================================================

# Identifica palavras, incluindo caracteres Unicode.
WORD_PATTERN = re.compile(
    r"\b[\wÀ-ÿ'-]+\b",
    flags=re.UNICODE
)


# Identifica sequências em que o mesmo carácter ocorre pelo menos
# três vezes consecutivamente.
#
# Exemplos:
#
# happyyyyy
# nooooo
# !!!!!
REPEATED_PATTERN = re.compile(
    r"(.)\1{2,}",
    flags=re.UNICODE
)


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def normalize_language(
    language: str | None
) -> str | None:
    """
    Normaliza um código de idioma.

    Exemplos:

        en-US -> en
        pt-PT -> pt
        PT    -> pt
    """

    if not language:
        return None

    normalized = (
        language
        .strip()
        .lower()
        .replace("_", "-")
        .split("-")[0]
    )

    if normalized in AFFECTIVE_LEXICONS:
        return normalized

    return None


def extract_affective_terms(
    text: str,
    language: str | None
) -> list[str]:
    """
    Identifica termos explicitamente afetivos num texto.

    A função não atribui uma emoção nem polaridade aos termos.
    Limita-se a identificar ocorrências pertencentes ao léxico configurado.
    """

    if not isinstance(text, str):
        return []

    normalized_language = normalize_language(
        language
    )

    if normalized_language is None:
        return []

    lexicon = AFFECTIVE_LEXICONS[
        normalized_language
    ]

    words = WORD_PATTERN.findall(
        text.lower()
    )

    return [
        word
        for word in words
        if word in lexicon
    ]


def calculate_uppercase_ratio(
    text: str
) -> float:
    """
    Calcula a proporção de letras maiúsculas relativamente ao número total
    de caracteres alfabéticos.

    Caracteres não alfabéticos não entram no denominador.
    """

    if not isinstance(text, str):
        return 0.0

    alphabetic_characters = [
        character
        for character in text
        if character.isalpha()
    ]

    if not alphabetic_characters:
        return 0.0

    uppercase_characters = sum(
        1
        for character in alphabetic_characters
        if character.isupper()
    )

    return (
        uppercase_characters
        / len(alphabetic_characters)
    )


def count_repeated_characters(
    text: str
) -> int:
    """
    Conta os caracteres que excedem duas repetições consecutivas.

    Exemplo:

        soooo

    possui quatro caracteres 'o' consecutivos.

    Como duas ocorrências são consideradas preservadas pelo pipeline:

        oo

    existem dois caracteres de intensificação adicionais.

    O resultado será, portanto, 2.
    """

    if not isinstance(text, str):
        return 0

    repeated_characters = 0

    for match in REPEATED_PATTERN.finditer(
        text
    ):

        sequence_length = len(
            match.group(0)
        )

        repeated_characters += max(
            sequence_length - 2,
            0
        )

    return repeated_characters


def calculate_intensity_score(
    text: str,
    uppercase_ratio: float,
    emoji_count: int,
    exclamation_count: int,
    question_count: int,
    repeated_characters_count: int
) -> float:
    """
    Calcula um indicador estrutural de intensidade entre 0 e 1.

    Este valor não corresponde a probabilidade emocional nem a uma
    classificação de sentimento.

    O indicador agrega quatro tipos de sinais observáveis:

    - utilização de maiúsculas;
    - pontuação expressiva;
    - presença de emojis;
    - repetição de caracteres.

    Os componentes são normalizados para o intervalo [0, 1] e combinados
    através de média simples.
    """

    if not isinstance(text, str) or not text:
        return 0.0

    words = WORD_PATTERN.findall(
        text
    )

    word_count = max(
        len(words),
        1
    )

    character_count = max(
        len(text),
        1
    )

    # Pontuação expressiva relativamente ao número de palavras.
    punctuation_component = min(
        (
            exclamation_count
            + question_count
        )
        / word_count,
        1.0
    )

    # Densidade de emojis relativamente ao número de palavras.
    emoji_component = min(
        emoji_count
        / word_count,
        1.0
    )

    # Proporção de caracteres adicionais provenientes de repetições.
    repetition_component = min(
        repeated_characters_count
        / character_count,
        1.0
    )

    # A proporção de maiúsculas já se encontra no intervalo [0,1].
    uppercase_component = min(
        max(
            uppercase_ratio,
            0.0
        ),
        1.0
    )

    intensity_score = (
        uppercase_component
        + punctuation_component
        + emoji_component
        + repetition_component
    ) / 4

    return round(
        intensity_score,
        4
    )


# =============================================================================
# EXTRAÇÃO PRINCIPAL
# =============================================================================

def extract_affective_features(
    original_text: str,
    processed_text: str,
    language: str | None = None
) -> dict[str, Any]:
    """
    Extrai as características afetivas associadas a um registo processado.

    A estratégia utiliza duas representações do mesmo conteúdo:

    Texto original:
        utilizado para sinais estruturais que podem desaparecer durante
        o pré-processamento, como emojis, hashtags, maiúsculas, pontuação
        expressiva e repetições.

    Texto processado:
        utilizado para identificar termos afetivos depois das operações
        de normalização textual.

    Args:
        original_text:
            Texto original preservado.

        processed_text:
            Texto resultante do pré-processamento.

        language:
            Idioma utilizado na deteção lexical.

    Returns:
        dict:
            Características afetivas estruturadas.
    """

    if not isinstance(
        original_text,
        str
    ):
        original_text = ""

    if not isinstance(
        processed_text,
        str
    ):
        processed_text = ""

    # -------------------------------------------------------------------------
    # Emojis e hashtags
    # -------------------------------------------------------------------------

    emojis = extract_emojis(
        original_text
    )

    hashtags = extract_hashtags(
        original_text
    )

    # -------------------------------------------------------------------------
    # Termos afetivos
    # -------------------------------------------------------------------------

    affective_terms = extract_affective_terms(
        processed_text,
        language
    )

    # -------------------------------------------------------------------------
    # Indicadores estruturais
    # -------------------------------------------------------------------------

    uppercase_ratio = (
        calculate_uppercase_ratio(
            original_text
        )
    )

    exclamation_count = (
        original_text.count(
            "!"
        )
    )

    question_count = (
        original_text.count(
            "?"
        )
    )

    repeated_characters_count = (
        count_repeated_characters(
            original_text
        )
    )

    # -------------------------------------------------------------------------
    # Intensidade estrutural
    # -------------------------------------------------------------------------

    intensity_score = (
        calculate_intensity_score(
            text=original_text,
            uppercase_ratio=uppercase_ratio,
            emoji_count=len(emojis),
            exclamation_count=exclamation_count,
            question_count=question_count,
            repeated_characters_count=(
                repeated_characters_count
            )
        )
    )

    return {
        "emojis": emojis,
        "emoji_count": len(
            emojis
        ),

        "hashtags": hashtags,
        "hashtag_count": len(
            hashtags
        ),

        "affective_terms": affective_terms,
        "affective_term_count": len(
            affective_terms
        ),

        "uppercase_ratio": (
            uppercase_ratio
        ),

        "exclamation_count": (
            exclamation_count
        ),

        "question_count": (
            question_count
        ),

        "repeated_characters_count": (
            repeated_characters_count
        ),

        "intensity_score": (
            intensity_score
        )
    }