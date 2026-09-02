"""
Página de consulta e pré-visualização dos dados brutos.

Esta página permite ao utilizador:

- consultar os conjuntos de dados importados;
- selecionar um conjunto de dados;
- visualizar os respetivos metadados;
- consultar os registos originais;
- visualizar os rótulos originais, quando existentes;
- navegar pelos dados através de paginação.

Os conteúdos apresentados correspondem aos dados brutos preservados antes
da aplicação do pipeline de pré-processamento.
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
# FUNÇÕES AUXILIARES
# =============================================================================

def get_error_detail(
    response: requests.Response
) -> str:
    """
    Obtém a mensagem de erro devolvida pelo backend.
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
    Executa um pedido GET à API.
    """

    response = requests.get(
        f"{API_BASE_URL}{endpoint}",
        params=params,
        timeout=timeout
    )

    if response.status_code != 200:

        raise RuntimeError(
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


def get_dataset(
    dataset_id: int
) -> dict:
    """
    Obtém os metadados de um conjunto de dados.
    """

    return get_json(
        f"/datasets/{dataset_id}"
    )


def get_dataset_posts(
    dataset_id: int,
    limit: int,
    offset: int
) -> list[dict]:
    """
    Obtém uma página dos registos originais.
    """

    return get_json(
        f"/datasets/{dataset_id}/posts",
        params={
            "limit": limit,
            "offset": offset
        }
    )


# =============================================================================
# INTERFACE
# =============================================================================

st.title(
    "Pré-visualização dos Dados"
)

st.markdown(
    """
    Nesta página é possível consultar os conjuntos de dados já importados e
    visualizar os dados brutos preservados na base de dados antes da aplicação
    das operações de pré-processamento.
    """
)


try:

    datasets = get_datasets()


    if not datasets:

        st.info(
            "Ainda não existem conjuntos de dados guardados."
        )

        st.stop()


    # =========================================================================
    # SELEÇÃO DO CONJUNTO DE DADOS
    # =========================================================================

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


    dataset = get_dataset(
        selected_dataset_id
    )


    # =========================================================================
    # RESUMO
    # =========================================================================

    st.subheader(
        "Informação do conjunto de dados"
    )


    col1, col2, col3 = st.columns(3)


    col1.metric(
        "ID",
        dataset["id"]
    )


    col2.metric(
        "Registos",
        dataset.get(
            "rows_count"
        ) or 0
    )


    col3.metric(
        "Fonte",
        dataset.get(
            "source"
        )
        or "Não indicada"
    )


    # =========================================================================
    # METADADOS
    # =========================================================================

    metadata = pd.DataFrame(
        [
            {
                "Propriedade": "Nome",
                "Valor": dataset.get(
                    "name"
                )
            },
            {
                "Propriedade": "Ficheiro original",
                "Valor": dataset.get(
                    "original_filename"
                )
            },
            {
                "Propriedade": "Coluna de ID",
                "Valor": (
                    dataset.get(
                        "id_column"
                    )
                    or "Gerada automaticamente"
                )
            },
            {
                "Propriedade": "Coluna de texto",
                "Valor": dataset.get(
                    "text_column"
                )
            },
            {
                "Propriedade": "Coluna de rótulo",
                "Valor": (
                    dataset.get(
                        "label_column"
                    )
                    or "Não definida"
                )
            },
            {
                "Propriedade": "Idioma",
                "Valor": (
                    dataset.get(
                        "language"
                    )
                    or "Não indicado"
                )
            },
            {
                "Propriedade": "Codificação",
                "Valor": (
                    dataset.get(
                        "encoding"
                    )
                    or "Não indicada"
                )
            },
            {
                "Propriedade": "Delimitador",
                "Valor": (
                    dataset.get(
                        "delimiter"
                    )
                    or "Não indicado"
                )
            },
            {
                "Propriedade": "Data de importação",
                "Valor": dataset.get(
                    "created_at"
                )
            }
        ]
    )


    st.dataframe(
        metadata,
        use_container_width=True,
        hide_index=True
    )


    with st.expander(
        "Informação de integridade e armazenamento"
    ):

        st.write(
            "**Hash SHA-256 do ficheiro:**"
        )

        st.code(
            dataset.get(
                "file_hash"
            )
            or "Não disponível"
        )


        st.write(
            "**Caminho do ficheiro bruto:**"
        )

        st.code(
            dataset.get(
                "raw_file_path"
            )
            or "Não disponível"
        )


    st.divider()


    # =========================================================================
    # DADOS BRUTOS
    # =========================================================================

    st.subheader(
        "Dados brutos armazenados"
    )


    total_records = int(
        dataset.get(
            "rows_count"
        )
        or 0
    )


    col_page_size, col_page_number = (
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
                f"raw_page_size_"
                f"{selected_dataset_id}"
            )
        )


    total_pages = max(
        1,
        math.ceil(
            total_records
            / page_size
        )
    )


    with col_page_number:

        page_number = st.number_input(
            "Página",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1,
            key=(
                f"raw_page_number_"
                f"{selected_dataset_id}"
            )
        )


    offset = (
        int(page_number) - 1
    ) * page_size


    posts = get_dataset_posts(
        dataset_id=selected_dataset_id,
        limit=page_size,
        offset=offset
    )


    if not posts:

        st.info(
            "Não existem registos na página selecionada."
        )

    else:

        df_posts = pd.DataFrame(
            posts
        )


        display_columns = [
            "id",
            "external_id",
            "original_text",
            "original_label",
            "inserted_at"
        ]


        available_columns = [
            column
            for column in display_columns
            if column in df_posts.columns
        ]


        column_names = {
            "id": "ID",
            "external_id": "ID externo",
            "original_text": "Texto original",
            "original_label": "Rótulo original",
            "inserted_at": "Inserido em"
        }


        display_df = (
            df_posts[
                available_columns
            ]
            .rename(
                columns=column_names
            )
        )


        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )


        first_record = (
            offset + 1
        )

        last_record = (
            offset
            + len(posts)
        )


        st.caption(
            f"A apresentar os registos "
            f"{first_record} a {last_record} "
            f"de {total_records}. "
            f"Página {int(page_number)} "
            f"de {total_pages}."
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

    st.code(
        str(error)
    )


except RuntimeError as error:

    st.error(
        str(error)
    )


except Exception as error:

    st.error(
        f"Ocorreu um erro inesperado: {error}"
    )