"""
Página de consulta e pré-visualização dos dados brutos.

Esta página permite ao utilizador:

- consultar os datasets já importados;
- selecionar um dataset;
- visualizar os respetivos metadados;
- consultar as publicações originais armazenadas na base de dados;
- navegar pelos registos através de paginação.

Os dados apresentados nesta página ainda não foram submetidos ao pipeline
de pré-processamento.
"""

import math
import os

import pandas as pd
import requests
import streamlit as st


# Endereço base do backend FastAPI.
#
# A variável de ambiente permite utilizar diferentes endereços consoante
# o ambiente de execução. Quando não está definida, é utilizado o backend local.
API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000"
)


def get_error_detail(response: requests.Response) -> str:
    """
    Obtém a mensagem de erro devolvida pelo backend.

    Quando a resposta contém JSON no formato utilizado pelo FastAPI, é extraído
    o campo ``detail``. Caso contrário, é devolvido o conteúdo textual.

    Args:
        response: Resposta HTTP recebida.

    Returns:
        str: Mensagem de erro interpretada.
    """

    try:
        response_data = response.json()
        return str(response_data.get("detail", response_data))
    except ValueError:
        return response.text


def get_datasets() -> list[dict]:
    """
    Obtém a lista de datasets registados no sistema.

    Returns:
        list[dict]: Metadados dos datasets existentes.

    Raises:
        RuntimeError: Quando o backend devolve uma resposta sem sucesso.
    """

    response = requests.get(
        f"{API_BASE_URL}/datasets",
        timeout=30
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Não foi possível obter a lista de datasets. "
            f"Detalhe: {get_error_detail(response)}"
        )

    return response.json()


def get_dataset(dataset_id: int) -> dict:
    """
    Obtém os metadados de um dataset específico.

    Args:
        dataset_id: Identificador interno do dataset.

    Returns:
        dict: Metadados do dataset.

    Raises:
        RuntimeError: Quando o dataset não pode ser consultado.
    """

    response = requests.get(
        f"{API_BASE_URL}/datasets/{dataset_id}",
        timeout=30
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Não foi possível obter a informação do dataset. "
            f"Detalhe: {get_error_detail(response)}"
        )

    return response.json()


def get_dataset_posts(
    dataset_id: int,
    limit: int,
    offset: int
) -> list[dict]:
    """
    Obtém uma página das publicações originais de um dataset.

    Args:
        dataset_id: Identificador do dataset.
        limit: Número máximo de publicações a devolver.
        offset: Número de publicações anteriores a ignorar.

    Returns:
        list[dict]: Publicações da página solicitada.

    Raises:
        RuntimeError: Quando os registos não podem ser consultados.
    """

    response = requests.get(
        f"{API_BASE_URL}/datasets/{dataset_id}/posts",
        params={
            "limit": limit,
            "offset": offset
        },
        timeout=30
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Não foi possível obter as publicações do dataset. "
            f"Detalhe: {get_error_detail(response)}"
        )

    return response.json()


# -------------------------------------------------------------------------
# Configuração visual da página
# -------------------------------------------------------------------------

st.title("Pré-visualização dos Dados")

st.markdown(
    """
    Nesta página é possível consultar os datasets já importados e visualizar
    os dados brutos preservados na base de dados antes da aplicação das
    operações de pré-processamento.
    """
)


try:
    # Obtém os datasets registados para preencher o componente de seleção.
    datasets = get_datasets()

    if not datasets:
        st.info(
            "Ainda não existem datasets guardados na base de dados."
        )
        st.stop()

    # Associa o texto apresentado na interface ao identificador interno
    # utilizado nos pedidos enviados ao backend.
    dataset_options = {
        f"{dataset['id']} - {dataset['name']}": dataset["id"]
        for dataset in datasets
    }

    selected_dataset_label = st.selectbox(
        "Selecionar dataset",
        options=list(dataset_options.keys())
    )

    selected_dataset_id = dataset_options[selected_dataset_label]

    # Obtém a informação detalhada do dataset selecionado.
    dataset = get_dataset(selected_dataset_id)

    # ---------------------------------------------------------------------
    # Metadados do dataset
    # ---------------------------------------------------------------------

    st.subheader("Informação do dataset")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "ID",
        dataset["id"]
    )

    col2.metric(
        "Registos",
        dataset["rows_count"] or 0
    )

    col3.metric(
        "Fonte",
        dataset["source"] or "Não indicada"
    )

    st.write("Nome:")
    st.code(dataset["name"])

    st.write("Ficheiro original:")
    st.code(dataset["original_filename"])

    st.write("Coluna de ID original:")
    st.code(
        dataset["id_column"]
        or "Gerada automaticamente"
    )

    st.write("Coluna de texto original:")
    st.code(dataset["text_column"])

    st.write("Data de importação:")
    st.code(str(dataset["created_at"]))

    st.divider()

    # ---------------------------------------------------------------------
    # Paginação das publicações
    # ---------------------------------------------------------------------

    st.subheader("Dados brutos armazenados")

    total_records = int(dataset["rows_count"] or 0)

    col_page_size, col_page_number = st.columns(2)

    with col_page_size:
        page_size = st.selectbox(
            "Registos por página",
            options=[25, 50, 100, 250, 500],
            index=2,
            key=f"raw_page_size_{selected_dataset_id}"
        )

    # Calcula o número total de páginas. É mantida pelo menos uma página
    # para evitar valores inválidos no componente number_input.
    total_pages = max(
        1,
        math.ceil(total_records / page_size)
    )

    with col_page_number:
        page_number = st.number_input(
            "Página",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1,
            key=f"raw_page_number_{selected_dataset_id}"
        )

    # O offset representa o número de registos a ignorar.
    offset = (page_number - 1) * page_size

    posts = get_dataset_posts(
        dataset_id=selected_dataset_id,
        limit=page_size,
        offset=offset
    )

    if posts:
        df_posts = pd.DataFrame(posts)

        # Seleciona explicitamente as colunas relevantes para a consulta
        # dos dados brutos.
        display_columns = [
            "id",
            "dataset_id",
            "external_id",
            "original_text",
            "inserted_at"
        ]

        available_display_columns = [
            column
            for column in display_columns
            if column in df_posts.columns
        ]

        st.dataframe(
            df_posts[available_display_columns],
            use_container_width=True,
            hide_index=True
        )

        first_record = offset + 1
        last_record = offset + len(posts)

        st.caption(
            f"A apresentar os registos {first_record} a {last_record} "
            f"de {total_records}. Página {page_number} de {total_pages}."
        )

    else:
        st.info(
            "Este dataset não possui publicações na página selecionada."
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

except RuntimeError as error:
    st.error(str(error))

except Exception as error:
    st.error(
        f"Ocorreu um erro inesperado: {error}"
    )