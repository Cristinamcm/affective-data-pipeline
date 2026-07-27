"""
Página de configuração e execução do pré-processamento.

Esta página permite ao utilizador:

1. selecionar um dataset previamente importado;
2. consultar uma amostra dos dados brutos;
3. escolher um preset ou construir uma configuração personalizada;
4. executar o pipeline modular de pré-processamento;
5. consultar o histórico de execuções;
6. visualizar métricas agregadas;
7. comparar o texto original com o texto processado;
8. descarregar uma página dos resultados em formato CSV.

O processamento textual é realizado pelo backend FastAPI. O Streamlit apenas
recolhe a configuração, envia o pedido e apresenta os resultados.
"""

import math
import os

import pandas as pd
import requests
import streamlit as st


API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000"
)


# Organização visual das operações apresentadas no formulário.
#
# Esta estrutura apenas determina a disposição na interface. A ordem real
# de execução é definida no backend, em preprocessing_pipeline.py.
OPERATION_GROUPS = {
    "Normalização básica": [
        "normalize_unicode",
        "lowercase",
        "normalize_spaces"
    ],
    "Privacidade e anonimização": [
        "replace_urls",
        "anonymize_mentions"
    ],
    "Elementos sociais e afetivos": [
        "extract_hashtags",
        "normalize_hashtags",
        "extract_emojis",
        "convert_emojis_to_text"
    ],
    "Redução de ruído textual": [
        "expand_abbreviations",
        "reduce_repeated_characters",
        "remove_special_characters",
        "remove_selected_punctuation"
    ],
    "Transformação linguística": [
        "tokenize",
        "remove_stopwords",
        "stemming",
        "lemmatization"
    ]
}


class ApiRequestError(RuntimeError):
    """
    Representa um erro devolvido pela API FastAPI.
    """


def get_error_detail(response: requests.Response) -> str:
    """
    Obtém o detalhe de erro devolvido pelo backend.

    Args:
        response: Resposta HTTP recebida.

    Returns:
        str: Mensagem interpretada a partir da resposta.
    """

    try:
        response_data = response.json()
        return str(response_data.get("detail", response_data))
    except ValueError:
        return response.text


def get_json(
    endpoint: str,
    params: dict | None = None,
    timeout: int = 30
):
    """
    Executa um pedido GET e devolve o respetivo conteúdo JSON.

    Args:
        endpoint: Caminho do endpoint sem o endereço base.
        params: Parâmetros opcionais enviados na query string.
        timeout: Tempo máximo de espera, em segundos.

    Returns:
        Conteúdo JSON devolvido pelo backend.

    Raises:
        ApiRequestError: Quando o backend devolve um código sem sucesso.
    """

    response = requests.get(
        f"{API_BASE_URL}{endpoint}",
        params=params,
        timeout=timeout
    )

    if response.status_code != 200:
        raise ApiRequestError(
            get_error_detail(response)
        )

    return response.json()


def get_datasets() -> list[dict]:
    """
    Obtém os datasets disponíveis para pré-processamento.
    """

    return get_json("/datasets")


def get_presets() -> dict:
    """
    Obtém as operações suportadas e os presets definidos no backend.
    """

    return get_json("/preprocessing/presets")


def get_dataset_posts(
    dataset_id: int,
    limit: int = 5,
    offset: int = 0
) -> list[dict]:
    """
    Obtém uma amostra das publicações originais de um dataset.
    """

    return get_json(
        f"/datasets/{dataset_id}/posts",
        params={
            "limit": limit,
            "offset": offset
        }
    )


def get_processing_runs(dataset_id: int) -> list[dict]:
    """
    Obtém o histórico de execuções associado a um dataset.
    """

    return get_json(
        f"/preprocessing/datasets/{dataset_id}/runs"
    )


def get_run_summary(processing_run_id: int) -> dict:
    """
    Obtém o resumo e as métricas agregadas de uma execução.
    """

    return get_json(
        f"/preprocessing/runs/{processing_run_id}/summary"
    )


def get_processed_posts(
    processing_run_id: int,
    limit: int,
    offset: int
) -> list[dict]:
    """
    Obtém uma página dos resultados individuais de uma execução.
    """

    return get_json(
        f"/preprocessing/runs/{processing_run_id}/posts",
        params={
            "limit": limit,
            "offset": offset
        }
    )


def execute_preprocessing(
    dataset_id: int,
    configuration_name: str,
    config: dict[str, bool]
) -> dict:
    """
    Solicita ao backend a execução do pipeline de pré-processamento.

    Args:
        dataset_id: Dataset que será processado.
        configuration_name: Nome atribuído à execução.
        config: Operações selecionadas pelo utilizador.

    Returns:
        dict: Resumo da execução concluída.

    Raises:
        ApiRequestError: Quando o backend não conclui o pedido com sucesso.
    """

    response = requests.post(
        f"{API_BASE_URL}/preprocessing/datasets/{dataset_id}/run",
        json={
            "configuration_name": configuration_name,
            "config": config
        },
        timeout=180
    )

    if response.status_code != 200:
        raise ApiRequestError(
            get_error_detail(response)
        )

    return response.json()


# -------------------------------------------------------------------------
# Configuração visual da página
# -------------------------------------------------------------------------

st.title("Pré-processamento dos Dados")

st.markdown(
    """
    Nesta página é possível configurar e executar um pipeline modular de
    pré-processamento sobre os dados brutos previamente importados.
    """
)


try:
    # ---------------------------------------------------------------------
    # Seleção do dataset
    # ---------------------------------------------------------------------

    datasets = get_datasets()

    if not datasets:
        st.info(
            "Ainda não existem datasets importados."
        )
        st.stop()

    presets_data = get_presets()

    supported_operations = presets_data["supported_operations"]
    presets = presets_data["presets"]

    dataset_options = {
        f"{dataset['id']} - {dataset['name']}": dataset["id"]
        for dataset in datasets
    }

    selected_dataset_label = st.selectbox(
        "Selecionar dataset",
        options=list(dataset_options.keys())
    )

    selected_dataset_id = dataset_options[selected_dataset_label]

    # ---------------------------------------------------------------------
    # Amostra dos dados brutos
    # ---------------------------------------------------------------------

    st.subheader("Amostra dos dados brutos")

    sample_posts = get_dataset_posts(
        dataset_id=selected_dataset_id,
        limit=5
    )

    if sample_posts:
        df_sample = pd.DataFrame(sample_posts)

        sample_columns = [
            column
            for column in [
                "id",
                "external_id",
                "original_text"
            ]
            if column in df_sample.columns
        ]

        st.dataframe(
            df_sample[sample_columns],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning(
            "O dataset selecionado não possui publicações."
        )

    st.divider()

    # ---------------------------------------------------------------------
    # Configuração do pipeline
    # ---------------------------------------------------------------------

    st.subheader("Configuração do pipeline")

    preset_labels = {
        "minimal": "Mínima",
        "intermediate": "Intermédia",
        "aggressive": "Agressiva",
        "custom": "Personalizada"
    }

    preset_choice = st.selectbox(
        "Escolher configuração inicial",
        options=[
            "minimal",
            "intermediate",
            "aggressive",
            "custom"
        ],
        format_func=lambda value: preset_labels[value]
    )

    if preset_choice == "custom":
        base_config = {
            operation: False
            for operation in supported_operations
        }
    else:
        # Cria uma cópia para evitar alterações diretas no preset recebido.
        base_config = dict(presets[preset_choice])

    st.markdown("### Operações disponíveis")

    # Os componentes são inseridos num formulário para que a execução apenas
    # seja iniciada depois de o utilizador confirmar a configuração.
    with st.form(
        key=(
            f"preprocessing_form_"
            f"{selected_dataset_id}_"
            f"{preset_choice}"
        )
    ):
        configuration_name = st.text_input(
            "Nome da configuração/execução",
            value=preset_choice,
            key=(
                f"configuration_name_"
                f"{selected_dataset_id}_"
                f"{preset_choice}"
            )
        )

        config: dict[str, bool] = {}

        # Constrói dinamicamente os checkboxes a partir das operações
        # disponibilizadas pelo backend.
        for group_name, operations in OPERATION_GROUPS.items():
            st.markdown(f"#### {group_name}")

            group_columns = st.columns(2)

            for index, operation in enumerate(operations):
                # Ignora uma operação caso tenha sido removida do backend,
                # evitando um KeyError na interface.
                if operation not in supported_operations:
                    continue

                with group_columns[index % 2]:
                    config[operation] = st.checkbox(
                        supported_operations[operation],
                        value=base_config.get(operation, False),
                        key=(
                            f"operation_"
                            f"{selected_dataset_id}_"
                            f"{preset_choice}_"
                            f"{operation}"
                        )
                    )

        submitted = st.form_submit_button(
            "Executar pré-processamento",
            type="primary"
        )

    if submitted:
        normalized_configuration_name = configuration_name.strip()

        if not normalized_configuration_name:
            st.error(
                "O nome da configuração não pode estar vazio."
            )

        elif (
            config.get("stemming")
            and config.get("lemmatization")
        ):
            st.error(
                "Stemming e lematização não devem ser aplicados "
                "simultaneamente. Selecione apenas uma destas operações."
            )

        else:
            if not any(config.values()):
                st.warning(
                    "Nenhuma operação foi selecionada. O texto será "
                    "armazenado sem transformações relevantes."
                )

            try:
                # A execução é síncrona. A página aguarda pela resposta
                # do backend até ao limite definido no pedido.
                with st.spinner(
                    "A executar o pré-processamento..."
                ):
                    result = execute_preprocessing(
                        dataset_id=selected_dataset_id,
                        configuration_name=(
                            normalized_configuration_name
                        ),
                        config=config
                    )

                st.success(
                    "Pré-processamento executado com sucesso."
                )

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "Run ID",
                    result["processing_run_id"]
                )

                col2.metric(
                    "Posts totais",
                    result["total_posts"]
                )

                col3.metric(
                    "Posts processados",
                    result["processed_posts"]
                )

                col4.metric(
                    "Duplicados",
                    result["duplicate_posts"]
                )

                st.metric(
                    "Textos vazios após processamento",
                    result["empty_after_processing"]
                )

            except ApiRequestError as error:
                st.error(
                    "O backend não conseguiu concluir "
                    "o pré-processamento."
                )
                st.code(str(error))

            except requests.exceptions.Timeout:
                st.error(
                    "O pré-processamento excedeu o tempo limite. "
                    "O backend poderá continuar a processar o dataset."
                )

    st.divider()

    # ---------------------------------------------------------------------
    # Histórico de execuções
    # ---------------------------------------------------------------------

    st.subheader("Execuções de pré-processamento")

    runs = get_processing_runs(selected_dataset_id)

    if not runs:
        st.info(
            "Ainda não existem execuções de pré-processamento "
            "para este dataset."
        )
        st.stop()

    df_runs = pd.DataFrame(runs)

    run_display_columns = [
        column
        for column in [
            "id",
            "configuration_name",
            "total_posts",
            "processed_posts",
            "duplicate_posts",
            "empty_after_processing",
            "status",
            "started_at",
            "finished_at"
        ]
        if column in df_runs.columns
    ]

    st.dataframe(
        df_runs[run_display_columns],
        use_container_width=True,
        hide_index=True
    )

    run_options = {
        (
            f"{run['id']} - "
            f"{run['configuration_name']} - "
            f"{run['status']}"
        ): run["id"]
        for run in runs
    }

    selected_run_label = st.selectbox(
        "Selecionar execução para visualizar resultados",
        options=list(run_options.keys())
    )

    selected_run_id = run_options[selected_run_label]

    # ---------------------------------------------------------------------
    # Métricas agregadas da execução
    # ---------------------------------------------------------------------

    summary = get_run_summary(selected_run_id)
    metrics = summary["metrics"]

    st.markdown("### Métricas da execução")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Registos",
        metrics["records"]
    )

    col2.metric(
        "Média do tamanho original",
        round(metrics["avg_original_length"], 2)
    )

    col3.metric(
        "Média do tamanho processado",
        round(metrics["avg_processed_length"], 2)
    )

    col4.metric(
        "Média de palavras",
        round(metrics["avg_word_count"], 2)
    )

    col5, col6, col7, col8 = st.columns(4)

    col5.metric(
        "URLs detetados",
        metrics["total_urls"]
    )

    col6.metric(
        "Menções detetadas",
        metrics["total_mentions"]
    )

    col7.metric(
        "Hashtags detetadas",
        metrics["total_hashtags"]
    )

    col8.metric(
        "Emojis detetados",
        metrics["total_emojis"]
    )

    # Métricas relacionadas com a presença dos elementos no dataset.
    social_metrics = pd.DataFrame(
        [
            {
                "Indicador": "Posts com URL",
                "Total": metrics["posts_with_url"]
            },
            {
                "Indicador": "Posts com menção",
                "Total": metrics["posts_with_mention"]
            },
            {
                "Indicador": "Posts com hashtag",
                "Total": metrics["posts_with_hashtag"]
            },
            {
                "Indicador": "Duplicados",
                "Total": metrics["duplicate_posts"]
            },
            {
                "Indicador": "Vazios após processamento",
                "Total": metrics["empty_after_processing"]
            }
        ]
    )

    st.markdown("### Indicadores dos dados")

    st.bar_chart(
        social_metrics.set_index("Indicador")
    )

    # Métricas que demonstram as transformações efetivamente aplicadas.
    transformation_metrics = pd.DataFrame(
        [
            {
                "Transformação": "URLs removidos",
                "Total": metrics.get(
                    "urls_removed_count",
                    0
                )
            },
            {
                "Transformação": "URLs substituídos",
                "Total": metrics.get(
                    "urls_replaced_count",
                    0
                )
            },
            {
                "Transformação": "Menções anonimizadas",
                "Total": metrics.get(
                    "mentions_anonymized_count",
                    0
                )
            },
            {
                "Transformação": "Hashtags removidas",
                "Total": metrics.get(
                    "hashtags_removed_count",
                    0
                )
            },
            {
                "Transformação": "Emojis preservados",
                "Total": metrics.get(
                    "emojis_preserved_count",
                    0
                )
            }
        ]
    )

    st.markdown("### Transformações realizadas")

    st.dataframe(
        transformation_metrics,
        use_container_width=True,
        hide_index=True
    )

    st.bar_chart(
        transformation_metrics.set_index("Transformação")
    )

    st.markdown("### Configuração aplicada")
    st.json(summary["configuration_json"])

    st.divider()

    # ---------------------------------------------------------------------
    # Paginação dos resultados individuais
    # ---------------------------------------------------------------------

    st.markdown("### Dados processados")

    total_processed_records = int(
        metrics.get("records", 0)
    )

    col_page_size, col_page_number = st.columns(2)

    with col_page_size:
        processed_page_size = st.selectbox(
            "Resultados por página",
            options=[25, 50, 100, 250, 500],
            index=2,
            key=f"processed_page_size_{selected_run_id}"
        )

    total_processed_pages = max(
        1,
        math.ceil(
            total_processed_records / processed_page_size
        )
    )

    with col_page_number:
        processed_page_number = st.number_input(
            "Página de resultados",
            min_value=1,
            max_value=total_processed_pages,
            value=1,
            step=1,
            key=f"processed_page_number_{selected_run_id}"
        )

    processed_offset = (
        processed_page_number - 1
    ) * processed_page_size

    processed_posts = get_processed_posts(
        processing_run_id=selected_run_id,
        limit=processed_page_size,
        offset=processed_offset
    )

    if processed_posts:
        df_processed = pd.DataFrame(processed_posts)

        metrics_columns = [
            "post_id",
            "original_text",
            "processed_text",
            "word_count",
            "token_count",
            "emoji_count",
            "url_count",
            "mention_count",
            "hashtag_count",
            "urls_removed_count",
            "urls_replaced_count",
            "mentions_anonymized_count",
            "hashtags_removed_count",
            "emojis_preserved_count",
            "is_duplicate",
            "is_empty_after_processing"
        ]

        available_metrics_columns = [
            column
            for column in metrics_columns
            if column in df_processed.columns
        ]

        st.dataframe(
            df_processed[available_metrics_columns],
            use_container_width=True,
            hide_index=True
        )

        st.markdown(
            "### Texto original vs. texto processado"
        )

        comparison_columns = [
            "original_text",
            "processed_text",
            "tokens",
            "emojis",
            "hashtags",
            "applied_steps"
        ]

        available_comparison_columns = [
            column
            for column in comparison_columns
            if column in df_processed.columns
        ]

        st.dataframe(
            df_processed[available_comparison_columns],
            use_container_width=True,
            hide_index=True
        )

        first_record = processed_offset + 1
        last_record = processed_offset + len(processed_posts)

        st.caption(
            f"A apresentar os resultados {first_record} a {last_record} "
            f"de {total_processed_records}."
        )

        # Apenas os registos atualmente carregados são incluídos no ficheiro.
        st.download_button(
            label="Descarregar página atual em CSV",
            data=df_processed.to_csv(
                index=False
            ).encode("utf-8"),
            file_name=(
                f"processed_run_{selected_run_id}_"
                f"page_{processed_page_number}.csv"
            ),
            mime="text/csv"
        )

    else:
        st.info(
            "Esta execução não possui dados processados "
            "na página selecionada."
        )

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
    st.code(str(error))

except ApiRequestError as error:
    st.error(
        "O backend devolveu um erro."
    )
    st.code(str(error))

except Exception as error:
    st.error(
        f"Ocorreu um erro inesperado: {error}"
    )