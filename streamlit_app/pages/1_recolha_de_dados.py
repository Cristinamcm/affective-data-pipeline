"""
Página de recolha e importação de dados.

Esta página permite ao utilizador:

1. selecionar um ficheiro CSV;
2. guardar o ficheiro na área de armazenamento bruto;
3. solicitar ao backend uma pré-visualização dos dados;
4. consultar as colunas disponíveis;
5. mapear a coluna de texto e a coluna identificadora;
6. importar o dataset para a base de dados.

O frontend Streamlit não cria diretamente os registos Dataset e Post.
Essa operação é delegada ao backend FastAPI através de pedidos HTTP.
"""

import os
from pathlib import Path

import pandas as pd
import requests
import streamlit as st


# Endereço base da API FastAPI.
#
# A variável de ambiente API_BASE_URL permite utilizar endereços diferentes
# em desenvolvimento, testes ou produção. Quando não está definida, é utilizado
# o backend local.
API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "http://127.0.0.1:8000"
)


# Diretório destinado ao armazenamento dos ficheiros na sua forma original.
#
# O caminho é relativo ao diretório a partir do qual a aplicação é executada.
RAW_DATA_DIR = Path("data/raw")


# Garante que o diretório existe antes de tentar guardar um ficheiro.
RAW_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# Título e descrição funcional da página.
st.title("Recolha de Dados")

st.markdown(
    """
    Nesta página é possível carregar datasets públicos em formato CSV,
    visualizar uma amostra inicial dos dados e mapear as colunas relevantes
    para o modelo interno do sistema.
    """
)


# Componente que permite ao utilizador selecionar um ficheiro CSV
# existente no seu computador.
uploaded_file = st.file_uploader(
    "Carregar ficheiro CSV",
    type=["csv"]
)


# O restante conteúdo da página apenas é apresentado quando existe
# um ficheiro selecionado.
if uploaded_file is not None:

    # Mantém apenas o nome final do ficheiro.
    #
    # A utilização de Path(...).name evita que componentes de caminho
    # presentes no nome fornecido tentem guardar o ficheiro fora de data/raw.
    input_filename = Path(uploaded_file.name).name

    # Constrói o caminho em que o ficheiro bruto será armazenado.
    input_path = RAW_DATA_DIR / input_filename

    try:
        # Guarda os bytes recebidos no diretório de dados brutos.
        #
        # O modo "wb" permite escrever o conteúdo binário do ficheiro.
        # Caso já exista um ficheiro com o mesmo nome, este será substituído.
        with input_path.open("wb") as file:
            file.write(uploaded_file.getbuffer())

        st.success(
            f"Ficheiro carregado com sucesso: {input_filename}"
        )

        # Solicita ao backend uma pré-visualização do CSV.
        #
        # O backend recebe apenas o nome do ficheiro porque, na arquitetura
        # atual, o Streamlit e o FastAPI partilham o diretório data/raw.
        preview_response = requests.get(
            f"{API_BASE_URL}/datasets/csv/preview",
            params={
                "input_filename": input_filename
            },
            timeout=30
        )

        if preview_response.status_code == 200:
            preview_data = preview_response.json()

            # -----------------------------------------------------------------
            # Pré-visualização dos dados
            # -----------------------------------------------------------------

            st.subheader("Pré-visualização do dataset")

            # Converte os registos JSON recebidos do backend num DataFrame,
            # facilitando a sua apresentação através do Streamlit.
            st.dataframe(
                pd.DataFrame(preview_data["preview"]),
                use_container_width=True
            )

            st.write("Colunas disponíveis:")

            # Apresenta os nomes das colunas num bloco de código para facilitar
            # a sua leitura, especialmente quando existem muitas colunas.
            st.code(
                ", ".join(preview_data["columns"])
            )

            # Apresenta o número de linhas identificado pelo backend.
            st.metric(
                "Número total de linhas",
                preview_data["rows_count"]
            )

            # -----------------------------------------------------------------
            # Metadados do dataset
            # -----------------------------------------------------------------

            st.subheader("Informação do dataset")

            # Sugere como nome do dataset o nome do ficheiro sem a extensão.
            dataset_name = st.text_input(
                "Nome do dataset",
                value=Path(input_filename).stem
            )

            # Permite identificar a origem do dataset.
            source = st.text_input(
                "Fonte do dataset",
                value="Kaggle"
            )

            # -----------------------------------------------------------------
            # Mapeamento das colunas
            # -----------------------------------------------------------------

            st.subheader("Mapeamento de colunas")

            available_columns = preview_data["columns"]

            # A coluna identificadora é opcional. Quando não é selecionada,
            # o backend gera identificadores sequenciais para as publicações.
            id_column_option = st.selectbox(
                "Coluna de identificador externo",
                options=["Nenhuma"] + available_columns
            )

            # A coluna textual é obrigatória porque é utilizada para preencher
            # o campo original_text do modelo Post.
            text_column = st.selectbox(
                "Coluna que contém o texto/publicação",
                options=available_columns
            )

            # Converte a opção visual "Nenhuma" no valor Python None.
            id_column = (
                None
                if id_column_option == "Nenhuma"
                else id_column_option
            )

            # Botão utilizado para confirmar a importação do dataset.
            import_button = st.button(
                "Guardar dataset na base de dados",
                type="primary"
            )

            if import_button:
                # Remove espaços no início e no fim dos campos introduzidos.
                normalized_dataset_name = dataset_name.strip()
                normalized_source = source.strip()

                # Valida os metadados antes de enviar o pedido ao backend.
                if not normalized_dataset_name:
                    st.error(
                        "O nome do dataset não pode estar vazio."
                    )

                elif not normalized_source:
                    st.error(
                        "A fonte do dataset não pode estar vazia."
                    )

                else:
                    try:
                        # Solicita ao backend a importação do ficheiro.
                        #
                        # O backend volta a ler o CSV, valida as colunas e cria:
                        # - um registo Dataset;
                        # - um registo Post por cada linha do ficheiro.
                        import_response = requests.post(
                            f"{API_BASE_URL}/datasets/import-csv",
                            params={
                                "input_filename": input_filename,
                                "dataset_name": normalized_dataset_name,
                                "source": normalized_source,
                                "id_column": id_column,
                                "text_column": text_column
                            },
                            timeout=60
                        )

                        if import_response.status_code == 200:
                            result = import_response.json()

                            st.success(
                                "Dataset guardado com sucesso "
                                "na base de dados."
                            )

                            # Apresenta as principais propriedades do dataset
                            # criado através de três métricas.
                            col1, col2, col3 = st.columns(3)

                            col1.metric(
                                "Dataset ID",
                                result["dataset_id"]
                            )

                            col2.metric(
                                "Total de registos",
                                result["rows_count"]
                            )

                            col3.metric(
                                "Fonte",
                                result["source"]
                            )

                            st.write("Coluna de ID:")

                            st.code(
                                result["id_column"]
                                or "Gerada automaticamente"
                            )

                            st.write("Coluna de texto:")

                            st.code(
                                result["text_column"]
                            )

                        else:
                            # Apresenta ao utilizador o detalhe devolvido
                            # pelo backend quando a importação falha.
                            st.error(
                                "Erro ao guardar o dataset "
                                "na base de dados."
                            )

                            try:
                                error_detail = import_response.json().get(
                                    "detail",
                                    import_response.text
                                )
                            except ValueError:
                                error_detail = import_response.text

                            st.code(str(error_detail))

                    except requests.exceptions.Timeout:
                        st.error(
                            "O tempo limite da importação foi excedido. "
                            "O ficheiro poderá ser demasiado grande ou "
                            "o backend poderá estar sobrecarregado."
                        )

                    except requests.exceptions.ConnectionError:
                        st.error(
                            "Não foi possível ligar ao backend FastAPI. "
                            f"Confirme que está em execução em {API_BASE_URL}."
                        )

                    except requests.exceptions.RequestException as error:
                        st.error(
                            "Ocorreu um erro durante a comunicação "
                            "com o backend."
                        )
                        st.code(str(error))

        else:
            st.error(
                "Erro ao obter a pré-visualização do ficheiro."
            )

            try:
                error_detail = preview_response.json().get(
                    "detail",
                    preview_response.text
                )
            except ValueError:
                error_detail = preview_response.text

            st.code(str(error_detail))

    except requests.exceptions.Timeout:
        st.error(
            "O backend demorou demasiado tempo a gerar "
            "a pré-visualização do ficheiro."
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

    except OSError as error:
        # Trata erros relacionados com a escrita do ficheiro,
        # como permissões insuficientes ou diretório indisponível.
        st.error(
            "Não foi possível guardar o ficheiro na área "
            "de armazenamento bruto."
        )
        st.code(str(error))

    except Exception as error:
        # Proteção final para erros não previstos.
        #
        # Numa versão de produção, o detalhe técnico deve ser registado
        # através de logging e não necessariamente apresentado ao utilizador.
        st.error(
            f"Erro inesperado: {error}"
        )

else:
    # Mensagem apresentada antes de o utilizador selecionar um ficheiro.
    st.info(
        "Carregue um ficheiro CSV para iniciar a recolha de dados."
    )