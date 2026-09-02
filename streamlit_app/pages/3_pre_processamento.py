"""
Página de configuração e execução do pré-processamento.

Esta página permite ao utilizador:

1. selecionar um conjunto de dados previamente importado;
2. consultar uma amostra dos dados brutos;
3. selecionar individualmente as operações de pré-processamento;
4. atribuir um nome à configuração;
5. executar o pipeline modular;
6. consultar um resumo imediato da execução realizada.

A consulta detalhada dos resultados, métricas e etapas executadas encontra-se
na página "Dados Processados e Métricas".

O processamento é realizado pelo backend FastAPI. O frontend Streamlit apenas
recolhe a configuração definida pelo utilizador e envia o pedido à API.
"""

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


# Organização visual das operações.
#
# Esta estrutura apenas controla a disposição das opções no frontend.
# A ordem efetiva de execução é definida no backend.
OPERATION_GROUPS = {
    "Extração de elementos": [
        "extract_emojis",
        "extract_hashtags"
    ],

    "Normalização e privacidade": [
        "normalize_unicode",
        "lowercase",
        "replace_urls",
        "anonymize_mentions",
        "normalize_hashtags",
        "convert_emojis_to_text",
        "normalize_spaces"
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

    Quando a resposta contém JSON no formato utilizado pelo FastAPI,
    é utilizado o campo ``detail``. Caso contrário, é devolvido o
    conteúdo textual da resposta.
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
    Executa um pedido GET à API e devolve o conteúdo JSON.
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
    Obtém os conjuntos de dados disponíveis.
    """

    return get_json(
        "/datasets"
    )


def get_presets() -> dict:
    """
    Obtém as operações de pré-processamento suportadas pelo backend.
    """

    return get_json(
        "/preprocessing/presets"
    )


def get_dataset_posts(
    dataset_id: int,
    limit: int = 5,
    offset: int = 0
) -> list[dict]:
    """
    Obtém uma amostra dos registos originais de um conjunto de dados.
    """

    return get_json(
        f"/datasets/{dataset_id}/posts",
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
        dataset_id:
            Identificador do conjunto de dados.

        configuration_name:
            Nome atribuído à configuração.

        config:
            Operações selecionadas pelo utilizador.

    Returns:
        dict:
            Resumo da execução concluída.

    Raises:
        ApiRequestError:
            Quando o backend devolve uma resposta sem sucesso.
    """

    response = requests.post(
        (
            f"{API_BASE_URL}/preprocessing/"
            f"datasets/{dataset_id}/run"
        ),
        json={
            "configuration_name": configuration_name,
            "config": config
        },
        timeout=300
    )

    if response.status_code != 200:
        raise ApiRequestError(
            get_error_detail(response)
        )

    return response.json()


# =============================================================================
# INTERFACE
# =============================================================================

st.title(
    "Pré-processamento dos Dados"
)

st.markdown(
    """
    Nesta página é possível configurar e executar um pipeline modular de
    preparação dos dados. As operações podem ser selecionadas individualmente
    de acordo com as características do conjunto de dados em análise.
    """
)


try:

    # =========================================================================
    # SELEÇÃO DO CONJUNTO DE DADOS
    # =========================================================================

    datasets = get_datasets()

    if not datasets:
        st.info(
            "Ainda não existem conjuntos de dados importados."
        )
        st.stop()


    presets_data = get_presets()

    supported_operations = (
        presets_data[
            "supported_operations"
        ]
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


    # Obtém também os metadados já disponíveis na lista.
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


    # =========================================================================
    # AMOSTRA DOS DADOS BRUTOS
    # =========================================================================

    st.subheader(
        "Amostra dos dados brutos"
    )


    sample_posts = get_dataset_posts(
        dataset_id=selected_dataset_id,
        limit=5
    )


    if sample_posts:

        df_sample = pd.DataFrame(
            sample_posts
        )


        sample_columns = [
            column
            for column in [
                "external_id",
                "original_text",
                "original_label"
            ]
            if column in df_sample.columns
        ]


        sample_column_names = {
            "external_id": "ID externo",
            "original_text": "Texto original",
            "original_label": "Rótulo original"
        }


        st.dataframe(
            df_sample[
                sample_columns
            ].rename(
                columns=sample_column_names
            ),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.warning(
            "O conjunto de dados selecionado não possui registos."
        )


    st.divider()


    # =========================================================================
    # CONFIGURAÇÃO DO PIPELINE
    # =========================================================================

    st.subheader(
        "Configuração do pipeline"
    )


    st.markdown(
        """
        Selecione as operações que pretende aplicar. A configuração é
        normalizada pelo backend e a ordem de execução é definida pelo pipeline.
        """
    )


    with st.form(
        key=(
            f"preprocessing_form_"
            f"{selected_dataset_id}"
        )
    ):

        configuration_name = st.text_input(
            "Nome da configuração",
            value="configuracao_personalizada",
            help=(
                "Permite identificar posteriormente esta execução "
                "no histórico de processamento."
            )
        )


        config: dict[str, bool] = {}


        # ---------------------------------------------------------------------
        # Construção dinâmica dos grupos
        # ---------------------------------------------------------------------

        for (
            group_name,
            operations
        ) in OPERATION_GROUPS.items():

            st.markdown(
                f"#### {group_name}"
            )


            group_columns = st.columns(2)


            for (
                index,
                operation
            ) in enumerate(
                operations
            ):

                # Caso uma operação tenha sido removida ou alterada no backend,
                # esta não é apresentada na interface.
                if operation not in supported_operations:
                    continue


                with group_columns[
                    index % 2
                ]:

                    config[
                        operation
                    ] = st.checkbox(
                        supported_operations[
                            operation
                        ],
                        value=False,
                        key=(
                            f"operation_"
                            f"{selected_dataset_id}_"
                            f"{operation}"
                        )
                    )


        submitted = st.form_submit_button(
            "Executar pré-processamento",
            type="primary",
            use_container_width=True
        )


    # =========================================================================
    # EXECUÇÃO
    # =========================================================================

    if submitted:

        normalized_configuration_name = (
            configuration_name.strip()
        )


        # ---------------------------------------------------------------------
        # Validações do frontend
        # ---------------------------------------------------------------------

        if not normalized_configuration_name:

            st.error(
                "O nome da configuração não pode estar vazio."
            )


        elif (
            config.get(
                "stemming"
            )
            and config.get(
                "lemmatization"
            )
        ):

            st.error(
                "Stemming e lematização não podem ser aplicados "
                "simultaneamente. Selecione apenas uma das operações."
            )


        elif not any(
            config.values()
        ):

            st.warning(
                "Selecione pelo menos uma operação de pré-processamento."
            )


        else:

            # -----------------------------------------------------------------
            # Executar
            # -----------------------------------------------------------------

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
                "Pré-processamento concluído com sucesso."
            )


            # =================================================================
            # RESUMO IMEDIATO
            # =================================================================

            st.subheader(
                "Resumo da execução"
            )


            col1, col2, col3, col4 = (
                st.columns(4)
            )


            col1.metric(
                "Execução",
                result[
                    "processing_run_id"
                ]
            )


            col2.metric(
                "Registos",
                result[
                    "total_posts"
                ]
            )


            col3.metric(
                "Processados",
                result[
                    "processed_posts"
                ]
            )


            col4.metric(
                "Com erro",
                result.get(
                    "failed_posts",
                    0
                )
            )


            col5, col6, col7 = (
                st.columns(3)
            )


            col5.metric(
                "Duplicados",
                result.get(
                    "duplicate_posts",
                    0
                )
            )


            col6.metric(
                "Textos vazios",
                result.get(
                    "empty_after_processing",
                    0
                )
            )


            duration_ms = result.get(
                "duration_ms",
                0
            )


            if duration_ms >= 1000:

                duration_display = (
                    f"{duration_ms / 1000:.2f} s"
                )

            else:

                duration_display = (
                    f"{duration_ms} ms"
                )


            col7.metric(
                "Duração",
                duration_display
            )


            st.info(
                "Os resultados detalhados, as etapas executadas e as "
                "métricas desta execução podem ser consultados na página "
                "'Dados Processados e Métricas'."
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