"""
Página de recolha e importação de dados.

Esta página permite ao utilizador:

1. selecionar um ficheiro CSV;
2. guardar o ficheiro na área de armazenamento bruto;
3. configurar a leitura do ficheiro;
4. solicitar ao backend uma pré-visualização;
5. mapear as colunas relevantes;
6. identificar opcionalmente uma coluna de rótulo;
7. importar o conjunto de dados para a base de dados.

O frontend Streamlit não escreve diretamente na base de dados.
A persistência é delegada ao backend FastAPI.
"""

import os
from pathlib import Path

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

RAW_DATA_DIR = Path("data/raw")

RAW_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
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


def normalize_delimiter_for_api(
    delimiter_label: str
) -> str:
    """
    Converte a designação apresentada ao utilizador no valor
    enviado para a API.
    """

    delimiters = {
        "Vírgula (,)": ",",
        "Ponto e vírgula (;)": ";",
        "Tabulação": "\\t",
        "Barra vertical (|)": "|"
    }

    return delimiters[
        delimiter_label
    ]


# =============================================================================
# INTERFACE
# =============================================================================

st.title("Recolha de Dados")

st.markdown(
    """
    Nesta página é possível carregar conjuntos de dados públicos em formato
    CSV, visualizar uma amostra dos dados e mapear as colunas relevantes
    para a representação interna do sistema.
    """
)


uploaded_file = st.file_uploader(
    "Carregar ficheiro CSV",
    type=["csv"]
)


if uploaded_file is None:

    st.info(
        "Carregue um ficheiro CSV para iniciar a recolha de dados."
    )

    st.stop()


# =============================================================================
# ARMAZENAMENTO DO FICHEIRO BRUTO
# =============================================================================

input_filename = Path(
    uploaded_file.name
).name

input_path = (
    RAW_DATA_DIR
    / input_filename
)


try:

    with input_path.open(
        "wb"
    ) as file:

        file.write(
            uploaded_file.getbuffer()
        )

    st.success(
        f"Ficheiro carregado com sucesso: {input_filename}"
    )

except OSError as error:

    st.error(
        "Não foi possível guardar o ficheiro na área "
        "de armazenamento bruto."
    )

    st.code(
        str(error)
    )

    st.stop()


# =============================================================================
# CONFIGURAÇÃO DA LEITURA
# =============================================================================

st.subheader(
    "Configuração do ficheiro"
)

col_encoding, col_delimiter = st.columns(2)


with col_encoding:

    encoding = st.selectbox(
        "Codificação",
        options=[
            "utf-8",
            "utf-8-sig",
            "latin-1",
            "cp1252"
        ],
        index=0
    )


with col_delimiter:

    delimiter_label = st.selectbox(
        "Delimitador",
        options=[
            "Vírgula (,)",
            "Ponto e vírgula (;)",
            "Tabulação",
            "Barra vertical (|)"
        ]
    )


delimiter = normalize_delimiter_for_api(
    delimiter_label
)


# =============================================================================
# PRÉ-VISUALIZAÇÃO
# =============================================================================

try:

    preview_response = requests.get(
        f"{API_BASE_URL}/datasets/csv/preview",
        params={
            "input_filename": input_filename,
            "encoding": encoding,
            "delimiter": delimiter
        },
        timeout=30
    )

except requests.exceptions.Timeout:

    st.error(
        "O backend demorou demasiado tempo a gerar "
        "a pré-visualização."
    )

    st.stop()

except requests.exceptions.ConnectionError:

    st.error(
        "Não foi possível ligar ao backend FastAPI. "
        f"Confirme que está em execução em {API_BASE_URL}."
    )

    st.stop()

except requests.exceptions.RequestException as error:

    st.error(
        "Ocorreu um erro durante a comunicação com o backend."
    )

    st.code(
        str(error)
    )

    st.stop()


if preview_response.status_code != 200:

    st.error(
        "Não foi possível obter a pré-visualização do ficheiro."
    )

    st.code(
        get_error_detail(
            preview_response
        )
    )

    st.stop()


preview_data = preview_response.json()

available_columns = preview_data[
    "columns"
]


st.subheader(
    "Pré-visualização dos dados"
)

st.dataframe(
    pd.DataFrame(
        preview_data["preview"]
    ),
    use_container_width=True,
    hide_index=True
)


col_rows, col_columns = st.columns(2)

col_rows.metric(
    "Número de registos",
    preview_data["rows_count"]
)

col_columns.metric(
    "Número de colunas",
    len(available_columns)
)


with st.expander(
    "Consultar colunas disponíveis"
):

    st.code(
        "\n".join(
            available_columns
        )
    )


# =============================================================================
# METADADOS
# =============================================================================

st.divider()

st.subheader(
    "Informação do conjunto de dados"
)


dataset_name = st.text_input(
    "Nome do conjunto de dados",
    value=Path(
        input_filename
    ).stem
)


source = st.text_input(
    "Fonte",
    value="Kaggle",
    help=(
        "Exemplos: Kaggle, SemEval, YouTube "
        "ou carregamento manual."
    )
)


language = st.text_input(
    "Idioma predominante",
    value="",
    placeholder="Ex.: en, pt, es",
    help=(
        "Campo opcional. Utilize um código de idioma "
        "quando este seja conhecido."
    )
)


# =============================================================================
# MAPEAMENTO DE COLUNAS
# =============================================================================

st.subheader(
    "Mapeamento de colunas"
)


id_column_option = st.selectbox(
    "Coluna de identificador externo",
    options=[
        "Nenhuma"
    ] + available_columns,
    help=(
        "Caso não exista uma coluna identificadora, "
        "o sistema gera identificadores sequenciais."
    )
)


text_column = st.selectbox(
    "Coluna que contém o texto",
    options=available_columns
)


label_column_option = st.selectbox(
    "Coluna de rótulo original",
    options=[
        "Nenhuma"
    ] + available_columns,
    help=(
        "Opcional. Pode corresponder, por exemplo, a sentimento, "
        "emoção ou outra classificação existente no dataset."
    )
)


id_column = (
    None
    if id_column_option == "Nenhuma"
    else id_column_option
)


label_column = (
    None
    if label_column_option == "Nenhuma"
    else label_column_option
)


# =============================================================================
# IMPORTAÇÃO
# =============================================================================

st.divider()


if st.button(
    "Guardar conjunto de dados",
    type="primary"
):

    normalized_dataset_name = (
        dataset_name.strip()
    )

    normalized_source = (
        source.strip()
    )

    normalized_language = (
        language.strip()
        or None
    )


    if not normalized_dataset_name:

        st.error(
            "O nome do conjunto de dados não pode estar vazio."
        )

        st.stop()


    if not normalized_source:

        st.error(
            "A fonte não pode estar vazia."
        )

        st.stop()


    try:

        with st.spinner(
            "A importar o conjunto de dados..."
        ):

            import_response = requests.post(
                f"{API_BASE_URL}/datasets/import-csv",
                params={
                    "input_filename": input_filename,
                    "dataset_name": normalized_dataset_name,
                    "source": normalized_source,
                    "text_column": text_column,
                    "id_column": id_column,
                    "label_column": label_column,
                    "language": normalized_language,
                    "encoding": encoding,
                    "delimiter": delimiter
                },
                timeout=120
            )


        if import_response.status_code != 200:

            st.error(
                "Não foi possível guardar o conjunto de dados."
            )

            st.code(
                get_error_detail(
                    import_response
                )
            )

            st.stop()


        result = import_response.json()


        st.success(
            "Conjunto de dados guardado com sucesso."
        )


        col1, col2, col3 = st.columns(3)

        col1.metric(
            "ID",
            result["dataset_id"]
        )

        col2.metric(
            "Registos",
            result["rows_count"]
        )

        col3.metric(
            "Fonte",
            result["source"]
        )


        st.markdown(
            "### Mapeamento registado"
        )


        mapping_data = {
            "Campo": [
                "Identificador externo",
                "Texto",
                "Rótulo"
            ],
            "Coluna original": [
                (
                    result["id_column"]
                    or "Gerado automaticamente"
                ),
                result["text_column"],
                (
                    result["label_column"]
                    or "Não definida"
                )
            ]
        }


        st.dataframe(
            pd.DataFrame(
                mapping_data
            ),
            use_container_width=True,
            hide_index=True
        )


        with st.expander(
            "Metadados técnicos"
        ):

            st.write(
                f"**Codificação:** "
                f"{result.get('encoding') or 'Não indicada'}"
            )

            st.write(
                f"**Delimitador:** "
                f"{result.get('delimiter') or 'Não indicado'}"
            )

            st.write(
                f"**Idioma:** "
                f"{result.get('language') or 'Não indicado'}"
            )

            st.write(
                "**Hash SHA-256:**"
            )

            st.code(
                result.get(
                    "file_hash"
                )
                or "Não disponível"
            )


    except requests.exceptions.Timeout:

        st.error(
            "A importação excedeu o tempo limite definido."
        )


    except requests.exceptions.ConnectionError:

        st.error(
            "Não foi possível ligar ao backend FastAPI."
        )


    except requests.exceptions.RequestException as error:

        st.error(
            "Ocorreu um erro durante a comunicação com o backend."
        )

        st.code(
            str(error)
        )