import pandas as pd
import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"

st.title("🧹 Pré-processamento dos Dados")

st.markdown(
    """
    Nesta página é possível aplicar diferentes variantes de pré-processamento
    aos dados brutos previamente importados para a base de dados.
    """
)

variant_descriptions = {
    "minimal": """
    Variante A — mínima:
    lowercasing, normalização de espaços, substituição de URLs,
    anonimização de menções e deduplicação simples.
    """,
    "intermediate": """
    Variante B — intermédia:
    inclui a Variante A, tokenização, normalização de hashtags,
    tratamento de emojis, expansão de abreviações e redução de caracteres repetidos.
    """,
    "aggressive": """
    Variante C — agressiva:
    inclui a Variante B, remoção de pontuação selecionada,
    remoção de stopwords e stemming.
    """
}

try:
    datasets_response = requests.get(
        f"{API_BASE_URL}/datasets",
        timeout=30
    )

    if datasets_response.status_code != 200:
        st.error("Erro ao obter datasets.")
        st.code(datasets_response.text)
        st.stop()

    datasets = datasets_response.json()

    if not datasets:
        st.info("Ainda não existem datasets importados.")
        st.stop()

    dataset_options = {
        f"{dataset['id']} - {dataset['name']}": dataset["id"]
        for dataset in datasets
    }

    selected_dataset_label = st.selectbox(
        "Selecionar dataset",
        options=list(dataset_options.keys())
    )

    selected_dataset_id = dataset_options[selected_dataset_label]

    selected_variant = st.radio(
        "Selecionar variante de pré-processamento",
        options=["minimal", "intermediate", "aggressive"],
        format_func=lambda value: {
            "minimal": "Variante A — mínima",
            "intermediate": "Variante B — intermédia",
            "aggressive": "Variante C — agressiva"
        }[value]
    )

    st.markdown("### Operações incluídas")
    st.info(variant_descriptions[selected_variant])

    run_button = st.button("Executar pré-processamento")

    if run_button:
        run_response = requests.post(
            f"{API_BASE_URL}/preprocessing/datasets/{selected_dataset_id}/run",
            params={"variant": selected_variant},
            timeout=120
        )

        if run_response.status_code == 200:
            result = run_response.json()

            st.success("Pré-processamento executado com sucesso.")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Run ID", result["processing_run_id"])
            col2.metric("Posts totais", result["total_posts"])
            col3.metric("Posts processados", result["processed_posts"])
            col4.metric("Duplicados", result["duplicate_posts"])

        else:
            st.error("Erro ao executar pré-processamento.")
            st.code(run_response.text)

    st.divider()

    st.subheader("Execuções de pré-processamento")

    runs_response = requests.get(
        f"{API_BASE_URL}/preprocessing/datasets/{selected_dataset_id}/runs",
        timeout=30
    )

    if runs_response.status_code == 200:
        runs = runs_response.json()

        if not runs:
            st.info("Ainda não existem execuções para este dataset.")
        else:
            df_runs = pd.DataFrame(runs)

            st.dataframe(
                df_runs,
                use_container_width=True
            )

            run_options = {
                f"{run['id']} - {run['variant']} - {run['status']}": run["id"]
                for run in runs
            }

            selected_run_label = st.selectbox(
                "Selecionar execução para visualizar resultados",
                options=list(run_options.keys())
            )

            selected_run_id = run_options[selected_run_label]

            posts_response = requests.get(
                f"{API_BASE_URL}/preprocessing/runs/{selected_run_id}/posts",
                params={
                    "limit": 100,
                    "offset": 0
                },
                timeout=30
            )

            if posts_response.status_code == 200:
                processed_posts = posts_response.json()

                if processed_posts:
                    df_processed = pd.DataFrame(processed_posts)

                    st.subheader("Dados processados")

                    st.dataframe(
                        df_processed[
                            [
                                "post_id",
                                "variant",
                                "original_text",
                                "processed_text",
                                "emoji_count",
                                "word_count",
                                "has_url",
                                "has_mention",
                                "has_hashtag",
                                "is_duplicate"
                            ]
                        ],
                        use_container_width=True
                    )

                    st.subheader("Comparação: texto original vs texto processado")

                    st.dataframe(
                        df_processed[
                            [
                                "original_text",
                                "processed_text",
                                "applied_steps"
                            ]
                        ],
                        use_container_width=True
                    )

                    st.subheader("Métricas do processamento")

                    col1, col2, col3 = st.columns(3)

                    col1.metric(
                        "Média de palavras",
                        round(df_processed["word_count"].mean(), 2)
                    )

                    col2.metric(
                        "Total de emojis",
                        int(df_processed["emoji_count"].sum())
                    )

                    col3.metric(
                        "Duplicados",
                        int(df_processed["is_duplicate"].sum())
                    )

                    st.markdown("### Elementos sociais detetados")

                    social_metrics = {
                        "Com URL": int(df_processed["has_url"].sum()),
                        "Com menção": int(df_processed["has_mention"].sum()),
                        "Com hashtag": int(df_processed["has_hashtag"].sum())
                    }

                    df_social = pd.DataFrame(
                        list(social_metrics.items()),
                        columns=["Elemento", "Total"]
                    )

                    st.bar_chart(
                        df_social.set_index("Elemento")
                    )

                else:
                    st.info("Esta execução ainda não tem dados processados.")

            else:
                st.error("Erro ao obter dados processados.")
                st.code(posts_response.text)

    else:
        st.error("Erro ao obter execuções.")
        st.code(runs_response.text)

except requests.exceptions.ConnectionError:
    st.error(
        "Não foi possível ligar ao backend FastAPI. "
        "Confirme que está em execução em http://127.0.0.1:8000."
    )

except Exception as error:
    st.error(f"Erro inesperado: {error}")