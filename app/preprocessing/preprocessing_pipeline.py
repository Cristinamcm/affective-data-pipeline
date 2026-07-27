"""
Pipeline configurável de pré-processamento textual.

Este módulo coordena as operações de preparação aplicadas às publicações
provenientes de redes sociais ou de datasets públicos.

O pipeline permite selecionar individualmente operações relacionadas com:

- normalização textual;
- anonimização de dados;
- tratamento de URLs, menções, hashtags e emojis;
- redução de ruído;
- tokenização;
- remoção de stopwords;
- stemming;
- lematização.

Para além de produzir o texto processado, a função principal devolve informação
sobre os elementos identificados, as transformações realizadas e várias
métricas utilizadas na avaliação do comportamento do pipeline.
"""

from typing import Any

from app.preprocessing.emoji_processing import (
    convert_emojis_to_text,
    extract_emojis
)
from app.preprocessing.presets import normalize_config
from app.preprocessing.text_cleaning import (
    anonymize_mentions,
    detect_social_markers,
    extract_hashtags,
    lowercase_text,
    normalize_hashtags,
    normalize_spaces,
    normalize_unicode,
    reduce_repeated_characters,
    remove_selected_punctuation,
    remove_special_characters,
    replace_urls
)
from app.preprocessing.text_transformation import (
    expand_abbreviations,
    lemmatize_tokens,
    remove_stopwords,
    stem_tokens,
    tokenize_text
)


def preprocess_text(text: str, config: dict | None = None) -> dict:
    """
    Aplica uma configuração de pré-processamento a um texto.

    A configuração é normalizada antes da execução, garantindo que todas as
    operações suportadas possuem um valor booleano. As transformações são
    aplicadas sequencialmente, de acordo com a ordem definida no pipeline.

    Args:
        text: Texto original da publicação.
        config: Operações de pré-processamento selecionadas. As operações
            ausentes são consideradas desativadas.

    Returns:
        dict[str, Any]: Texto original e processado, estruturas extraídas,
        etapas aplicadas, indicadores de presença e métricas de transformação.
    """

    # Completa a configuração recebida com todas as operações suportadas.    
    config = normalize_config(config)

    # Converte entradas inválidas num texto vazio, garantindo que as funções
    # seguintes recebem sempre uma string.
    if not isinstance(text, str):
        text = ""

    # Preserva o conteúdo original para permitir comparação, rastreabilidade
    # e cálculo de métricas antes e depois do processamento.
    original_text = text

    # Identifica URLs, menções e hashtags existentes no texto original.
    #
    # Esta deteção é efetuada antes de qualquer transformação, garantindo que
    # as métricas representam o conteúdo recebido pelo sistema.
    original_social_markers = detect_social_markers(original_text)

    # Os emojis originais são sempre identificados para permitir calcular
    # corretamente as métricas, independentemente de o utilizador ter escolhido
    # apresentar a lista de emojis extraídos.
    original_emojis = extract_emojis(original_text)


    # Estruturas devolvidas pelo pipeline.
    emojis: list[str] = []
    hashtags: list[str] = []
    tokens: list[str] = []
    applied_steps: list[str] = []

    # -------------------------------------------------------------------------
    # Extração de elementos antes das transformações
    # -------------------------------------------------------------------------    

    if config.get("extract_emojis"):
        # Disponibiliza separadamente os emojis presentes no texto original.
        emojis = extract_emojis(original_text)
        applied_steps.append("extract_emojis")

    if config.get("extract_hashtags"):
        # Extrai as hashtags antes de estas poderem ser normalizadas ou alteradas.
        hashtags = extract_hashtags(original_text)
        applied_steps.append("extract_hashtags")

    # O texto processado começa como uma cópia do conteúdo original.
    processed_text = original_text

    # -------------------------------------------------------------------------
    # Normalização e tratamento dos elementos das redes sociais
    # -------------------------------------------------------------------------

    if config.get("normalize_unicode"):
        # Uniformiza diferentes representações Unicode equivalentes.
        processed_text = normalize_unicode(processed_text)
        applied_steps.append("normalize_unicode")

    if config.get("lowercase"):
        # Converte o texto para minúsculas para reduzir variações lexicais.
        processed_text = lowercase_text(processed_text)
        applied_steps.append("lowercase")

    if config.get("replace_urls"):
        # Substitui cada URL por um marcador normalizado, como [URL].
        processed_text = replace_urls(processed_text)
        applied_steps.append("replace_urls")

    if config.get("anonymize_mentions"):
        # Substitui referências a utilizadores por um marcador anónimo,
        # reduzindo a exposição de identificadores pessoais.        
        processed_text = anonymize_mentions(processed_text)
        applied_steps.append("anonymize_mentions")

    if config.get("normalize_hashtags"):
        # Normaliza a representação das hashtags, preservando o respetivo
        # conteúdo textual para posterior análise.        
        processed_text = normalize_hashtags(processed_text)
        applied_steps.append("normalize_hashtags")

    if config.get("convert_emojis_to_text"):
        # Converte os emojis para descrições textuais antes da tokenização.        
        processed_text = convert_emojis_to_text(processed_text)
        applied_steps.append("convert_emojis_to_text")

    # -------------------------------------------------------------------------
    # Redução de ruído e normalização linguística
    # -------------------------------------------------------------------------

    if config.get("expand_abbreviations"):
        # Substitui abreviações conhecidas pelas respetivas formas completas
        processed_text = expand_abbreviations(processed_text)
        applied_steps.append("expand_abbreviations")

    if config.get("reduce_repeated_characters"):
        # Reduz repetições utilizadas para intensificação, como:
        # "felizzzzz" → "felizz", dependendo da implementação da função.        
        processed_text = reduce_repeated_characters(processed_text)
        applied_steps.append("reduce_repeated_characters")

    if config.get("remove_special_characters"):
        # Remove caracteres especiais considerados ruído para o processamento.
        processed_text = remove_special_characters(processed_text)
        applied_steps.append("remove_special_characters")

    if config.get("remove_selected_punctuation"):
        # Remove apenas os sinais de pontuação definidos pela função,
        # permitindo preservar elementos considerados afetivamente relevantes.        
        processed_text = remove_selected_punctuation(processed_text)
        applied_steps.append("remove_selected_punctuation")

    if config.get("normalize_spaces"):
        # Reduz sequências de espaços, tabulações e quebras de linha.
        processed_text = normalize_spaces(processed_text)
        applied_steps.append("normalize_spaces")

    # -------------------------------------------------------------------------
    # Preparação das operações baseadas em tokens
    # -------------------------------------------------------------------------

    # Algumas operações precisam de tokens mesmo quando a opção explícita
    # "tokenize" não foi selecionada.
    requires_tokens = (
        config.get("tokenize")
        or config.get("remove_stopwords")
        or config.get("stemming")
        or config.get("lemmatization")
    )

    if requires_tokens:
        tokens = tokenize_text(processed_text)
        applied_steps.append("tokenize")

    if config.get("remove_stopwords"):
        # Remove palavras funcionais de elevada frequência e reconstrói o texto
        # a partir dos tokens restantes.        
        tokens = remove_stopwords(tokens)
        processed_text = " ".join(tokens)
        applied_steps.append("remove_stopwords")

    if config.get("stemming"):
        # Reduz os tokens às respetivas formas radicais.        
        tokens = stem_tokens(tokens)
        processed_text = " ".join(tokens)
        applied_steps.append("stemming")

    if config.get("lemmatization"):
        # Converte os tokens para as respetivas formas canónicas ou lemas.        
        tokens = lemmatize_tokens(tokens)
        processed_text = " ".join(tokens)
        applied_steps.append("lemmatization")

    # Quando uma operação baseada em tokens reconstrói o texto, a junção dos
    # tokens já produz normalmente espaços simples. Caso apenas a tokenização
    # tenha sido selecionada, os tokens permanecem associados ao texto atual.
    if requires_tokens and not tokens:
        tokens = tokenize_text(processed_text)

    # Verifica se o conteúdo deixou de possuir informação textual depois das
    # operações selecionadas.
    is_empty_after_processing = processed_text.strip() == ""


    # -------------------------------------------------------------------------
    # Cálculo das métricas de transformação
    # -------------------------------------------------------------------------

    # O pipeline atual não contém uma operação que remova URLs.
    # Esta métrica permanece a zero até ser adicionada uma opção remove_urls.
    urls_removed_count = 0

    # Quando a substituição de URLs está ativa, considera-se que todos os URLs
    # identificados no texto original foram substituídos.
    urls_replaced_count = (
        original_social_markers["url_count"]
        if config.get("replace_urls")
        else 0
    )

    # Quando a anonimização está ativa, considera-se que todas as menções
    # identificadas foram transformadas num marcador anónimo.
    mentions_anonymized_count = (
        original_social_markers["mention_count"]
        if config.get("anonymize_mentions")
        else 0
    )

    # O pipeline atual normaliza hashtags, mas não possui uma operação que
    # remova completamente a hashtag e o respetivo conteúdo.
    hashtags_removed_count = 0

    # Volta a identificar os emojis no resultado final para determinar quantos
    # permaneceram efetivamente representados como emojis.
    processed_emojis = extract_emojis(processed_text)
    emojis_preserved_count = len(processed_emojis)

    return {
        # Conteúdo textual.
        "original_text": original_text,
        "processed_text": processed_text,

        # Elementos e estruturas extraídas.
        "tokens": tokens,
        "emojis": emojis,
        "hashtags": hashtags,
        "applied_steps": applied_steps,

        # Métricas de dimensão.
        "original_length": len(original_text),
        "processed_length": len(processed_text),
        "word_count": len(processed_text.split()),
        "token_count": len(tokens),

        # Quantidades encontradas no texto original.
        #
        # A quantidade de emojis é calculada mesmo quando extract_emojis
        # está desativado, para que a métrica não dependa da apresentação
        # da lista de emojis.
        "emoji_count": len(original_emojis),
        "hashtag_count": original_social_markers["hashtag_count"],
        "url_count": original_social_markers["url_count"],
        "mention_count": original_social_markers["mention_count"],

        # Indicadores de presença no texto original.
        "has_url": original_social_markers["has_url"],
        "has_mention": original_social_markers["has_mention"],
        "has_hashtag": original_social_markers["has_hashtag"],

        # Indicador de qualidade do resultado.
        "is_empty_after_processing": is_empty_after_processing,

        # Métricas das transformações efetivamente realizadas.
        "urls_removed_count": urls_removed_count,
        "urls_replaced_count": urls_replaced_count,
        "mentions_anonymized_count": mentions_anonymized_count,
        "hashtags_removed_count": hashtags_removed_count,
        "emojis_preserved_count": emojis_preserved_count
    }