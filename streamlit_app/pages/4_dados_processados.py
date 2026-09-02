"""
Página de consulta dos dados processados e métricas.

Esta página permite ao utilizador:

1. selecionar um conjunto de dados;
2. consultar o histórico das execuções de pré-processamento;
3. selecionar uma execução específica;
4. visualizar a configuração aplicada;
5. consultar as métricas de qualidade;
6. consultar as métricas das transformações;
7. analisar o desempenho do processamento;
8. visualizar as etapas efetivamente executadas;
9. comparar os textos originais com os textos processados;
10. descarregar os resultados apresentados em formato CSV.

Os dados apresentados são obtidos através da API FastAPI.
"""

import math
import os

import pandas as pd
import requests
import streamlit as st


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000"
)


# =============================================================================
# EXCEÇÕES
# =============================================================================

class ApiRequestError(RuntimeError):
    """
    Representa um erro devolvido pela API FastAPI.
    """


# =============================================================================
# FUNÇÕES DE COMUNICAÇÃO COM A API
# =============================================================================

def get_error_detail(
    response: requests.Response
) -> str:
    """
    Obtém o detalhe de erro devolvido pelo backend.
    """

    try:

        response_data = response.json()

        return str(
            response_data.get(
                "detail",
                response_data
            )
        )

    except ValueError:

        return response.text


def get_json(
    endpoint: str,
    params: dict | None = None,
    timeout: int = 30
):
    """
    Executa um pedido GET à API e devolve o respetivo conteúdo JSON.
    """

    response = requests.get(
        f"{API_BASE_URL}{endpoint}",
        params=params,
        timeout=timeout
    )

    if response.status_code != 200:

        raise ApiRequestError(
            get_error_detail(
                response
            )
        )

    return response.json()


def get_datasets() -> list[dict]:
    """
    Obtém os conjuntos de dados registados.
    """

    return get_json(
        "/datasets"
    )


def get_presets() -> dict:
    """
    Obtém as designações das operações suportadas.

    Nesta página são utilizadas para traduzir os identificadores internos
    das etapas para designações compreensíveis pelo utilizador.
    """

    return get_json(
        "/preprocessing/presets"
    )


def get_processing_runs(
    dataset_id: int
) -> list[dict]:
    """
    Obtém o histórico de execuções de um conjunto de dados.
    """

    return get_json(
        (
            f"/preprocessing/datasets/"
            f"{dataset_id}/runs"
        )
    )


def get_run_summary(
    processing_run_id: int
) -> dict:
    """
    Obtém o resumo de uma execução.
    """

    return get_json(
        (
            f"/preprocessing/runs/"
            f"{processing_run_id}/summary"
        )
    )


def get_processing_steps(
    processing_run_id: int
) -> list[dict]:
    """
    Obtém as etapas associadas a uma execução.
    """

    return get_json(
        (
            f"/preprocessing/runs/"
            f"{processing_run_id}/steps"
        )
    )


def get_processed_posts(
    processing_run_id: int,
    limit: int,
    offset: int
) -> list[dict]:
    """
    Obtém uma página dos resultados processados.
    """

    return get_json(
        (
            f"/preprocessing/runs/"
            f"{processing_run_id}/posts"
        ),
        params={
            "limit": limit,
            "offset": offset
        }
    )


# =============================================================================
# FUNÇÕES DE FORMATAÇÃO
# =============================================================================

def format_percentage(
    value
) -> str:
    """
    Converte uma proporção entre 0 e 1 numa percentagem.
    """

    try:

        return (
            f"{float(value) * 100:.2f}%"
        )

    except (
        TypeError,
        ValueError
    ):

        return "—"


def format_number(
    value,
    decimals: int = 2
) -> str:
    """
    Formata um valor numérico.
    """

    try:

        return (
            f"{float(value):,.{decimals}f}"
        )

    except (
        TypeError,
        ValueError
    ):

        return "—"


def format_duration(
    duration_ms
) -> str:
    """
    Formata uma duração em milissegundos.
    """

    try:

        duration_ms = float(
            duration_ms
        )

    except (
        TypeError,
        ValueError
    ):

        return "—"


    if duration_ms >= 1000:

        return (
            f"{duration_ms / 1000:.2f} s"
        )


    return (
        f"{duration_ms:.0f} ms"
    )


def get_metric(
    metrics: dict,
    metric_name: str
) -> dict | None:
    """
    Obtém uma métrica através do respetivo identificador.
    """

    metric = metrics.get(
        metric_name
    )

    if not isinstance(
        metric,
        dict
    ):

        return None

    return metric


# =============================================================================
# INTERFACE
# =============================================================================

st.title(
    "Dados Processados e Métricas"
)

st.markdown(
    """
    Nesta página é possível consultar os resultados produzidos pelo pipeline
    de pré-processamento, analisar as transformações realizadas e avaliar o
    comportamento de cada execução através das métricas registadas pelo sistema.
    """
)


try:

    # =========================================================================
    # CONJUNTOS DE DADOS
    # =========================================================================

    datasets = get_datasets()


    if not datasets:

        st.info(
            "Ainda não existem conjuntos de dados importados."
        )

        st.stop()


    presets_data = get_presets()

    supported_operations = (
        presets_data.get(
            "supported_operations",
            {}
        )
    )


    dataset_options = {
        (
            f"{dataset['id']} - "
            f"{dataset['name']}"
        ): dataset["id"]
        for dataset in datasets
    }


    selected_dataset_label = st.selectbox(
        "Selecionar conjunto de dados",
        options=list(
            dataset_options.keys()
        )
    )


    selected_dataset_id = (
        dataset_options[
            selected_dataset_label
        ]
    )


    selected_dataset = next(
        dataset
        for dataset in datasets
        if dataset["id"] == selected_dataset_id
    )


    # =========================================================================
    # INFORMAÇÃO DO CONJUNTO DE DADOS
    # =========================================================================

    col1, col2, col3 = st.columns(3)


    col1.metric(
        "Registos",
        selected_dataset.get(
            "rows_count",
            0
        )
        or 0
    )


    col2.metric(
        "Fonte",
        selected_dataset.get(
            "source"
        )
        or "Não indicada"
    )


    col3.metric(
        "Idioma",
        selected_dataset.get(
            "language"
        )
        or "Não indicado"
    )


    st.divider()


    # =========================================================================
    # HISTÓRICO DAS EXECUÇÕES
    # =========================================================================

    st.subheader(
        "Histórico de execuções"
    )


    runs = get_processing_runs(
        selected_dataset_id
    )


    if not runs:

        st.info(
            "Ainda não existem execuções de pré-processamento "
            "para este conjunto de dados."
        )

        st.stop()


    df_runs = pd.DataFrame(
        runs
    )


    run_columns = [
        column
        for column in [
            "id",
            "configuration_name",
            "pipeline_version",
            "total_posts",
            "processed_posts",
            "failed_posts",
            "duplicate_posts",
            "empty_after_processing",
            "duration_ms",
            "status",
            "started_at",
            "finished_at"
        ]
        if column in df_runs.columns
    ]


    run_column_names = {
        "id": "Execução",
        "configuration_name": "Configuração",
        "pipeline_version": "Versão",
        "total_posts": "Registos",
        "processed_posts": "Processados",
        "failed_posts": "Com erro",
        "duplicate_posts": "Duplicados",
        "empty_after_processing": "Textos vazios",
        "duration_ms": "Duração (ms)",
        "status": "Estado",
        "started_at": "Início",
        "finished_at": "Fim"
    }


    st.dataframe(
        df_runs[
            run_columns
        ].rename(
            columns=run_column_names
        ),
        use_container_width=True,
        hide_index=True
    )


    # =========================================================================
    # SELEÇÃO DA EXECUÇÃO
    # =========================================================================

    run_options = {
        (
            f"Execução {run['id']} - "
            f"{run['configuration_name']} - "
            f"{run['status']}"
        ): run["id"]
        for run in runs
    }


    selected_run_label = st.selectbox(
        "Selecionar execução para análise",
        options=list(
            run_options.keys()
        )
    )


    selected_run_id = (
        run_options[
            selected_run_label
        ]
    )


    # =========================================================================
    # RESUMO
    # =========================================================================

    summary = get_run_summary(
        selected_run_id
    )


    text_statistics = summary.get(
        "text_statistics",
        {}
    )


    metrics = summary.get(
        "metrics",
        {}
    )


    st.divider()

    st.subheader(
        "Resumo da execução"
    )


    col1, col2, col3, col4 = (
        st.columns(4)
    )


    col1.metric(
        "Registos processados",
        text_statistics.get(
            "records",
            0
        )
    )


    col2.metric(
        "Comprimento médio original",
        format_number(
            text_statistics.get(
                "avg_original_length"
            )
        )
    )


    col3.metric(
        "Comprimento médio processado",
        format_number(
            text_statistics.get(
                "avg_processed_length"
            )
        )
    )


    throughput_metric = get_metric(
        metrics,
        "throughput"
    )


    col4.metric(
        "Registos por segundo",
        (
            format_number(
                throughput_metric[
                    "value"
                ]
            )
            if throughput_metric
            else "—"
        )
    )


    # =========================================================================
    # ESTATÍSTICAS TEXTUAIS
    # =========================================================================

    with st.expander(
        "Estatísticas textuais"
    ):

        text_statistics_data = pd.DataFrame(
            [
                {
                    "Indicador": "Registos",
                    "Valor": (
                        text_statistics.get(
                            "records",
                            0
                        )
                    )
                },
                {
                    "Indicador": "Comprimento médio original",
                    "Valor": format_number(
                        text_statistics.get(
                            "avg_original_length"
                        )
                    )
                },
                {
                    "Indicador": "Comprimento médio processado",
                    "Valor": format_number(
                        text_statistics.get(
                            "avg_processed_length"
                        )
                    )
                },
                {
                    "Indicador": "Palavras médias no texto original",
                    "Valor": format_number(
                        text_statistics.get(
                            "avg_original_word_count"
                        )
                    )
                },
                {
                    "Indicador": "Palavras médias no texto processado",
                    "Valor": format_number(
                        text_statistics.get(
                            "avg_processed_word_count"
                        )
                    )
                },
                {
                    "Indicador": "Número médio de tokens",
                    "Valor": format_number(
                        text_statistics.get(
                            "avg_token_count"
                        )
                    )
                }
            ]
        )


        st.dataframe(
            text_statistics_data,
            use_container_width=True,
            hide_index=True
        )


    # =========================================================================
    # MÉTRICAS DE QUALIDADE
    # =========================================================================

    st.subheader(
        "Métricas de qualidade"
    )


    quality_metrics = {
        "proportion_changed_texts":
            "Textos alterados",

        "proportion_empty_texts":
            "Textos vazios",

        "proportion_duplicate_records":
            "Registos duplicados",

        "proportion_failed_records":
            "Registos com erro"
    }


    quality_columns = st.columns(
        len(
            quality_metrics
        )
    )


    for (
        column,
        (
            metric_name,
            metric_label
        )
    ) in zip(
        quality_columns,
        quality_metrics.items()
    ):

        metric = get_metric(
            metrics,
            metric_name
        )


        if metric:

            value = format_percentage(
                metric[
                    "value"
                ]
            )

        else:

            value = "—"


        column.metric(
            metric_label,
            value
        )


    # =========================================================================
    # MÉTRICAS DE TRANSFORMAÇÃO
    # =========================================================================

    transformation_metrics = {
        "proportion_urls_replaced":
            "URLs substituídos",

        "proportion_mentions_anonymized":
            "Menções anonimizadas",

        "proportion_hashtags_normalized":
            "Hashtags normalizadas",

        "proportion_emojis_converted":
            "Emojis convertidos para texto",

        "proportion_emojis_preserved":
            "Emojis preservados",

        "proportion_repeated_sequences_reduced":
            "Sequências repetidas normalizadas"
    }


    available_transformation_metrics = []


    for (
        metric_name,
        metric_label
    ) in transformation_metrics.items():

        metric = get_metric(
            metrics,
            metric_name
        )


        # Uma métrica que não existe significa geralmente que a respetiva
        # operação não foi selecionada.
        if metric is None:
            continue


        available_transformation_metrics.append(
            {
                "Transformação": metric_label,

                "Proporção": format_percentage(
                    metric[
                        "value"
                    ]
                ),

                "Elementos tratados": (
                    metric.get(
                        "numerator"
                    )
                ),

                "Elementos identificados": (
                    metric.get(
                        "denominator"
                    )
                )
            }
        )


    st.subheader(
        "Transformações realizadas"
    )


    if available_transformation_metrics:

        st.dataframe(
            pd.DataFrame(
                available_transformation_metrics
            ),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "Esta execução não possui métricas específicas "
            "de transformação."
        )


    # =========================================================================
    # DESEMPENHO
    # =========================================================================

    st.subheader(
        "Desempenho"
    )


    duration_metric = get_metric(
        metrics,
        "processing_time_ms"
    )


    length_metric = get_metric(
        metrics,
        "average_length_change"
    )


    throughput_metric = get_metric(
        metrics,
        "throughput"
    )


    col1, col2, col3 = (
        st.columns(3)
    )


    col1.metric(
        "Tempo total",
        (
            format_duration(
                duration_metric[
                    "value"
                ]
            )
            if duration_metric
            else "—"
        )
    )


    col2.metric(
        "Throughput",
        (
            (
                f"{format_number(throughput_metric['value'])} "
                f"registos/s"
            )
            if throughput_metric
            else "—"
        )
    )


    col3.metric(
        "Variação média do comprimento",
        (
            (
                f"{format_number(length_metric['value'])} "
                f"caracteres"
            )
            if length_metric
            else "—"
        )
    )


    # =========================================================================
    # ETAPAS EXECUTADAS
    # =========================================================================

    st.subheader(
        "Etapas executadas"
    )


    steps = get_processing_steps(
        selected_run_id
    )


    if steps:

        step_rows = []


        for step in steps:

            rows_received = int(
                step.get(
                    "rows_received",
                    0
                )
                or 0
            )


            rows_changed = int(
                step.get(
                    "rows_changed",
                    0
                )
                or 0
            )


            change_ratio = (
                rows_changed
                / rows_received
                if rows_received > 0
                else 0.0
            )


            operation_name = (
                step.get(
                    "step_name"
                )
            )


            step_rows.append(
                {
                    "Ordem": step.get(
                        "step_order"
                    ),

                    "Operação": (
                        supported_operations.get(
                            operation_name,
                            operation_name
                        )
                    ),

                    "Registos recebidos": (
                        rows_received
                    ),

                    "Registos alterados": (
                        rows_changed
                    ),

                    "Proporção alterada": (
                        format_percentage(
                            change_ratio
                        )
                    ),

                    "Erros": step.get(
                        "rows_failed",
                        0
                    ),

                    "Duração (ms)": step.get(
                        "duration_ms"
                    ),

                    "Estado": step.get(
                        "status"
                    )
                }
            )


        st.dataframe(
            pd.DataFrame(
                step_rows
            ),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "Não foram registadas etapas para esta execução."
        )


    # =========================================================================
    # CONFIGURAÇÃO APLICADA
    # =========================================================================

    with st.expander(
        "Configuração efetivamente aplicada"
    ):

        configuration = summary.get(
            "configuration_json",
            {}
        )


        enabled_operations = [
            operation
            for (
                operation,
                enabled
            ) in configuration.items()
            if enabled
        ]


        if enabled_operations:

            configuration_rows = [
                {
                    "Ordem": index,

                    "Operação": (
                        supported_operations.get(
                            operation,
                            operation
                        )
                    ),

                    "Identificador interno": (
                        operation
                    )
                }

                for (
                    index,
                    operation
                ) in enumerate(
                    enabled_operations,
                    start=1
                )
            ]


            st.dataframe(
                pd.DataFrame(
                    configuration_rows
                ),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "Não foram selecionadas operações nesta execução."
            )


    st.divider()


    # =========================================================================
    # DADOS PROCESSADOS
    # =========================================================================

    st.subheader(
        "Dados processados"
    )


    total_processed_records = int(
        text_statistics.get(
            "records",
            0
        )
        or 0
    )


    col_page_size, col_page_number = (
        st.columns(2)
    )


    with col_page_size:

        processed_page_size = st.selectbox(
            "Registos por página",
            options=[
                25,
                50,
                100,
                250,
                500
            ],
            index=2,
            key=(
                f"processed_page_size_"
                f"{selected_run_id}"
            )
        )


    total_processed_pages = max(
        1,
        math.ceil(
            total_processed_records
            / processed_page_size
        )
    )


    with col_page_number:

        processed_page_number = (
            st.number_input(
                "Página",
                min_value=1,
                max_value=total_processed_pages,
                value=1,
                step=1,
                key=(
                    f"processed_page_number_"
                    f"{selected_run_id}"
                )
            )
        )


    processed_offset = (
        int(
            processed_page_number
        ) - 1
    ) * processed_page_size


    processed_posts = get_processed_posts(
        processing_run_id=selected_run_id,
        limit=processed_page_size,
        offset=processed_offset
    )


    if processed_posts:

        df_processed = pd.DataFrame(
            processed_posts
        )


        # =====================================================================
        # COMPARAÇÃO TEXTUAL
        # =====================================================================

        st.markdown(
            "#### Comparação do texto original e processado"
        )


        comparison_columns = [
            column
            for column in [
                "post_id",
                "original_text",
                "processed_text",
                "is_duplicate",
                "is_empty_after_processing"
            ]
            if column in df_processed.columns
        ]


        comparison_names = {
            "post_id": "Registo",
            "original_text": "Texto original",
            "processed_text": "Texto processado",
            "is_duplicate": "Duplicado",
            "is_empty_after_processing": "Texto vazio"
        }


        st.dataframe(
            df_processed[
                comparison_columns
            ].rename(
                columns=comparison_names
            ),
            use_container_width=True,
            hide_index=True
        )


        # =====================================================================
        # INFORMAÇÃO QUANTITATIVA
        # =====================================================================

        with st.expander(
            "Consultar detalhes dos registos processados"
        ):

            detail_columns = [
                column
                for column in [
                    "post_id",
                    "original_length",
                    "processed_length",
                    "original_word_count",
                    "processed_word_count",
                    "token_count",
                    "tokens",
                    "processed_at"
                ]
                if column in df_processed.columns
            ]


            detail_names = {
                "post_id": "Registo",
                "original_length": "Comprimento original",
                "processed_length": "Comprimento processado",
                "original_word_count": "Palavras originais",
                "processed_word_count": "Palavras processadas",
                "token_count": "Número de tokens",
                "tokens": "Tokens",
                "processed_at": "Processado em"
            }


            st.dataframe(
                df_processed[
                    detail_columns
                ].rename(
                    columns=detail_names
                ),
                use_container_width=True,
                hide_index=True
            )


        # =====================================================================
        # PAGINAÇÃO
        # =====================================================================

        first_record = (
            processed_offset
            + 1
        )


        last_record = (
            processed_offset
            + len(
                processed_posts
            )
        )


        st.caption(
            f"A apresentar os registos "
            f"{first_record} a {last_record} "
            f"de {total_processed_records}. "
            f"Página {int(processed_page_number)} "
            f"de {total_processed_pages}."
        )


        # =====================================================================
        # EXPORTAÇÃO
        # =====================================================================

        st.download_button(
            label=(
                "Descarregar página atual em CSV"
            ),

            data=(
                df_processed
                .to_csv(
                    index=False
                )
                .encode(
                    "utf-8-sig"
                )
            ),

            file_name=(
                f"dados_processados_"
                f"execucao_{selected_run_id}_"
                f"pagina_{int(processed_page_number)}.csv"
            ),

            mime="text/csv"
        )


    else:

        st.info(
            "Não existem resultados na página selecionada."
        )


# =============================================================================
# TRATAMENTO DE ERROS
# =============================================================================

except requests.exceptions.Timeout:

    st.error(
        "O backend demorou demasiado tempo a responder."
    )


except requests.exceptions.ConnectionError:

    st.error(
        "Não foi possível ligar ao backend FastAPI. "
        f"Confirme que está em execução em {API_BASE_URL}."
    )


except requests.exceptions.RequestException as error:

    st.error(
        "Ocorreu um erro durante a comunicação com o backend."
    )

    st.code(
        str(error)
    )


except ApiRequestError as error:

    st.error(
        "O backend devolveu um erro."
    )

    st.code(
        str(error)
    )


except Exception as error:

    st.error(
        f"Ocorreu um erro inesperado: {error}"
    )