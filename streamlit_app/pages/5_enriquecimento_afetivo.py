"""
Página de enriquecimento afetivo.

Esta página permite ao utilizador:

1. selecionar um conjunto de dados;
2. selecionar uma execução de pré-processamento concluída;
3. executar a extração de características afetivas;
4. consultar indicadores agregados;
5. visualizar as características extraídas por registo.

O módulo identifica sinais relevantes para posterior análise afetiva,
mas não realiza classificação de emoções ou sentimento.
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

class ApiRequestError(
    RuntimeError
):
    """
    Representa um erro devolvido pelo backend.
    """


# =============================================================================
# API
# =============================================================================

def get_error_detail(
    response: requests.Response
) -> str:
    """
    Obtém o detalhe de um erro devolvido pelo FastAPI.
    """

    try:

        response_data = (
            response.json()
        )

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
    Executa um pedido GET.
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
    Obtém os conjuntos de dados.
    """

    return get_json(
        "/datasets"
    )


def get_processing_runs(
    dataset_id: int
) -> list[dict]:
    """
    Obtém as execuções de pré-processamento de um conjunto de dados.
    """

    return get_json(
        (
            f"/preprocessing/datasets/"
            f"{dataset_id}/runs"
        )
    )


def execute_affective_enrichment(
    processing_run_id: int,
    language: str | None
) -> dict:
    """
    Executa o enriquecimento afetivo.
    """

    response = requests.post(
        (
            f"{API_BASE_URL}/affective/"
            f"runs/{processing_run_id}/enrich"
        ),
        json={
            "language": language
        },
        timeout=300
    )

    if response.status_code != 200:

        raise ApiRequestError(
            get_error_detail(
                response
            )
        )

    return response.json()


def get_affective_summary(
    processing_run_id: int
) -> dict:
    """
    Obtém o resumo das características afetivas.
    """

    return get_json(
        (
            f"/affective/runs/"
            f"{processing_run_id}/summary"
        )
    )


def get_affective_features(
    processing_run_id: int,
    limit: int,
    offset: int
) -> list[dict]:
    """
    Obtém uma página das características afetivas.
    """

    return get_json(
        (
            f"/affective/runs/"
            f"{processing_run_id}/features"
        ),
        params={
            "limit": limit,
            "offset": offset
        }
    )


# =============================================================================
# FORMATAÇÃO
# =============================================================================

def format_percentage(
    value
) -> str:
    """
    Formata uma proporção como percentagem.
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


def calculate_ratio(
    numerator: int,
    denominator: int
) -> float:
    """
    Calcula uma proporção evitando divisão por zero.
    """

    if denominator <= 0:
        return 0.0

    return (
        numerator
        / denominator
    )


# =============================================================================
# INTERFACE
# =============================================================================

st.title(
    "Enriquecimento Afetivo"
)

st.markdown(
    """
    Esta etapa identifica e estrutura características potencialmente relevantes
    para posterior análise afetiva, incluindo emojis, hashtags, termos afetivos,
    utilização de maiúsculas, pontuação expressiva e sinais de intensidade.
    
    O enriquecimento não atribui ainda uma emoção ou sentimento ao texto.
    """
)


try:

    # =========================================================================
    # DATASET
    # =========================================================================

    datasets = get_datasets()


    if not datasets:

        st.info(
            "Ainda não existem conjuntos de dados importados."
        )

        st.stop()


    dataset_options = {
        (
            f"{dataset['id']} - "
            f"{dataset['name']}"
        ): dataset["id"]

        for dataset in datasets
    }


    selected_dataset_label = (
        st.selectbox(
            "Selecionar conjunto de dados",
            options=list(
                dataset_options.keys()
            )
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
        if dataset["id"]
        == selected_dataset_id
    )


    # =========================================================================
    # EXECUÇÕES
    # =========================================================================

    runs = get_processing_runs(
        selected_dataset_id
    )


    completed_runs = [
        run
        for run in runs
        if run.get(
            "status"
        ) in {
            "completed",
            "finished"
        }
    ]


    if not completed_runs:

        st.warning(
            "Este conjunto de dados ainda não possui uma execução "
            "de pré-processamento concluída."
        )

        st.stop()


    run_options = {
        (
            f"Execução {run['id']} - "
            f"{run['configuration_name']}"
        ): run["id"]

        for run in completed_runs
    }


    selected_run_label = (
        st.selectbox(
            "Selecionar execução de pré-processamento",
            options=list(
                run_options.keys()
            )
        )
    )


    selected_run_id = (
        run_options[
            selected_run_label
        ]
    )


    selected_run = next(
        run
        for run in completed_runs
        if run["id"]
        == selected_run_id
    )


    # =========================================================================
    # INFORMAÇÃO DA EXECUÇÃO
    # =========================================================================

    st.subheader(
        "Execução selecionada"
    )


    col1, col2, col3 = (
        st.columns(3)
    )


    col1.metric(
        "Execução",
        selected_run_id
    )


    col2.metric(
        "Registos processados",
        selected_run.get(
            "processed_posts",
            0
        )
    )


    col3.metric(
        "Configuração",
        selected_run.get(
            "configuration_name",
            "—"
        )
    )


    # =========================================================================
    # CONFIGURAÇÃO DO ENRIQUECIMENTO
    # =========================================================================

    st.subheader(
        "Configuração do enriquecimento"
    )


    dataset_language = (
        selected_dataset.get(
            "language"
        )
    )


    language_options = {
        "Automático": None,
        "Inglês": "en",
        "Português": "pt"
    }


    # Tenta selecionar automaticamente uma opção coerente com o dataset.
    default_language_index = 0

    if dataset_language:

        normalized_dataset_language = (
            str(dataset_language)
            .lower()
            .split("-")[0]
        )

        if normalized_dataset_language == "en":
            default_language_index = 1

        elif normalized_dataset_language == "pt":
            default_language_index = 2


    selected_language_label = (
        st.selectbox(
            "Idioma para identificação de termos afetivos",
            options=list(
                language_options.keys()
            ),
            index=default_language_index,
            help=(
                "A seleção do idioma afeta apenas a identificação "
                "lexical de termos afetivos. Emojis, hashtags e "
                "indicadores estruturais são independentes do idioma."
            )
        )
    )


    selected_language = (
        language_options[
            selected_language_label
        ]
    )


    if st.button(
        "Executar enriquecimento afetivo",
        type="primary",
        use_container_width=True
    ):

        with st.spinner(
            "A extrair características afetivas..."
        ):

            result = (
                execute_affective_enrichment(
                    processing_run_id=(
                        selected_run_id
                    ),
                    language=(
                        selected_language
                    )
                )
            )


        st.success(
            "Enriquecimento afetivo concluído com sucesso."
        )


        col1, col2, col3 = (
            st.columns(3)
        )


        col1.metric(
            "Registos enriquecidos",
            result.get(
                "enriched_records",
                0
            )
        )


        col2.metric(
            "Novos registos",
            result.get(
                "created_records",
                0
            )
        )


        col3.metric(
            "Registos atualizados",
            result.get(
                "updated_records",
                0
            )
        )


    st.divider()


    # =========================================================================
    # RESUMO
    # =========================================================================

    affective_summary_response = (
        get_affective_summary(
            selected_run_id
        )
    )


    summary = (
        affective_summary_response.get(
            "summary",
            {}
        )
    )


    total_records = int(
        summary.get(
            "records",
            0
        )
        or 0
    )


    if total_records == 0:

        st.info(
            "Ainda não existem características afetivas para esta "
            "execução. Execute primeiro o enriquecimento afetivo."
        )

        st.stop()


    st.subheader(
        "Resumo das características afetivas"
    )


    col1, col2, col3, col4 = (
        st.columns(4)
    )


    col1.metric(
        "Emojis identificados",
        summary.get(
            "total_emojis",
            0
        )
    )


    col2.metric(
        "Hashtags identificadas",
        summary.get(
            "total_hashtags",
            0
        )
    )


    col3.metric(
        "Termos afetivos",
        summary.get(
            "total_affective_terms",
            0
        )
    )


    col4.metric(
        "Intensidade média",
        (
            f"{summary.get('avg_intensity_score', 0):.4f}"
        )
    )


    # =========================================================================
    # PROPORÇÕES
    # =========================================================================

    st.subheader(
        "Presença de indicadores"
    )


    indicator_rows = [
        {
            "Indicador": "Registos com emojis",

            "Registos": summary.get(
                "records_with_emojis",
                0
            )
        },

        {
            "Indicador": "Registos com hashtags",

            "Registos": summary.get(
                "records_with_hashtags",
                0
            )
        },

        {
            "Indicador": "Registos com termos afetivos",

            "Registos": summary.get(
                "records_with_affective_terms",
                0
            )
        },

        {
            "Indicador": "Registos com exclamações",

            "Registos": summary.get(
                "records_with_exclamations",
                0
            )
        },

        {
            "Indicador": "Registos com interrogações",

            "Registos": summary.get(
                "records_with_questions",
                0
            )
        },

        {
            "Indicador": "Registos com caracteres repetidos",

            "Registos": summary.get(
                "records_with_repeated_characters",
                0
            )
        }
    ]


    for row in indicator_rows:

        row[
            "Proporção"
        ] = format_percentage(
            calculate_ratio(
                row["Registos"],
                total_records
            )
        )


    st.dataframe(
        pd.DataFrame(
            indicator_rows
        ),
        use_container_width=True,
        hide_index=True
    )


    # =========================================================================
    # OUTROS INDICADORES
    # =========================================================================

    st.subheader(
        "Indicadores estruturais"
    )


    col1, col2, col3, col4 = (
        st.columns(4)
    )


    col1.metric(
        "Exclamações",
        summary.get(
            "total_exclamations",
            0
        )
    )


    col2.metric(
        "Interrogações",
        summary.get(
            "total_questions",
            0
        )
    )


    col3.metric(
        "Caracteres repetidos",
        summary.get(
            "total_repeated_characters",
            0
        )
    )


    col4.metric(
        "Maiúsculas médias",
        format_percentage(
            summary.get(
                "avg_uppercase_ratio",
                0.0
            )
        )
    )


    st.divider()


    # =========================================================================
    # REGISTOS
    # =========================================================================

    st.subheader(
        "Características por registo"
    )


    col_page_size, col_page = (
        st.columns(2)
    )


    with col_page_size:

        page_size = st.selectbox(
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
                f"affective_page_size_"
                f"{selected_run_id}"
            )
        )


    total_pages = max(
        1,
        math.ceil(
            total_records
            / page_size
        )
    )


    with col_page:

        page_number = st.number_input(
            "Página",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1,
            key=(
                f"affective_page_"
                f"{selected_run_id}"
            )
        )


    offset = (
        int(page_number)
        - 1
    ) * page_size


    features = (
        get_affective_features(
            processing_run_id=(
                selected_run_id
            ),
            limit=page_size,
            offset=offset
        )
    )


    if features:

        df_features = pd.DataFrame(
            features
        )


        # Converte listas para texto para melhorar a leitura da tabela.
        for column in [
            "emojis",
            "hashtags",
            "affective_terms"
        ]:

            if column in df_features.columns:

                df_features[
                    column
                ] = (
                    df_features[
                        column
                    ]
                    .apply(
                        lambda values:
                            ", ".join(
                                map(
                                    str,
                                    values
                                )
                            )
                            if isinstance(
                                values,
                                list
                            )
                            else ""
                    )
                )


        display_columns = [
            column
            for column in [
                "post_id",
                "processed_text",
                "emojis",
                "emoji_count",
                "hashtags",
                "hashtag_count",
                "affective_terms",
                "affective_term_count",
                "uppercase_ratio",
                "exclamation_count",
                "question_count",
                "repeated_characters_count",
                "intensity_score"
            ]
            if column in df_features.columns
        ]


        column_names = {
            "post_id": "Registo",
            "processed_text": "Texto processado",
            "emojis": "Emojis",
            "emoji_count": "N.º emojis",
            "hashtags": "Hashtags",
            "hashtag_count": "N.º hashtags",
            "affective_terms": "Termos afetivos",
            "affective_term_count": "N.º termos afetivos",
            "uppercase_ratio": "Proporção maiúsculas",
            "exclamation_count": "Exclamações",
            "question_count": "Interrogações",
            "repeated_characters_count": "Caracteres repetidos",
            "intensity_score": "Índice de intensidade"
        }


        st.dataframe(
            df_features[
                display_columns
            ].rename(
                columns=column_names
            ),
            use_container_width=True,
            hide_index=True
        )


        first_record = (
            offset + 1
        )

        last_record = (
            offset
            + len(features)
        )


        st.caption(
            f"A apresentar os registos "
            f"{first_record} a {last_record} "
            f"de {total_records}."
        )


        st.download_button(
            "Descarregar página atual em CSV",

            data=(
                df_features
                .to_csv(
                    index=False
                )
                .encode(
                    "utf-8-sig"
                )
            ),

            file_name=(
                f"caracteristicas_afetivas_"
                f"execucao_{selected_run_id}_"
                f"pagina_{int(page_number)}.csv"
            ),

            mime="text/csv"
        )


# =============================================================================
# ERROS
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