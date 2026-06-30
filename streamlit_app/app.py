from pathlib import Path

import pandas as pd
import requests
import streamlit as st


# URL base da API FastAPI responsável pelo pré-processamento dos dados
API_BASE_URL = "http://127.0.0.1:8000"

# Diretórios onde serão armazenados os ficheiros originais e processados
RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")

# Configuração inicial da página Streamlit
st.set_page_config(
    page_title="Sistema de Recolha e Preparação de Dados Afectivos",
    page_icon="💬",
    layout="wide"
)

# Titulo e descrição da aplicação
st.title("💬 Sistema de Recolha e Preparação de Dados Afectivos")
st.markdown(
    """
    Protótipo para recolha, pré-processamento e estruturação de dados afetivos a partir de conjuntos de dados de redes sociais.
    """
)

# Criação dos diretórios necessários, caso ainda não existam
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ============================
# Barra lateral da aplicação
# ============================

# Secção lateral para seleção ou upload do dataset
st.sidebar.header("Dataset Input")


# Permite ao utilizador carregar um ficheiro CSV através da interface
uploaded_file = st.sidebar.file_uploader(
    "Upload a CSV file",
    type=["csv"]
)

# Caso o utilizador carregue um ficheiro, este é guardado no diretório data/raw
if uploaded_file is not None:
    input_filename = uploaded_file.name
    input_path = RAW_DATA_DIR / input_filename

    # Escrita do ficheiro carregado no sistema de ficheiros local
    with open(input_path, "wb") as file:
        file.write(uploaded_file.getbuffer())

    st.sidebar.success(f"File uploaded: {input_filename}")

# Caso contrário, o utilizador pode indicar o nome de um ficheiro já existente em data/raw
else:
    input_filename = st.sidebar.text_input(
        "Or use an existing file in data/raw/",
        value="dev.csv"
    )

# Separador visual na barra lateral
st.sidebar.divider()

# Botão que inicia o processamento do dataset através da API
process_button = st.sidebar.button("Process Dataset")


# ============================
# Organização da interface em separadores
# ============================

# Criação de três separadores principais:
# 1. Pré-visualização do dataset original
# 2. Resultado do processamento
# 3. Visualização do dataset processado

tab1, tab2, tab3 = st.tabs(
    [
        "Dataset Preview",
        "Processing Result",
        "Processed Data"
    ]
)


# ============================
# Separador 1: Dataset Original
# ============================


with tab1:
    st.subheader("Original Dataset")

    # Caminho completo para o ficheiro de entrada
    input_path = RAW_DATA_DIR / input_filename

    # Verifica se o ficheiro indicado existe no diretório data/raw
    if input_path.exists():
        try:
            # Leitura do ficheiro CSV original
            df_original = pd.read_csv(input_path)

            # Apresentação das primeiras 20 linhas do dataset
            st.write("Preview of the original dataset:")
            st.dataframe(df_original.head(20), use_container_width=True)

            # Apresentação de métricas gerais sobre o dataset
            col1, col2, col3 = st.columns(3)
            col1.metric("Rows", len(df_original))
            col2.metric("Columns", len(df_original.columns))
            col3.metric("Selected file", input_filename)

            # Apresentação dos nomes das colunas existentes no dataset
            st.write("Columns:")
            st.code(", ".join(df_original.columns))

        except Exception as error:
            # Mensagem apresentada caso ocorra algum erro na leitura do CSV
            st.error(f"Error reading CSV file: {error}")

    else:
        # Mensagem informativa quando o ficheiro não existe
        st.info("Upload a CSV file or provide the name of an existing file in data/raw/.")

# ============================
# Separador 2: Resultado do Processamento
# ============================

with tab2:
    st.subheader("Processing Result")

    # O processamento só é executado quando o utilizador clica no botão lateral
    if process_button:
        try:
            # Pedido POST à API FastAPI para executar o pipeline de pré-processamento
            response = requests.post(
                f"{API_BASE_URL}/preprocessing/csv",
                params={"input_filename": input_filename},
                timeout=30
            )
            
            # Caso a resposta da API seja bem-sucedida
            if response.status_code == 200:
                result = response.json()

                st.success("Dataset processed successfully.")
                
                # Apresentação de métricas resultantes do processamento
                col1, col2 = st.columns(2)
                col1.metric("Total records", result["total_records"])
                col2.metric("Total columns", len(result["columns"]))

                # Caminho do ficheiro de entrada utilizado pela API
                st.write("Input path:")
                st.code(result["input_path"])

                # Caminho do ficheiro processado gerado pela API
                st.write("Output path:")
                st.code(result["output_path"])

                # Listagem das colunas existentes no ficheiro processado
                st.write("Generated columns:")
                st.code(", ".join(result["columns"]))

            else:
                # Mensagem apresentada quando a API responde com erro
                st.error("The API returned an error.")
                st.code(response.text)

        except requests.exceptions.ConnectionError:
            # Mensagem apresentada quando o frontend não consegue comunicar com o backend
            st.error(
                "Could not connect to the FastAPI backend. "
                "Make sure it is running on http://127.0.0.1:8000."
            )

        except Exception as error:
            # Tratamento genérico para outros erros inesperados
            st.error(f"Unexpected error: {error}")

    else:
        # Mensagem inicial antes do utilizador executar o processamento
        st.info("Click 'Process Dataset' in the sidebar to run the preprocessing pipeline.")

# ============================
# Separador 3: Dataset Processado
# ============================

with tab3:
    st.subheader("Processed Dataset")

    # Nome esperado para o ficheiro processado
    processed_filename = f"processed_{input_filename}"

    # Caminho completo para o ficheiro processado
    processed_path = PROCESSED_DATA_DIR / processed_filename

    # Verifica se já existe um ficheiro processado correspondente ao dataset selecionado
    if processed_path.exists():
        try:
            # Leitura do dataset processado
            df_processed = pd.read_csv(processed_path)

            # Apresentação das primeiras 20 linhas do dataset processado
            st.write("Preview of the processed dataset:")
            st.dataframe(df_processed.head(20), use_container_width=True)

            # Botão para descarregar o dataset processado em formato CSV
            st.download_button(
                label="Download processed CSV",
                data=df_processed.to_csv(index=False).encode("utf-8"),
                file_name=processed_filename,
                mime="text/csv"
            )

            # Caso exista a coluna cleaned_text, compara o texto original com o texto limpo
            if "cleaned_text" in df_processed.columns:
                st.subheader("Original Text vs Cleaned Text")

                columns_to_show = []

                # Inclui a coluna original text, caso exista no dataset
                if "text" in df_processed.columns:
                    columns_to_show.append("text")

                # Inclui sempre a coluna cleaned_text
                columns_to_show.append("cleaned_text")

                # Apresentação comparativa entre texto original e texto pré-processado
                st.dataframe(
                    df_processed[columns_to_show].head(20),
                    use_container_width=True
                )

            # Caso exista a coluna emoji_count, apresenta a distribuição da contagem de emojis
            if "emoji_count" in df_processed.columns:
                st.subheader("Emoji Count Distribution")
                st.bar_chart(df_processed["emoji_count"].value_counts().sort_index())


            # Caso exista a coluna language, apresenta a distribuição das línguas detectadas
            if "language" in df_processed.columns:
                st.subheader("Language Distribution")
                st.bar_chart(df_processed["language"].value_counts())

        except Exception as error:
            # Mensagem apresentada caso ocorra algum erro na leitura do ficheiro processado
            st.error(f"Error reading processed CSV file: {error}")

    else:
        # Mensagem apresentada quando ainda não existe ficheiro processado
        st.info("No processed file found yet. Process a dataset first.")