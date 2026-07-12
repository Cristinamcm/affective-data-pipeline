import pandas as pd
import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"

st.title("👀 Pré-visualização dos Dados")

st.markdown(
    """
    Nesta página é possível consultar os datasets já importados e visualizar
    os dados brutos armazenados na base de dados.
    """
)

try:
    datasets_response = requests.get(
        f"{API_BASE_URL}/datasets",
        timeout=30
    )

    if datasets_response.status_code == 200:
        datasets = datasets_response.json()

        if not datasets:
            st.info("Ainda não existem datasets guardados na base de dados.")
        else:
            dataset_options = {
                f"{dataset['id']} - {dataset['name']}": dataset["id"]
                for dataset in datasets
            }

            selected_dataset_label = st.selectbox(
                "Selecionar dataset",
                options=list(dataset_options.keys())
            )

            selected_dataset_id = dataset_options[selected_dataset_label]

            dataset_response = requests.get(
                f"{API_BASE_URL}/datasets/{selected_dataset_id}",
                timeout=30
            )

            posts_response = requests.get(
                f"{API_BASE_URL}/datasets/{selected_dataset_id}/posts",
                params={
                    "limit": 100,
                    "offset": 0
                },
                timeout=30
            )

            if dataset_response.status_code == 200:
                dataset = dataset_response.json()

                st.subheader("Informação do dataset")

                col1, col2, col3 = st.columns(3)

                col1.metric("ID", dataset["id"])
                col2.metric("Registos", dataset["rows_count"])
                col3.metric("Fonte", dataset["source"])

                st.write("Nome:")
                st.code(dataset["name"])

                st.write("Ficheiro original:")
                st.code(dataset["original_filename"])

                st.write("Coluna de ID original:")
                st.code(dataset["id_column"] or "Gerada automaticamente")

                st.write("Coluna de texto original:")
                st.code(dataset["text_column"])

            else:
                st.error("Erro ao obter informação do dataset.")
                st.code(dataset_response.text)

            if posts_response.status_code == 200:
                posts = posts_response.json()

                st.subheader("Dados brutos armazenados")

                if posts:
                    df_posts = pd.DataFrame(posts)

                    st.dataframe(
                        df_posts[
                            [
                                "id",
                                "dataset_id",
                                "external_id",
                                "original_text",
                                "inserted_at"
                            ]
                        ],
                        use_container_width=True
                    )
                else:
                    st.info("Este dataset ainda não tem posts associados.")

            else:
                st.error("Erro ao obter posts do dataset.")
                st.code(posts_response.text)

    else:
        st.error("Erro ao obter lista de datasets.")
        st.code(datasets_response.text)

except requests.exceptions.ConnectionError:
    st.error(
        "Não foi possível ligar ao backend FastAPI. "
        "Confirme que está em execução em http://127.0.0.1:8000."
    )

except Exception as error:
    st.error(f"Erro inesperado: {error}")