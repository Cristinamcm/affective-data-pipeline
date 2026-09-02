"""
Pipeline configurável de pré-processamento textual.

Este módulo coordena as operações de preparação aplicadas aos conteúdos
provenientes de redes sociais ou de conjuntos de dados públicos.

O pipeline permite selecionar individualmente operações relacionadas com:

- extração de elementos;
- normalização textual;
- anonimização;
- tratamento de URLs, menções, hashtags e emojis;
- redução de ruído;
- tokenização;
- remoção de stopwords;
- stemming;
- lematização.

Para além do texto processado, são produzidas métricas sobre:

- os elementos encontrados;
- as transformações realizadas;
- as operações que modificaram efetivamente o texto;
- o tempo de execução de cada operação.
"""

from time import perf_counter
from typing import Any

from app.preprocessing.emoji_processing import (
    convert_emojis_to_text,
    extract_emojis
)

from app.preprocessing.presets import (
    normalize_config
)

from app.preprocessing.text_cleaning import (
    anonymize_mentions,
    count_control_characters,
    count_hashtags,
    count_mentions,
    count_repeated_character_sequences,
    count_selected_punctuation,
    count_urls,
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


def _elapsed_ms(
    start_time: float
) -> float:
    """
    Calcula o tempo decorrido em milissegundos.
    """

    return (
        perf_counter()
        - start_time
    ) * 1000


def _build_step_result(
    changed: bool,
    duration_ms: float,
    items_detected: int | None = None,
    items_transformed: int | None = None
) -> dict[str, Any]:
    """
    Cria a estrutura normalizada utilizada para descrever o resultado
    de uma operação do pipeline.
    """

    return {
        "changed": changed,
        "duration_ms": duration_ms,
        "items_detected": items_detected,
        "items_transformed": items_transformed
    }


def preprocess_text(
    text: str,
    config: dict | None = None
) -> dict[str, Any]:
    """
    Aplica uma configuração de pré-processamento a um texto.

    Args:
        text:
            Texto original.

        config:
            Operações selecionadas.

    Returns:
        dict[str, Any]:
            Resultado completo do processamento.
    """

    # -------------------------------------------------------------------------
    # Configuração
    # -------------------------------------------------------------------------

    config = normalize_config(
        config
    )

    if not isinstance(text, str):
        text = ""

    original_text = text

    # -------------------------------------------------------------------------
    # Métricas do conteúdo original
    # -------------------------------------------------------------------------

    original_social_markers = (
        detect_social_markers(
            original_text
        )
    )

    original_emojis = (
        extract_emojis(
            original_text
        )
    )

    # -------------------------------------------------------------------------
    # Estruturas de resultado
    # -------------------------------------------------------------------------

    processed_text = original_text

    emojis: list[str] = []
    hashtags: list[str] = []
    tokens: list[str] = []

    applied_steps: list[str] = []
    changed_steps: list[str] = []

    step_results: dict[
        str,
        dict[str, Any]
    ] = {}

    # =========================================================================
    # EXTRAÇÃO DE EMOJIS
    # =========================================================================

    if config["extract_emojis"]:

        start_time = perf_counter()

        emojis = extract_emojis(
            original_text
        )

        duration_ms = _elapsed_ms(
            start_time
        )

        applied_steps.append(
            "extract_emojis"
        )

        step_results[
            "extract_emojis"
        ] = _build_step_result(
            changed=False,
            duration_ms=duration_ms,
            items_detected=len(emojis),
            items_transformed=0
        )

    # =========================================================================
    # EXTRAÇÃO DE HASHTAGS
    # =========================================================================

    if config["extract_hashtags"]:

        start_time = perf_counter()

        hashtags = extract_hashtags(
            original_text
        )

        duration_ms = _elapsed_ms(
            start_time
        )

        applied_steps.append(
            "extract_hashtags"
        )

        step_results[
            "extract_hashtags"
        ] = _build_step_result(
            changed=False,
            duration_ms=duration_ms,
            items_detected=len(hashtags),
            items_transformed=0
        )

    # =========================================================================
    # NORMALIZAÇÃO UNICODE
    # =========================================================================

    if config["normalize_unicode"]:

        before = processed_text

        start_time = perf_counter()

        processed_text = normalize_unicode(
            processed_text
        )

        duration_ms = _elapsed_ms(
            start_time
        )

        changed = (
            before != processed_text
        )

        applied_steps.append(
            "normalize_unicode"
        )

        if changed:
            changed_steps.append(
                "normalize_unicode"
            )

        step_results[
            "normalize_unicode"
        ] = _build_step_result(
            changed=changed,
            duration_ms=duration_ms
        )

    # =========================================================================
    # MINÚSCULAS
    # =========================================================================

    if config["lowercase"]:

        before = processed_text

        start_time = perf_counter()

        processed_text = lowercase_text(
            processed_text
        )

        duration_ms = _elapsed_ms(
            start_time
        )

        changed = (
            before != processed_text
        )

        applied_steps.append(
            "lowercase"
        )

        if changed:
            changed_steps.append(
                "lowercase"
            )

        step_results[
            "lowercase"
        ] = _build_step_result(
            changed=changed,
            duration_ms=duration_ms
        )

    # =========================================================================
    # URLS
    # =========================================================================

    if config["replace_urls"]:

        before = processed_text

        urls_before = count_urls(
            before
        )

        start_time = perf_counter()

        processed_text = replace_urls(
            processed_text
        )

        duration_ms = _elapsed_ms(
            start_time
        )

        urls_after = count_urls(
            processed_text
        )

        urls_transformed = max(
            urls_before - urls_after,
            0
        )

        changed = (
            before != processed_text
        )

        applied_steps.append(
            "replace_urls"
        )

        if changed:
            changed_steps.append(
                "replace_urls"
            )

        step_results[
            "replace_urls"
        ] = _build_step_result(
            changed=changed,
            duration_ms=duration_ms,
            items_detected=urls_before,
            items_transformed=urls_transformed
        )

    # =========================================================================
    # MENÇÕES
    # =========================================================================

    if config["anonymize_mentions"]:

        before = processed_text

        mentions_before = count_mentions(
            before
        )

        start_time = perf_counter()

        processed_text = anonymize_mentions(
            processed_text
        )

        duration_ms = _elapsed_ms(
            start_time
        )

        mentions_after = count_mentions(
            processed_text
        )

        mentions_transformed = max(
            mentions_before
            - mentions_after,
            0
        )

        changed = (
            before != processed_text
        )

        applied_steps.append(
            "anonymize_mentions"
        )

        if changed:
            changed_steps.append(
                "anonymize_mentions"
            )

        step_results[
            "anonymize_mentions"
        ] = _build_step_result(
            changed=changed,
            duration_ms=duration_ms,
            items_detected=mentions_before,
            items_transformed=(
                mentions_transformed
            )
        )

    # =========================================================================
    # HASHTAGS
    # =========================================================================

    if config["normalize_hashtags"]:

        before = processed_text

        hashtags_before = count_hashtags(
            before
        )

        start_time = perf_counter()

        processed_text = normalize_hashtags(
            processed_text
        )

        duration_ms = _elapsed_ms(
            start_time
        )

        hashtags_after = count_hashtags(
            processed_text
        )

        hashtags_transformed = max(
            hashtags_before
            - hashtags_after,
            0
        )

        changed = (
            before != processed_text
        )

        applied_steps.append(
            "normalize_hashtags"
        )

        if changed:
            changed_steps.append(
                "normalize_hashtags"
            )

        step_results[
            "normalize_hashtags"
        ] = _build_step_result(
            changed=changed,
            duration_ms=duration_ms,
            items_detected=hashtags_before,
            items_transformed=(
                hashtags_transformed
            )
        )

    # =========================================================================
    # EMOJIS PARA TEXTO
    # =========================================================================

    if config["convert_emojis_to_text"]:

        before = processed_text

        emojis_before = extract_emojis(
            before
        )

        start_time = perf_counter()

        processed_text = (
            convert_emojis_to_text(
                processed_text
            )
        )

        duration_ms = _elapsed_ms(
            start_time
        )

        emojis_after = extract_emojis(
            processed_text
        )

        emojis_transformed = max(
            len(emojis_before)
            - len(emojis_after),
            0
        )

        changed = (
            before != processed_text
        )

        applied_steps.append(
            "convert_emojis_to_text"
        )

        if changed:
            changed_steps.append(
                "convert_emojis_to_text"
            )

        step_results[
            "convert_emojis_to_text"
        ] = _build_step_result(
            changed=changed,
            duration_ms=duration_ms,
            items_detected=len(
                emojis_before
            ),
            items_transformed=(
                emojis_transformed
            )
        )

    # =========================================================================
    # ABREVIAÇÕES
    # =========================================================================

    if config["expand_abbreviations"]:

        before = processed_text

        start_time = perf_counter()

        processed_text = (
            expand_abbreviations(
                processed_text
            )
        )

        duration_ms = _elapsed_ms(
            start_time
        )

        changed = (
            before != processed_text
        )

        applied_steps.append(
            "expand_abbreviations"
        )

        if changed:
            changed_steps.append(
                "expand_abbreviations"
            )

        step_results[
            "expand_abbreviations"
        ] = _build_step_result(
            changed=changed,
            duration_ms=duration_ms
        )

    # =========================================================================
    # CARACTERES REPETIDOS
    # =========================================================================

    if config[
        "reduce_repeated_characters"
    ]:

        before = processed_text

        repetitions_before = (
            count_repeated_character_sequences(
                before
            )
        )

        start_time = perf_counter()

        processed_text = (
            reduce_repeated_characters(
                processed_text
            )
        )

        duration_ms = _elapsed_ms(
            start_time
        )

        changed = (
            before != processed_text
        )

        applied_steps.append(
            "reduce_repeated_characters"
        )

        if changed:
            changed_steps.append(
                "reduce_repeated_characters"
            )

        step_results[
            "reduce_repeated_characters"
        ] = _build_step_result(
            changed=changed,
            duration_ms=duration_ms,
            items_detected=(
                repetitions_before
            ),
            items_transformed=(
                repetitions_before
                if changed
                else 0
            )
        )

    # =========================================================================
    # CARACTERES DE CONTROLO
    # =========================================================================

    if config[
        "remove_special_characters"
    ]:

        before = processed_text

        control_characters = (
            count_control_characters(
                before
            )
        )

        start_time = perf_counter()

        processed_text = (
            remove_special_characters(
                processed_text
            )
        )

        duration_ms = _elapsed_ms(
            start_time
        )

        changed = (
            before != processed_text
        )

        applied_steps.append(
            "remove_special_characters"
        )

        if changed:
            changed_steps.append(
                "remove_special_characters"
            )

        step_results[
            "remove_special_characters"
        ] = _build_step_result(
            changed=changed,
            duration_ms=duration_ms,
            items_detected=(
                control_characters
            ),
            items_transformed=(
                control_characters
                if changed
                else 0
            )
        )

    # =========================================================================
    # PONTUAÇÃO
    # =========================================================================

    if config[
        "remove_selected_punctuation"
    ]:

        before = processed_text

        punctuation_before = (
            count_selected_punctuation(
                before
            )
        )

        start_time = perf_counter()

        processed_text = (
            remove_selected_punctuation(
                processed_text
            )
        )

        duration_ms = _elapsed_ms(
            start_time
        )

        changed = (
            before != processed_text
        )

        applied_steps.append(
            "remove_selected_punctuation"
        )

        if changed:
            changed_steps.append(
                "remove_selected_punctuation"
            )

        step_results[
            "remove_selected_punctuation"
        ] = _build_step_result(
            changed=changed,
            duration_ms=duration_ms,
            items_detected=(
                punctuation_before
            ),
            items_transformed=(
                punctuation_before
                if changed
                else 0
            )
        )

    # =========================================================================
    # ESPAÇOS
    # =========================================================================

    if config["normalize_spaces"]:

        before = processed_text

        start_time = perf_counter()

        processed_text = (
            normalize_spaces(
                processed_text
            )
        )

        duration_ms = _elapsed_ms(
            start_time
        )

        changed = (
            before != processed_text
        )

        applied_steps.append(
            "normalize_spaces"
        )

        if changed:
            changed_steps.append(
                "normalize_spaces"
            )

        step_results[
            "normalize_spaces"
        ] = _build_step_result(
            changed=changed,
            duration_ms=duration_ms
        )

    # =========================================================================
    # TOKENIZAÇÃO
    # =========================================================================

    if config["tokenize"]:

        start_time = perf_counter()

        tokens = tokenize_text(
            processed_text
        )

        duration_ms = _elapsed_ms(
            start_time
        )

        applied_steps.append(
            "tokenize"
        )

        # A tokenização produz uma estrutura auxiliar, mas não altera
        # diretamente o texto.
        step_results[
            "tokenize"
        ] = _build_step_result(
            changed=False,
            duration_ms=duration_ms,
            items_detected=len(tokens),
            items_transformed=len(tokens)
        )

    # =========================================================================
    # STOPWORDS
    # =========================================================================

    if config["remove_stopwords"]:

        before_text = processed_text
        before_tokens = tokens.copy()

        start_time = perf_counter()

        tokens = remove_stopwords(
            tokens
        )

        processed_text = " ".join(
            tokens
        )

        duration_ms = _elapsed_ms(
            start_time
        )

        removed_count = max(
            len(before_tokens)
            - len(tokens),
            0
        )

        changed = (
            before_text != processed_text
        )

        applied_steps.append(
            "remove_stopwords"
        )

        if changed:
            changed_steps.append(
                "remove_stopwords"
            )

        step_results[
            "remove_stopwords"
        ] = _build_step_result(
            changed=changed,
            duration_ms=duration_ms,
            items_detected=len(
                before_tokens
            ),
            items_transformed=(
                removed_count
            )
        )

    # =========================================================================
    # STEMMING
    # =========================================================================

    if config["stemming"]:

        before_text = processed_text
        before_tokens = tokens.copy()

        start_time = perf_counter()

        tokens = stem_tokens(
            tokens
        )

        processed_text = " ".join(
            tokens
        )

        duration_ms = _elapsed_ms(
            start_time
        )

        changed_token_count = sum(
            1
            for before_token, after_token
            in zip(
                before_tokens,
                tokens
            )
            if before_token != after_token
        )

        changed = (
            before_text != processed_text
        )

        applied_steps.append(
            "stemming"
        )

        if changed:
            changed_steps.append(
                "stemming"
            )

        step_results[
            "stemming"
        ] = _build_step_result(
            changed=changed,
            duration_ms=duration_ms,
            items_detected=len(
                before_tokens
            ),
            items_transformed=(
                changed_token_count
            )
        )

    # =========================================================================
    # LEMATIZAÇÃO
    # =========================================================================

    if config["lemmatization"]:

        before_text = processed_text
        before_tokens = tokens.copy()

        start_time = perf_counter()

        tokens = lemmatize_tokens(
            tokens
        )

        processed_text = " ".join(
            tokens
        )

        duration_ms = _elapsed_ms(
            start_time
        )

        changed_token_count = sum(
            1
            for before_token, after_token
            in zip(
                before_tokens,
                tokens
            )
            if before_token != after_token
        )

        changed = (
            before_text != processed_text
        )

        applied_steps.append(
            "lemmatization"
        )

        if changed:
            changed_steps.append(
                "lemmatization"
            )

        step_results[
            "lemmatization"
        ] = _build_step_result(
            changed=changed,
            duration_ms=duration_ms,
            items_detected=len(
                before_tokens
            ),
            items_transformed=(
                changed_token_count
            )
        )

    # =========================================================================
    # MÉTRICAS FINAIS
    # =========================================================================

    is_empty_after_processing = (
        processed_text.strip() == ""
    )

    processed_emojis = (
        extract_emojis(
            processed_text
        )
    )

    urls_replaced_count = (
        step_results
        .get(
            "replace_urls",
            {}
        )
        .get(
            "items_transformed",
            0
        )
        or 0
    )

    mentions_anonymized_count = (
        step_results
        .get(
            "anonymize_mentions",
            {}
        )
        .get(
            "items_transformed",
            0
        )
        or 0
    )

    hashtags_normalized_count = (
        step_results
        .get(
            "normalize_hashtags",
            {}
        )
        .get(
            "items_transformed",
            0
        )
        or 0
    )

    emojis_converted_count = (
        step_results
        .get(
            "convert_emojis_to_text",
            {}
        )
        .get(
            "items_transformed",
            0
        )
        or 0
    )

    repeated_characters_reduced_count = (
        step_results
        .get(
            "reduce_repeated_characters",
            {}
        )
        .get(
            "items_transformed",
            0
        )
        or 0
    )

    # =========================================================================
    # RESULTADO
    # =========================================================================

    return {
        # ---------------------------------------------------------------------
        # Texto
        # ---------------------------------------------------------------------

        "original_text": original_text,
        "processed_text": processed_text,

        # ---------------------------------------------------------------------
        # Estruturas
        # ---------------------------------------------------------------------

        "tokens": tokens,
        "emojis": emojis,
        "hashtags": hashtags,

        # ---------------------------------------------------------------------
        # Etapas
        # ---------------------------------------------------------------------

        "applied_steps": (
            applied_steps
        ),

        "changed_steps": (
            changed_steps
        ),

        "step_results": (
            step_results
        ),

        # ---------------------------------------------------------------------
        # Dimensão
        # ---------------------------------------------------------------------

        "original_length": len(
            original_text
        ),

        "processed_length": len(
            processed_text
        ),

        "original_word_count": len(
            original_text.split()
        ),

        "processed_word_count": len(
            processed_text.split()
        ),

        # Mantido temporariamente por compatibilidade.
        "word_count": len(
            processed_text.split()
        ),

        "token_count": len(
            tokens
        ),

        # ---------------------------------------------------------------------
        # Conteúdo original
        # ---------------------------------------------------------------------

        "emoji_count": len(
            original_emojis
        ),

        "hashtag_count": (
            original_social_markers[
                "hashtag_count"
            ]
        ),

        "url_count": (
            original_social_markers[
                "url_count"
            ]
        ),

        "mention_count": (
            original_social_markers[
                "mention_count"
            ]
        ),

        "has_url": (
            original_social_markers[
                "has_url"
            ]
        ),

        "has_mention": (
            original_social_markers[
                "has_mention"
            ]
        ),

        "has_hashtag": (
            original_social_markers[
                "has_hashtag"
            ]
        ),

        # ---------------------------------------------------------------------
        # Qualidade
        # ---------------------------------------------------------------------

        "is_empty_after_processing": (
            is_empty_after_processing
        ),

        # ---------------------------------------------------------------------
        # Transformações
        # ---------------------------------------------------------------------

        "urls_removed_count": 0,

        "urls_replaced_count": (
            urls_replaced_count
        ),

        "mentions_anonymized_count": (
            mentions_anonymized_count
        ),

        "hashtags_removed_count": 0,

        "hashtags_normalized_count": (
            hashtags_normalized_count
        ),

        "emojis_converted_count": (
            emojis_converted_count
        ),

        "emojis_preserved_count": len(
            processed_emojis
        ),

        "repeated_characters_reduced_count": (
            repeated_characters_reduced_count
        )
    }