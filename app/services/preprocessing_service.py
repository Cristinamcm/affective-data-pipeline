"""
Serviço responsável por coordenar o pré-processamento dos conjuntos de dados.

Este módulo implementa a lógica aplicacional necessária para:

1. validar a existência do conjunto de dados;
2. normalizar a configuração escolhida pelo utilizador;
3. obter os registos originais;
4. criar o registo da execução de processamento;
5. criar as etapas de processamento selecionadas;
6. identificar registos duplicados;
7. aplicar o pipeline a cada registo;
8. guardar os resultados processados;
9. recolher métricas sobre cada etapa;
10. calcular e guardar métricas agregadas;
11. finalizar a execução com sucesso ou erro.

A camada de serviço coordena os diferentes componentes do sistema,
mantendo separadas:

- a lógica de transformação textual;
- a lógica de acesso à base de dados;
- a recolha das métricas de execução.
"""

from time import perf_counter

from sqlalchemy.orm import Session

from app.preprocessing.preprocessing_pipeline import preprocess_text
from app.preprocessing.presets import (
    PIPELINE_OPERATION_ORDER,
    normalize_config
)
from app.repositories.dataset_repository import get_dataset_by_id
from app.repositories.preprocessing_repository import (
    create_processing_run,
    create_processing_step,
    finish_processing_run,
    finish_processing_step,
    get_all_posts_by_dataset,
    save_pipeline_metric,
    save_processed_post
)


# Versão atual do pipeline.
#
# Este valor é guardado em cada execução para permitir identificar
# posteriormente qual a versão do processamento que produziu os resultados.
PIPELINE_VERSION = "1.0"


def _to_int(value) -> int:
    """
    Converte um valor numérico para inteiro.

    Quando o valor recebido é nulo ou não pode ser convertido, é devolvido
    zero.

    Args:
        value: Valor que será convertido.

    Returns:
        int: Valor convertido ou zero.
    """

    try:
        return int(value or 0)

    except (TypeError, ValueError):
        return 0


def _to_float(value) -> float:
    """
    Converte um valor numérico para float.

    Quando o valor recebido é nulo ou inválido, é devolvido zero.

    Args:
        value: Valor que será convertido.

    Returns:
        float: Valor convertido ou zero.
    """

    try:
        return float(value or 0.0)

    except (TypeError, ValueError):
        return 0.0


def _calculate_ratio(
    numerator: int,
    denominator: int
) -> float:
    """
    Calcula uma proporção evitando divisão por zero.

    Args:
        numerator:
            Número de ocorrências que satisfazem a condição.

        denominator:
            Número total de elementos considerados.

    Returns:
        float:
            Proporção entre 0 e 1. Quando o denominador é zero,
            é devolvido 0.0.
    """

    if denominator <= 0:
        return 0.0

    return numerator / denominator


def preprocess_dataset(
    db: Session,
    dataset_id: int,
    configuration_name: str,
    config: dict[str, bool]
):
    """
    Executa o pipeline configurável de pré-processamento sobre um conjunto
    de dados.

    O processamento é realizado sobre os registos originais, preservando-os
    na base de dados. Os resultados são armazenados separadamente e associados
    à execução responsável pela sua criação.

    Para além dos resultados processados, são registadas:

    - as operações executadas;
    - a ordem das operações;
    - o número de registos alterados por cada operação;
    - o tempo consumido por cada etapa;
    - métricas agregadas sobre a execução.

    Args:
        db:
            Sessão SQLAlchemy utilizada para comunicar com a base de dados.

        dataset_id:
            Identificador do conjunto de dados a processar.

        configuration_name:
            Nome atribuído à configuração.

        config:
            Operações selecionadas pelo utilizador.

    Returns:
        dict:
            Resumo da execução concluída.

    Raises:
        ValueError:
            Quando o conjunto de dados não existe ou quando a configuração
            é inválida.

        Exception:
            Quando ocorre um erro durante o processamento.
    """

    # =========================================================================
    # 1. VALIDAR O CONJUNTO DE DADOS
    # =========================================================================

    dataset = get_dataset_by_id(
        db=db,
        dataset_id=dataset_id
    )

    if dataset is None:
        raise ValueError(
            "Conjunto de dados não encontrado."
        )

    # =========================================================================
    # 2. NORMALIZAR A CONFIGURAÇÃO
    # =========================================================================

    # A normalização:
    #
    # - adiciona todas as operações suportadas;
    # - converte os valores para booleanos;
    # - resolve dependências entre operações;
    # - valida incompatibilidades.
    normalized_config = normalize_config(
        config
    )

    # =========================================================================
    # 3. OBTER OS REGISTOS ORIGINAIS
    # =========================================================================

    posts = get_all_posts_by_dataset(
        db=db,
        dataset_id=dataset_id
    )

    # =========================================================================
    # 4. CRIAR A EXECUÇÃO
    # =========================================================================

    run = create_processing_run(
        db=db,
        dataset_id=dataset_id,
        configuration_name=configuration_name,
        configuration_json=normalized_config,
        total_posts=len(posts),
        pipeline_version=PIPELINE_VERSION
    )

    # =========================================================================
    # 5. DETERMINAR AS OPERAÇÕES SELECIONADAS
    # =========================================================================

    # A utilização de PIPELINE_OPERATION_ORDER garante que a ordem registada
    # na base de dados corresponde exatamente à ordem definida para o pipeline.
    selected_operations = [
        operation_name
        for operation_name in PIPELINE_OPERATION_ORDER
        if normalized_config.get(
            operation_name,
            False
        )
    ]

    # Dicionário que relaciona o nome da operação com o respetivo
    # ProcessingStep criado na base de dados.
    processing_steps = {}

    for step_order, operation_name in enumerate(
        selected_operations,
        start=1
    ):

        step = create_processing_step(
            db=db,
            processing_run_id=run.id,
            step_name=operation_name,
            step_order=step_order
        )

        processing_steps[
            operation_name
        ] = step

    # =========================================================================
    # 6. ESTRUTURAS AUXILIARES
    # =========================================================================

    # Guarda versões normalizadas dos textos já encontrados para permitir
    # identificar duplicados durante a execução atual.
    seen_texts = set()

    # -------------------------------------------------------------------------
    # Contadores gerais
    # -------------------------------------------------------------------------

    duplicate_posts = 0
    empty_after_processing = 0

    processed_posts_count = 0
    failed_posts_count = 0

    changed_posts_count = 0

    # -------------------------------------------------------------------------
    # Dimensão dos textos
    # -------------------------------------------------------------------------

    total_original_length = 0
    total_processed_length = 0

    # -------------------------------------------------------------------------
    # Elementos encontrados nos textos originais
    # -------------------------------------------------------------------------

    urls_found = 0
    mentions_found = 0
    hashtags_found = 0
    emojis_found = 0

    # -------------------------------------------------------------------------
    # Transformações realizadas
    # -------------------------------------------------------------------------

    urls_replaced = 0
    mentions_anonymized = 0
    hashtags_normalized = 0
    emojis_converted = 0

    repeated_sequences_reduced = 0

    emojis_preserved = 0

    # -------------------------------------------------------------------------
    # Métricas específicas de cada etapa
    # -------------------------------------------------------------------------

    # Número de registos cujo conteúdo foi efetivamente alterado
    # por cada operação.
    step_changed_counts = {
        operation_name: 0
        for operation_name in selected_operations
    }

    # Tempo total consumido por cada operação ao longo de todos os registos.
    step_duration_totals = {
        operation_name: 0.0
        for operation_name in selected_operations
    }

    # Número total de elementos encontrados por cada etapa.
    #
    # Por exemplo:
    #
    # replace_urls:
    #     items_detected = número de URLs encontrados.
    step_items_detected = {
        operation_name: 0
        for operation_name in selected_operations
    }

    # Número total de elementos efetivamente transformados.
    step_items_transformed = {
        operation_name: 0
        for operation_name in selected_operations
    }

    # Marca o início da execução global.
    run_start = perf_counter()

    try:

        # =====================================================================
        # 7. PROCESSAR CADA REGISTO
        # =====================================================================

        for post in posts:

            try:

                # =============================================================
                # 7.1. DETEÇÃO DE DUPLICADOS
                # =============================================================

                # Produz uma representação mínima normalizada para comparação.
                original_normalized = (
                    post.original_text
                    .strip()
                    .lower()
                )

                # Quando a normalização de espaços está selecionada, esta
                # normalização é também utilizada na deteção de duplicados.
                if normalized_config.get(
                    "normalize_spaces"
                ):

                    original_normalized = " ".join(
                        original_normalized.split()
                    )

                is_duplicate = False

                if original_normalized in seen_texts:

                    is_duplicate = True

                    duplicate_posts += 1

                else:

                    seen_texts.add(
                        original_normalized
                    )

                # =============================================================
                # 7.2. EXECUTAR O PIPELINE
                # =============================================================

                processed_data = preprocess_text(
                    text=post.original_text,
                    config=normalized_config
                )

                processed_text = str(
                    processed_data.get(
                        "processed_text",
                        ""
                    )
                )

                # =============================================================
                # 7.3. MÉTRICAS GERAIS DE QUALIDADE
                # =============================================================

                is_empty = processed_data.get(
                    "is_empty_after_processing",
                    not bool(
                        processed_text.strip()
                    )
                )

                if is_empty:
                    empty_after_processing += 1

                # Determina se, considerando todo o pipeline, o texto final
                # ficou diferente do texto original.
                if processed_text != post.original_text:
                    changed_posts_count += 1

                # =============================================================
                # 7.4. MÉTRICAS DE DIMENSÃO
                # =============================================================

                total_original_length += _to_int(
                    processed_data.get(
                        "original_length",
                        len(post.original_text)
                    )
                )

                total_processed_length += _to_int(
                    processed_data.get(
                        "processed_length",
                        len(processed_text)
                    )
                )

                # =============================================================
                # 7.5. ELEMENTOS IDENTIFICADOS NO TEXTO ORIGINAL
                # =============================================================

                urls_found += _to_int(
                    processed_data.get(
                        "url_count"
                    )
                )

                mentions_found += _to_int(
                    processed_data.get(
                        "mention_count"
                    )
                )

                hashtags_found += _to_int(
                    processed_data.get(
                        "hashtag_count"
                    )
                )

                emojis_found += _to_int(
                    processed_data.get(
                        "emoji_count"
                    )
                )

                # =============================================================
                # 7.6. TRANSFORMAÇÕES REALIZADAS
                # =============================================================

                urls_replaced += _to_int(
                    processed_data.get(
                        "urls_replaced_count"
                    )
                )

                mentions_anonymized += _to_int(
                    processed_data.get(
                        "mentions_anonymized_count"
                    )
                )

                hashtags_normalized += _to_int(
                    processed_data.get(
                        "hashtags_normalized_count"
                    )
                )

                emojis_converted += _to_int(
                    processed_data.get(
                        "emojis_converted_count"
                    )
                )

                repeated_sequences_reduced += _to_int(
                    processed_data.get(
                        "repeated_characters_reduced_count"
                    )
                )

                emojis_preserved += _to_int(
                    processed_data.get(
                        "emojis_preserved_count"
                    )
                )

                # =============================================================
                # 7.7. MÉTRICAS DAS ETAPAS
                # =============================================================

                # O novo pipeline devolve para cada operação:
                #
                # {
                #     "changed": True/False,
                #     "duration_ms": ...,
                #     "items_detected": ...,
                #     "items_transformed": ...
                # }
                #
                # Desta forma, não confundimos "operação executada" com
                # "operação que realmente alterou o registo".
                step_results = processed_data.get(
                    "step_results",
                    {}
                )

                for (
                    step_name,
                    step_result
                ) in step_results.items():

                    # Ignora qualquer resultado de uma etapa que não pertença
                    # à configuração efetivamente selecionada.
                    if (
                        step_name
                        not in step_changed_counts
                    ):
                        continue

                    # ---------------------------------------------------------
                    # Registos alterados
                    # ---------------------------------------------------------

                    if step_result.get(
                        "changed",
                        False
                    ):

                        step_changed_counts[
                            step_name
                        ] += 1

                    # ---------------------------------------------------------
                    # Tempo da etapa
                    # ---------------------------------------------------------

                    step_duration_totals[
                        step_name
                    ] += _to_float(
                        step_result.get(
                            "duration_ms"
                        )
                    )

                    # ---------------------------------------------------------
                    # Elementos encontrados
                    # ---------------------------------------------------------

                    items_detected = (
                        step_result.get(
                            "items_detected"
                        )
                    )

                    if items_detected is not None:

                        step_items_detected[
                            step_name
                        ] += _to_int(
                            items_detected
                        )

                    # ---------------------------------------------------------
                    # Elementos transformados
                    # ---------------------------------------------------------

                    items_transformed = (
                        step_result.get(
                            "items_transformed"
                        )
                    )

                    if (
                        items_transformed
                        is not None
                    ):

                        step_items_transformed[
                            step_name
                        ] += _to_int(
                            items_transformed
                        )

                # =============================================================
                # 7.8. GUARDAR O RESULTADO PROCESSADO
                # =============================================================

                save_processed_post(
                    db=db,
                    post=post,
                    run=run,
                    processed_data=processed_data,
                    is_duplicate=is_duplicate
                )

                processed_posts_count += 1

            except Exception:

                # Regista a ocorrência de um erro durante o processamento
                # do registo atual.
                failed_posts_count += 1

                # O comportamento atual interrompe a execução ao primeiro erro.
                # Futuramente poderá ser implementado processamento tolerante
                # a falhas com registo individual na tabela erros_processamento.
                raise

        # =====================================================================
        # 8. CALCULAR TEMPO TOTAL
        # =====================================================================

        duration_seconds = (
            perf_counter()
            - run_start
        )

        duration_ms = int(
            duration_seconds
            * 1000
        )

        # =====================================================================
        # 9. FINALIZAR AS ETAPAS
        # =====================================================================

        for (
            operation_name,
            step
        ) in processing_steps.items():

            finish_processing_step(
                db=db,
                step=step,

                # Numa execução concluída com sucesso, todas as etapas
                # receberam todos os registos processados.
                rows_received=processed_posts_count,

                # Número real de registos cujo conteúdo foi modificado
                # pela operação.
                rows_changed=(
                    step_changed_counts.get(
                        operation_name,
                        0
                    )
                ),

                rows_failed=0,

                # Soma do tempo consumido pela mesma operação em todos
                # os registos.
                duration_ms=int(
                    round(
                        step_duration_totals.get(
                            operation_name,
                            0.0
                        )
                    )
                ),

                status="completed"
            )

        # =====================================================================
        # 10. GUARDAR MÉTRICAS GERAIS
        # =====================================================================

        # ---------------------------------------------------------------------
        # Proporção de textos alterados
        # ---------------------------------------------------------------------

        save_pipeline_metric(
            db=db,
            processing_run_id=run.id,

            metric_name=(
                "proportion_changed_texts"
            ),

            metric_value=_calculate_ratio(
                changed_posts_count,
                processed_posts_count
            ),

            numerator=changed_posts_count,
            denominator=processed_posts_count,

            unit="proportion",

            description=(
                "Proporção de registos cujo texto final ficou "
                "diferente do texto original."
            )
        )

        # ---------------------------------------------------------------------
        # Proporção de textos vazios
        # ---------------------------------------------------------------------

        save_pipeline_metric(
            db=db,
            processing_run_id=run.id,

            metric_name=(
                "proportion_empty_texts"
            ),

            metric_value=_calculate_ratio(
                empty_after_processing,
                processed_posts_count
            ),

            numerator=empty_after_processing,
            denominator=processed_posts_count,

            unit="proportion",

            description=(
                "Proporção de registos cujo texto ficou vazio "
                "após o pré-processamento."
            )
        )

        # ---------------------------------------------------------------------
        # Proporção de duplicados
        # ---------------------------------------------------------------------

        save_pipeline_metric(
            db=db,
            processing_run_id=run.id,

            metric_name=(
                "proportion_duplicate_records"
            ),

            metric_value=_calculate_ratio(
                duplicate_posts,
                processed_posts_count
            ),

            numerator=duplicate_posts,
            denominator=processed_posts_count,

            unit="proportion",

            description=(
                "Proporção de registos identificados como duplicados."
            )
        )

        # ---------------------------------------------------------------------
        # Proporção de erros
        # ---------------------------------------------------------------------

        save_pipeline_metric(
            db=db,
            processing_run_id=run.id,

            metric_name=(
                "proportion_failed_records"
            ),

            metric_value=_calculate_ratio(
                failed_posts_count,
                len(posts)
            ),

            numerator=failed_posts_count,
            denominator=len(posts),

            unit="proportion",

            description=(
                "Proporção de registos em que ocorreu erro durante "
                "o processamento."
            )
        )

        # ---------------------------------------------------------------------
        # Variação média do comprimento
        # ---------------------------------------------------------------------

        average_length_change = 0.0

        if processed_posts_count > 0:

            average_length_change = (
                (
                    total_processed_length
                    - total_original_length
                )
                / processed_posts_count
            )

        save_pipeline_metric(
            db=db,
            processing_run_id=run.id,

            metric_name=(
                "average_length_change"
            ),

            metric_value=(
                average_length_change
            ),

            unit="characters",

            description=(
                "Variação média do número de caracteres entre "
                "o texto original e o texto processado."
            )
        )

        # ---------------------------------------------------------------------
        # Tempo total
        # ---------------------------------------------------------------------

        save_pipeline_metric(
            db=db,
            processing_run_id=run.id,

            metric_name=(
                "processing_time_ms"
            ),

            metric_value=float(
                duration_ms
            ),

            unit="ms",

            description=(
                "Duração total do processamento em milissegundos."
            )
        )

        # ---------------------------------------------------------------------
        # Throughput
        # ---------------------------------------------------------------------

        throughput = 0.0

        if duration_seconds > 0:

            throughput = (
                processed_posts_count
                / duration_seconds
            )

        save_pipeline_metric(
            db=db,
            processing_run_id=run.id,

            metric_name="throughput",

            metric_value=throughput,

            unit="records_per_second",

            description=(
                "Número médio de registos processados por segundo."
            )
        )

        # =====================================================================
        # 11. MÉTRICAS ESPECÍFICAS DAS TRANSFORMAÇÕES
        # =====================================================================

        # As métricas seguintes só são criadas quando a respetiva operação
        # foi efetivamente selecionada pelo utilizador.

        # ---------------------------------------------------------------------
        # URLs substituídos
        # ---------------------------------------------------------------------

        if normalized_config.get(
            "replace_urls"
        ):

            save_pipeline_metric(
                db=db,
                processing_run_id=run.id,

                metric_name=(
                    "proportion_urls_replaced"
                ),

                metric_value=_calculate_ratio(
                    urls_replaced,
                    urls_found
                ),

                numerator=urls_replaced,
                denominator=urls_found,

                unit="proportion",

                description=(
                    "Proporção de URLs substituídos relativamente "
                    "aos URLs identificados."
                )
            )

        # ---------------------------------------------------------------------
        # Menções anonimizadas
        # ---------------------------------------------------------------------

        if normalized_config.get(
            "anonymize_mentions"
        ):

            save_pipeline_metric(
                db=db,
                processing_run_id=run.id,

                metric_name=(
                    "proportion_mentions_anonymized"
                ),

                metric_value=_calculate_ratio(
                    mentions_anonymized,
                    mentions_found
                ),

                numerator=mentions_anonymized,
                denominator=mentions_found,

                unit="proportion",

                description=(
                    "Proporção de menções anonimizadas relativamente "
                    "às menções identificadas."
                )
            )

        # ---------------------------------------------------------------------
        # Hashtags normalizadas
        # ---------------------------------------------------------------------

        if normalized_config.get(
            "normalize_hashtags"
        ):

            save_pipeline_metric(
                db=db,
                processing_run_id=run.id,

                metric_name=(
                    "proportion_hashtags_normalized"
                ),

                metric_value=_calculate_ratio(
                    hashtags_normalized,
                    hashtags_found
                ),

                numerator=hashtags_normalized,
                denominator=hashtags_found,

                unit="proportion",

                description=(
                    "Proporção de hashtags normalizadas relativamente "
                    "às hashtags identificadas."
                )
            )

        # ---------------------------------------------------------------------
        # Emojis convertidos para texto
        # ---------------------------------------------------------------------

        if normalized_config.get(
            "convert_emojis_to_text"
        ):

            save_pipeline_metric(
                db=db,
                processing_run_id=run.id,

                metric_name=(
                    "proportion_emojis_converted"
                ),

                metric_value=_calculate_ratio(
                    emojis_converted,
                    emojis_found
                ),

                numerator=emojis_converted,
                denominator=emojis_found,

                unit="proportion",

                description=(
                    "Proporção de emojis convertidos para representação "
                    "textual relativamente aos emojis identificados."
                )
            )

        # ---------------------------------------------------------------------
        # Sequências de caracteres repetidos reduzidas
        # ---------------------------------------------------------------------

        if normalized_config.get(
            "reduce_repeated_characters"
        ):

            repeated_sequences_detected = (
                step_items_detected.get(
                    "reduce_repeated_characters",
                    0
                )
            )

            save_pipeline_metric(
                db=db,
                processing_run_id=run.id,

                metric_name=(
                    "proportion_repeated_sequences_reduced"
                ),

                metric_value=_calculate_ratio(
                    repeated_sequences_reduced,
                    repeated_sequences_detected
                ),

                numerator=(
                    repeated_sequences_reduced
                ),

                denominator=(
                    repeated_sequences_detected
                ),

                unit="proportion",

                description=(
                    "Proporção de sequências de caracteres repetidos "
                    "reduzidas relativamente às sequências identificadas."
                )
            )

        # ---------------------------------------------------------------------
        # Preservação de emojis
        # ---------------------------------------------------------------------

        # Esta métrica é relevante quando os emojis não foram intencionalmente
        # convertidos para texto. Permite verificar se outras operações do
        # pipeline provocaram a perda destes elementos afetivos.
        if (
            not normalized_config.get(
                "convert_emojis_to_text"
            )
            and emojis_found > 0
        ):

            save_pipeline_metric(
                db=db,
                processing_run_id=run.id,

                metric_name=(
                    "proportion_emojis_preserved"
                ),

                metric_value=_calculate_ratio(
                    emojis_preserved,
                    emojis_found
                ),

                numerator=emojis_preserved,
                denominator=emojis_found,

                unit="proportion",

                description=(
                    "Proporção de emojis preservados no texto final "
                    "relativamente aos emojis existentes no texto original."
                )
            )

        # =====================================================================
        # 12. FINALIZAR A EXECUÇÃO
        # =====================================================================

        finish_processing_run(
            db=db,
            run=run,

            processed_posts_count=(
                processed_posts_count
            ),

            failed_posts_count=(
                failed_posts_count
            ),

            duplicate_posts=(
                duplicate_posts
            ),

            empty_after_processing=(
                empty_after_processing
            ),

            duration_ms=(
                duration_ms
            ),

            status="completed"
        )

        # =====================================================================
        # 13. DEVOLVER RESUMO
        # =====================================================================

        return {
            "processing_run_id": run.id,

            "dataset_id": dataset_id,

            "configuration_name": (
                configuration_name
            ),

            "pipeline_version": (
                PIPELINE_VERSION
            ),

            "total_posts": len(posts),

            "processed_posts": (
                processed_posts_count
            ),

            "failed_posts": (
                failed_posts_count
            ),

            "duplicate_posts": (
                duplicate_posts
            ),

            "empty_after_processing": (
                empty_after_processing
            ),

            "duration_ms": (
                duration_ms
            ),

            "status": "completed"
        }

    except Exception as error:

        # =====================================================================
        # 14. TRATAMENTO DE ERRO
        # =====================================================================

        duration_ms = int(
            (
                perf_counter()
                - run_start
            )
            * 1000
        )

        # Marca as etapas ainda não concluídas como falhadas.
        #
        # O número de registos recebidos corresponde aos registos concluídos
        # acrescidos do registo onde ocorreu o erro.
        for (
            operation_name,
            step
        ) in processing_steps.items():

            if step.status == "completed":
                continue

            finish_processing_step(
                db=db,
                step=step,

                rows_received=(
                    processed_posts_count
                    + failed_posts_count
                ),

                rows_changed=(
                    step_changed_counts.get(
                        operation_name,
                        0
                    )
                ),

                rows_failed=(
                    failed_posts_count
                ),

                duration_ms=int(
                    round(
                        step_duration_totals.get(
                            operation_name,
                            0.0
                        )
                    )
                ),

                status="failed"
            )

        # Atualiza a execução principal.
        finish_processing_run(
            db=db,
            run=run,

            processed_posts_count=(
                processed_posts_count
            ),

            failed_posts_count=(
                failed_posts_count
            ),

            duplicate_posts=(
                duplicate_posts
            ),

            empty_after_processing=(
                empty_after_processing
            ),

            duration_ms=(
                duration_ms
            ),

            status="failed",

            error_message=str(
                error
            )
        )

        # Propaga a exceção para que a camada da API devolva a resposta
        # HTTP adequada.
        raise