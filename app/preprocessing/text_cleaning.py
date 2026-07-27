"""
Operações de limpeza, normalização e deteção de elementos sociais.

Este módulo contém funções utilizadas pelo pipeline para:

- normalizar caracteres Unicode;
- converter texto para minúsculas;
- normalizar espaços;
- substituir URLs;
- anonimizar menções;
- extrair e normalizar hashtags;
- reduzir caracteres repetidos;
- remover caracteres de controlo e pontuação;
- detetar URLs, menções e hashtags no texto original.

As funções deste módulo são independentes da base de dados e não alteram
diretamente os registos armazenados. Recebem um texto e devolvem o respetivo
resultado transformado ou as métricas calculadas.
"""

import re
import unicodedata
from typing import TypedDict


class SocialMarkerMetrics(TypedDict):
    """
    Estrutura das métricas associadas aos elementos característicos
    das publicações em redes sociais.
    """

    url_count: int
    mention_count: int
    hashtag_count: int
    has_url: bool
    has_mention: bool
    has_hashtag: bool


# Expressões regulares reutilizadas pelas diferentes funções.
#
# A sua definição ao nível do módulo evita recompilar o mesmo padrão
# sempre que uma função é executada.
WHITESPACE_PATTERN = re.compile(r"\s+")

URL_PATTERN = re.compile(
    r"(https?://\S+|www\.\S+)",
    flags=re.IGNORECASE
)

MENTION_PATTERN = re.compile(r"@\w+")

# O grupo de captura devolve apenas o conteúdo textual da hashtag,
# excluindo o carácter inicial "#".
HASHTAG_PATTERN = re.compile(r"#(\w+)")

# Identifica caracteres repetidos três ou mais vezes.
REPEATED_CHARACTER_PATTERN = re.compile(r"(.)\1{2,}")

# Caracteres de controlo pertencentes aos intervalos C0 e C1 do Unicode.
CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x1f\x7f-\x9f]")

# Remove pontuação e símbolos, preservando:
# - caracteres alfanuméricos;
# - espaços;
# - parênteses retos utilizados nos marcadores [URL] e [USER].
SELECTED_PUNCTUATION_PATTERN = re.compile(r"[^\w\s\[\]]")



def normalize_unicode(text: str) -> str:
    """
    Normaliza a representação Unicode de um texto.

    É utilizada a forma NFKC, que converte caracteres visual ou
    semanticamente equivalentes numa representação mais uniforme.

    Esta operação ajuda a reduzir diferenças entre caracteres provenientes
    de diferentes fontes, sistemas ou formatos de codificação.

    Args:
        text: Texto que será normalizado.

    Returns:
        str: Texto normalizado. Quando o valor recebido não é uma string,
        é devolvido um texto vazio.
    """
    if not isinstance(text, str):
        return ""

    return unicodedata.normalize("NFKC", text)


def lowercase_text(text: str) -> str:
    """
    Converte todos os caracteres textuais para minúsculas.

    Esta operação reduz variações lexicais, permitindo que palavras como
    ``Feliz``, ``FELIZ`` e ``feliz`` sejam tratadas de forma equivalente.

    Args:
        text: Texto que será convertido.

    Returns:
        str: Texto convertido para minúsculas.
    """

    if not isinstance(text, str):
        return ""

    return text.lower()


def normalize_spaces(text: str) -> str:
    """
    Normaliza os espaços existentes num texto.

    Sequências de espaços, tabulações e mudanças de linha são substituídas
    por um único espaço. Os espaços existentes no início e no fim também
    são removidos.

    Args:
        text: Texto que será normalizado.

    Returns:
        str: Texto com os espaços normalizados.

    Example:
        >>> normalize_spaces("Estou   muito\\n feliz")
        "Estou muito feliz"
    """    
    if not isinstance(text, str):
        return ""

    return WHITESPACE_PATTERN.sub(" ", text).strip()


def replace_urls(text: str) -> str:
    """
    Substitui os URLs encontrados por um marcador normalizado.

    O marcador ``[URL]`` preserva a informação de que existia uma ligação
    no texto sem manter o endereço original. Esta transformação contribui
    para a redução de ruído e para a minimização de informação potencialmente
    identificável.

    São reconhecidos endereços iniciados por:

    - http://
    - https://
    - www.

    Args:
        text: Texto que poderá conter URLs.

    Returns:
        str: Texto com os URLs substituídos pelo marcador ``[URL]``.

    Example:
        >>> replace_urls("Visita https://example.com")
        "Visita  [URL] "
    """

    if not isinstance(text, str):
        return ""

    return URL_PATTERN.sub(
        " [URL] ",
        text
    )


def anonymize_mentions(text: str) -> str:
    """
    Substitui menções a utilizadores por um marcador anónimo.

    Menções como ``@maria`` ou ``@user123`` são substituídas por ``[USER]``.
    A transformação reduz a exposição direta de identificadores de utilizador
    presentes nos dados recolhidos.

    Args:
        text: Texto que poderá conter menções.

    Returns:
        str: Texto com as menções anonimizadas.

    Example:
        >>> anonymize_mentions("@maria gostei muito")
        " [USER]  gostei muito"
    """

    if not isinstance(text, str):
        return ""

    return MENTION_PATTERN.sub(
        " [USER] ",
        text
    )


def extract_hashtags(text: str) -> list[str]:
    """
    Extrai as hashtags existentes num texto.

    O carácter ``#`` não é incluído nos valores devolvidos. A ordem e as
    repetições das hashtags são preservadas.

    Args:
        text: Texto no qual as hashtags serão identificadas.

    Returns:
        list[str]: Conteúdo textual das hashtags encontradas.

    Example:
        >>> extract_hashtags("Estou #feliz com estas #boasnoticias")
        ["feliz", "boasnoticias"]
    """

    if not isinstance(text, str):
        return []

    return HASHTAG_PATTERN.findall(text)


def normalize_hashtags(text: str) -> str:
    """
    Remove o carácter inicial das hashtags, preservando o respetivo conteúdo.

    Esta operação não elimina semanticamente a hashtag. Apenas transforma
    ``#feliz`` em ``feliz``, permitindo que o conteúdo seja tratado como texto
    normal em operações posteriores.

    Args:
        text: Texto que poderá conter hashtags.

    Returns:
        str: Texto com as hashtags normalizadas.

    Example:
        >>> normalize_hashtags("Hoje estou #feliz")
        "Hoje estou feliz"
    """

    if not isinstance(text, str):
        return ""

    return HASHTAG_PATTERN.sub(
        r"\1",
        text
    )


def reduce_repeated_characters(text: str) -> str:
    """
    Reduz sequências de caracteres repetidos.

    Quando um carácter ocorre três ou mais vezes consecutivas, a sequência
    é reduzida para duas ocorrências.

    Esta operação procura diminuir variações informais frequentes nas redes
    sociais, preservando parcialmente o indicador de intensidade.

    Args:
        text: Texto que será processado.

    Returns:
        str: Texto com as repetições reduzidas.

    Examples:
        >>> reduce_repeated_characters("felizzzzz")
        "felizz"

        >>> reduce_repeated_characters("adorei!!!!!")
        "adorei!!"
    """

    if not isinstance(text, str):
        return ""

    return REPEATED_CHARACTER_PATTERN.sub(
        r"\1\1",
        text
    )


def remove_special_characters(text: str) -> str:
    """
    Remove caracteres de controlo existentes no texto.

    Apesar do nome da função, esta operação não remove todos os caracteres
    especiais. Remove especificamente caracteres de controlo, como determinadas
    tabulações, separadores e símbolos não imprimíveis.

    Os caracteres encontrados são substituídos por espaços para evitar a união
    indevida de palavras.

    Args:
        text: Texto que será limpo.

    Returns:
        str: Texto sem caracteres de controlo.
    """

    if not isinstance(text, str):
        return ""

    return CONTROL_CHARACTER_PATTERN.sub(
        " ",
        text
    )


def remove_selected_punctuation(text: str) -> str:
    """
    Remove sinais de pontuação e símbolos selecionados.

    São preservados caracteres alfanuméricos, espaços e parênteses retos.
    A preservação dos parênteses retos impede que marcadores como ``[URL]``
    e ``[USER]`` sejam destruídos.

    Depois da remoção, os espaços resultantes são normalizados.

    Args:
        text: Texto que será processado.

    Returns:
        str: Texto sem os sinais de pontuação selecionados.

    Important:
        Emojis também podem ser removidos por esta operação, uma vez que
        geralmente não pertencem às categorias preservadas pela expressão
        regular. Quando é necessário manter o significado dos emojis, estes
        devem ser convertidos para texto antes desta etapa.
    """

    if not isinstance(text, str):
        return ""

    cleaned_text = SELECTED_PUNCTUATION_PATTERN.sub(
        " ",
        text
    )

    return normalize_spaces(cleaned_text)


def count_urls(text: str) -> int:
    """
    Conta os URLs existentes num texto.

    Args:
        text: Texto que será analisado.

    Returns:
        int: Número de URLs encontrados.
    """

    if not isinstance(text, str):
        return 0

    return len(URL_PATTERN.findall(text))


def count_mentions(text: str) -> int:
    """
    Conta as menções a utilizadores existentes num texto.

    Args:
        text: Texto que será analisado.

    Returns:
        int: Número de menções encontradas.
    """

    if not isinstance(text, str):
        return 0

    return len(MENTION_PATTERN.findall(text))


def count_hashtags(text: str) -> int:
    """
    Conta as hashtags existentes num texto.

    Args:
        text: Texto que será analisado.

    Returns:
        int: Número de hashtags encontradas.
    """

    if not isinstance(text, str):
        return 0

    return len(HASHTAG_PATTERN.findall(text))


def detect_social_markers(text: str) -> SocialMarkerMetrics:
    """
    Identifica e contabiliza elementos característicos das redes sociais.

    A função calcula numa única passagem lógica as quantidades de URLs,
    menções e hashtags e produz também indicadores booleanos da presença
    desses elementos.

    Estas métricas representam o conteúdo original, antes da aplicação
    das operações de pré-processamento.

    Args:
        text: Texto original da publicação.

    Returns:
        SocialMarkerMetrics: Quantidades e indicadores dos elementos
        sociais encontrados.
    """
    # Cada contador é executado apenas uma vez.
    #
    # No código anterior, cada função era executada duas vezes:
    # uma para obter a quantidade e outra para calcular o indicador booleano.
    url_count = count_urls(text)
    mention_count = count_mentions(text)
    hashtag_count = count_hashtags(text)

    return {
        "url_count": url_count,
        "mention_count": mention_count,
        "hashtag_count": hashtag_count,
        "has_url": url_count > 0,
        "has_mention": mention_count > 0,
        "has_hashtag": hashtag_count > 0
    }