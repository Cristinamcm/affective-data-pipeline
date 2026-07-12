from pathlib import Path

import pandas as pd
import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"
RAW_DATA_DIR = Path("data/raw")

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

st.title("📥 Recolha de Dados")

st.markdown(
    """
    Nesta página é possível carregar datasets públicos em formato CSV,
    visualizar uma amostra inicial dos dados e mapear as colunas relevantes
    para o modelo interno do sistema.
    """
)

uploaded_file = st.file_uploader(
    "Carregar ficheiro CSV",
    type=["csv"]
)

if uploaded_file is not None:
    input_filename = uploaded_file.name
    input_path = RAW_DATA_DIR / input_filename

    with open(input_path, "wb") as file:
        file.write(uploaded_file.getbuffer())

    st.success(f"Ficheiro carregado com sucesso: {input_filename}")

    try:
        preview_response = requests.get(
            f"{API_BASE_URL}/datasets/csv/preview",
            params={"input_filename": input_filename},
            timeout=30
        )

        if preview_response.status_code == 200:
            preview_data = preview_response.json()

            st.subheader("Pré-visualização do dataset")
            st.dataframe(
                pd.DataFrame(preview_data["preview"]),
                use_container_width=True
            )

            st.write("Colunas disponíveis:")
            st.code(", ".join(preview_data["columns"]))

            st.metric("Número total de linhas", preview_data["rows_count"])

            st.subheader("Informação do dataset")

            dataset_name = st.text_input(
                "Nome do dataset",
                value=input_filename.replace(".csv", "")
            )

            source = st.text_input(
                "Fonte do dataset",
                value="Kaggle"
            )

            st.subheader("Mapeamento de colunas")

            available_columns = preview_data["columns"]

            id_column = st.selectbox(
                "Coluna de identificador externo",
                options=["Nenhuma"] + available_columns
            )

            text_column = st.selectbox(
                "Coluna que contém o texto/post",
                options=available_columns
            )

            id_column = None if id_column == "Nenhuma" else id_column

            import_button = st.button("Guardar dataset na base de dados")

            if import_button:
                import_response = requests.post(
                    f"{API_BASE_URL}/datasets/import-csv",
                    params={
                        "input_filename": input_filename,
                        "dataset_name": dataset_name,
                        "source": source,
                        "id_column": id_column,
                        "text_column": text_column
                    },
                    timeout=60
                )

                if import_response.status_code == 200:
                    result = import_response.json()

                    st.success("Dataset guardado com sucesso na base de dados.")

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Dataset ID", result["dataset_id"])
                    col2.metric("Total de registos", result["rows_count"])
                    col3.metric("Fonte", result["source"])

                    st.write("Coluna de ID:")
                    st.code(result["id_column"] or "Gerada automaticamente")

                    st.write("Coluna de texto:")
                    st.code(result["text_column"])

                else:
                    st.error("Erro ao guardar dataset na base de dados.")
                    st.code(import_response.text)

        else:
            st.error("Erro ao obter pré-visualização do ficheiro.")
            st.code(preview_response.text)

    except requests.exceptions.ConnectionError:
        st.error(
            "Não foi possível ligar ao backend FastAPI. "
            "Confirme que está em execução em http://127.0.0.1:8000."
        )

    except Exception as error:
        st.error(f"Erro inesperado: {error}")

else:
    st.info("Carregue um ficheiro CSV para iniciar a recolha de dados.")