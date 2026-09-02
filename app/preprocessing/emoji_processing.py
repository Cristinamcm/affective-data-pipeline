"""
Operações de identificação e transformação de emojis.

Este módulo disponibiliza funções auxiliares utilizadas pelo pipeline de
pré-processamento para:

- identificar emojis presentes num registo textual;
- converter emojis numa representação textual.

Os emojis constituem elementos potencialmente relevantes para análise afetiva,
uma vez que podem complementar, reforçar ou modificar o significado emocional
do conteúdo textual.
"""

import emoji


def extract_emojis(
    text: str
) -> list[str]:
    """
    Extrai os emojis existentes num texto.

    É utilizada a funcionalidade disponibilizada pela biblioteca ``emoji``
    para reconhecer corretamente emojis simples e sequências compostas.

    A ordem e as repetições existentes no texto são preservadas.

    Args:
        text:
            Texto no qual os emojis serão identificados.

    Returns:
        list[str]:
            Emojis encontrados pela ordem em que surgem no texto.

            Quando o valor recebido não é uma string, é devolvida
            uma lista vazia.

    Example:
        >>> extract_emojis("Estou feliz 😄❤️")
        ["😄", "❤️"]
    """

    if not isinstance(text, str):
        return []

    emoji_items = emoji.emoji_list(
        text
    )

    return [
        item["emoji"]
        for item in emoji_items
    ]


def count_emojis(
    text: str
) -> int:
    """
    Conta os emojis existentes num texto.

    Args:
        text:
            Texto que será analisado.

    Returns:
        int:
            Número de emojis encontrados.
    """

    return len(
        extract_emojis(text)
    )


def convert_emojis_to_text(
    text: str
) -> str:
    """
    Converte os emojis existentes num texto para descrições textuais.

    Esta transformação torna explicitamente disponível a informação semântica
    representada pelos emojis para operações posteriores, como tokenização
    ou classificação emocional.

    Atualmente as descrições são produzidas em inglês.

    Args:
        text:
            Texto que poderá conter emojis.

    Returns:
        str:
            Texto no qual os emojis foram convertidos para descrições.

    Example:
        >>> convert_emojis_to_text("Estou feliz 😄")
        "Estou feliz :grinning_face_with_smiling_eyes:"
    """

    if not isinstance(text, str):
        return ""

    return emoji.demojize(
        text,
        language="en"
    )