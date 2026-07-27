"""
Operações de identificação e transformação de emojis.

Este módulo disponibiliza funções auxiliares utilizadas pelo pipeline de
pré-processamento para:

- identificar emojis presentes numa publicação;
- converter emojis numa representação textual.

Os emojis constituem elementos relevantes para a análise afetiva, uma vez que
podem complementar, reforçar ou alterar o significado emocional do texto.
"""
import emoji


def extract_emojis(text: str) -> list[str]:
    """
    Extrai os emojis existentes num texto.

    A função percorre o conteúdo recebido e devolve os caracteres reconhecidos
    pela biblioteca ``emoji`` como emojis.

    Args:
        text: Texto no qual os emojis serão identificados.

    Returns:
        list[str]: Emojis encontrados, pela ordem em que surgem no texto.
        Quando o valor recebido não é uma string, é devolvida uma lista vazia.

    Example:
        >>> extract_emojis("Estou muito feliz! 😄❤️")
        ["😄", "❤"]
    """

    # Garante que a função apenas tenta processar valores textuais.
    if not isinstance(text, str):
        return []
    # Verifica individualmente os caracteres do texto e mantém apenas aqueles
    # que se encontram registados como emojis pela biblioteca.    
    if emoji is None:
        return []

    return [char for char in text if char in emoji.EMOJI_DATA]


def convert_emojis_to_text(text: str) -> str:
    """
    Converte os emojis existentes num texto para descrições textuais.

    Esta transformação pode tornar a informação semântica dos emojis
    explicitamente disponível para operações posteriores, como tokenização,
    classificação emocional ou aplicação de modelos de aprendizagem automática.

    Atualmente, as descrições são produzidas em inglês.

    Args:
        text: Texto que poderá conter emojis.

    Returns:
        str: Texto com os emojis convertidos para descrições textuais.
        Quando o valor recebido não é uma string, é devolvido um texto vazio.

    Example:
        >>> convert_emojis_to_text("Estou feliz 😄")
        "Estou feliz :grinning_face_with_smiling_eyes:"
    """    
    if not isinstance(text, str):
        return ""

    if emoji is None:
        return text

    # Converte os emojis para nomes delimitados por dois pontos.
    #
    # A opção language="en" determina que os nomes produzidos estejam em inglês.    
    return emoji.demojize(text, language="en")