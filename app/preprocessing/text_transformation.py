"""
Operações de transformação linguística aplicadas ao texto e aos tokens.

Este módulo disponibiliza funções para:

- expandir abreviações frequentes nas redes sociais;
- tokenizar o texto;
- remover stopwords;
- aplicar stemming;
- aplicar lematização.

As listas e os recursos atuais estão orientados para textos em inglês. Esta
limitação deve ser considerada quando o sistema processa datasets noutros
idiomas.
"""
import re

# Marcadores estruturais produzidos pelo módulo de limpeza textual.
#
# Estes valores devem ser preservados durante as operações de stemming,
# lematização e remoção de stopwords.
PROTECTED_TOKENS = {
    "[URL]",
    "[USER]"
}

# Abreviações e contrações frequentes em textos informais em inglês.
#
# A chave corresponde à forma abreviada e o valor à sua expansão.
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

# Stopwords básicas em inglês.
#
# A lista não inclui palavras negativas como "not", porque a sua remoção
# poderia alterar significativamente a polaridade ou o significado afetivo
# da publicação.
STOPWORDS_EN = {
    "a", "an", "the", "and", "or", "but", "if", "while",
    "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "in", "on", "for", "with", "as", "by",
    "at", "from", "this", "that", "these", "those",
    "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their"
}


# Constrói um padrão que reconhece as abreviações independentemente de
# maiúsculas e minúsculas.
#
# As chaves são ordenadas por comprimento para assegurar que formas maiores,
# como "you're", sejam testadas antes de formas menores.
ABBREVIATION_PATTERN = re.compile(
    r"(?<!\w)("
    + "|".join(
        re.escape(abbreviation)
        for abbreviation in sorted(
            BASIC_ABBREVIATIONS,
            key=len,
            reverse=True
        )
    )
    + r")(?!\w)",
    flags=re.IGNORECASE
)

# Reconhece primeiro os marcadores [URL] e [USER] e, em seguida,
# palavras e números delimitados por fronteiras lexicais.
TOKEN_PATTERN = re.compile(
    r"\[URL\]|\[USER\]|\b\w+\b"
)


# O NLTK é uma dependência das operações linguísticas avançadas.
#
# A importação é efetuada uma única vez quando o módulo é carregado,
# evitando repetir a importação e a criação dos processadores em cada chamada.
try:
    from nltk.stem import PorterStemmer, WordNetLemmatizer
except ImportError:
    PorterStemmer = None
    WordNetLemmatizer = None


# Cria instâncias reutilizáveis, quando o NLTK está instalado.
PORTER_STEMMER = (
    PorterStemmer()
    if PorterStemmer is not None
    else None
)

WORDNET_LEMMATIZER = (
    WordNetLemmatizer()
    if WordNetLemmatizer is not None
    else None
)


def expand_abbreviations(text: str) -> str:
    """
    Expande abreviações e contrações frequentes em inglês.

    Ao contrário de uma separação simples através de espaços, a expressão
    regular permite reconhecer abreviações junto a sinais de pontuação.

    Por exemplo, ``omg!`` é corretamente transformado em ``oh my god!``.

    Args:
        text: Texto no qual as abreviações serão expandidas.

    Returns:
        str: Texto com as abreviações conhecidas substituídas.

    Examples:
        >>> expand_abbreviations("omg! i'm happy")
        "oh my god! i am happy"

        >>> expand_abbreviations("idk, but it's fine")
        "i do not know, but it is fine"
    """


    if not isinstance(text, str):
        return ""

    # Normaliza o apóstrofo tipográfico para permitir que formas como
    # “don’t” sejam reconhecidas através da entrada "don't".
    normalized_text = text.replace("’", "'")

    def replace_abbreviation(match: re.Match) -> str:
        abbreviation = match.group(0).lower()
        return BASIC_ABBREVIATIONS[abbreviation]

    return ABBREVIATION_PATTERN.sub(
        replace_abbreviation,
        normalized_text
    )



def tokenize_text(text: str) -> list[str]:
    """
    Divide o texto numa sequência de tokens.

    A tokenização preserva explicitamente os marcadores ``[URL]`` e ``[USER]``.
    As restantes palavras e números são identificados através da expressão
    regular ``\\b\\w+\\b``.

    Args:
        text: Texto que será tokenizado.

    Returns:
        list[str]: Tokens encontrados, pela ordem em que surgem no texto.

    Example:
        >>> tokenize_text("[USER] gostei deste site [URL]")
        ["[USER]", "gostei", "deste", "site", "[URL]"]
    """    
    if not isinstance(text, str):
        return []

    return TOKEN_PATTERN.findall(text)


def remove_stopwords(tokens: list[str]) -> list[str]:
    """
    Remove stopwords inglesas de uma lista de tokens.

    Os marcadores ``[URL]`` e ``[USER]`` são preservados, mesmo que uma
    configuração futura inclua valores semelhantes na lista de stopwords.

    Args:
        tokens: Tokens que serão filtrados.

    Returns:
        list[str]: Tokens que não pertencem à lista de stopwords.
    """    
    if not isinstance(tokens, list):
        return []

    return [
        token
        for token in tokens
        if (
            token in PROTECTED_TOKENS
            or token.lower() not in STOPWORDS_EN
        )
    ]



def stem_tokens(tokens: list[str]) -> list[str]:
    """
    Aplica o algoritmo Porter Stemmer aos tokens.

    O stemming reduz palavras a uma forma radical, que pode não corresponder
    a uma palavra válida. Por exemplo, ``studies`` pode ser reduzido a
    uma forma como ``studi``.

    Os marcadores estruturais são preservados sem alteração.

    Args:
        tokens: Tokens que serão submetidos ao stemming.

    Returns:
        list[str]: Tokens transformados.

    Raises:
        RuntimeError: Quando a biblioteca NLTK não está instalada.
    """

    if not isinstance(tokens, list):
        return []

    # Falhar explicitamente evita indicar que o stemming foi aplicado quando,
    # na realidade, a dependência necessária não está disponível.
    if PORTER_STEMMER is None:
        raise RuntimeError(
            "Não foi possível aplicar stemming porque a biblioteca "
            "NLTK não está instalada."
        )

    stemmed_tokens: list[str] = []

    for token in tokens:
        if token in PROTECTED_TOKENS:
            stemmed_tokens.append(token)
        else:
            stemmed_tokens.append(
                PORTER_STEMMER.stem(token)
            )

    return stemmed_tokens



def lemmatize_tokens(tokens: list[str]) -> list[str]:
    """
    Aplica lematização através do WordNetLemmatizer.

    A lematização procura converter cada token para a respetiva forma canónica.
    Ao contrário do stemming, pretende produzir palavras linguisticamente
    válidas.

    Os marcadores ``[URL]`` e ``[USER]`` são preservados.

    Args:
        tokens: Tokens que serão lematizados.

    Returns:
        list[str]: Tokens lematizados.

    Raises:
        RuntimeError: Quando o NLTK não está instalado ou quando os recursos
        WordNet necessários não estão disponíveis.
    """

    if not isinstance(tokens, list):
        return []

    if WORDNET_LEMMATIZER is None:
        raise RuntimeError(
            "Não foi possível aplicar lematização porque a biblioteca "
            "NLTK não está instalada."
        )

    lemmatized_tokens: list[str] = []

    try:
        for token in tokens:
            if token in PROTECTED_TOKENS:
                lemmatized_tokens.append(token)
            else:
                lemmatized_tokens.append(
                    WORDNET_LEMMATIZER.lemmatize(token)
                )

        return lemmatized_tokens

    except LookupError as error:
        # O WordNetLemmatizer requer recursos adicionais do NLTK.
        #
        # A exceção explícita evita que a operação seja registada como aplicada
        # quando os tokens foram devolvidos sem qualquer transformação.
        raise RuntimeError(
            "Os recursos WordNet necessários para a lematização "
            "não estão instalados."
        ) from error