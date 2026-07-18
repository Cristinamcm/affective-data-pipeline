import pandas as pd
import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"


st.title("🧹 Pré-processamento dos Dados")

st.markdown(
    """
    Nesta página é possível configurar e executar um pipeline modular de
    pré-processamento sobre os dados brutos previamente importados.
    """
)


def get_datasets():
    response = requests.get(
        f"{API_BASE_URL}/datasets",
        timeout=30
    )

    if response.status_code != 200:
        st.error("Erro ao obter datasets.")
        st.code(response.text)
        st.stop()

    return response.json()


def get_presets():
    response = requests.get(
        f"{API_BASE_URL}/preprocessing/presets",
        timeout=30
    )

    if response.status_code != 200:
        st.error("Erro ao obter configurações de pré-processamento.")
        st.code(response.text)
        st.stop()

    return response.json()


def get_dataset_posts(dataset_id: int, limit: int = 5):
    response = requests.get(
        f"{API_BASE_URL}/datasets/{dataset_id}/posts",
        params={
            "limit": limit,
            "offset": 0
        },
        timeout=30
    )

    if response.status_code != 200:
        return []

    return response.json()


def get_processing_runs(dataset_id: int):
    response = requests.get(
        f"{API_BASE_URL}/preprocessing/datasets/{dataset_id}/runs",
        timeout=30
    )

    if response.status_code != 200:
        return []

    return response.json()


try:
    datasets = get_datasets()

    if not datasets:
        st.info("Ainda não existem datasets importados.")
        st.stop()

    presets_data = get_presets()

    supported_operations = presets_data["supported_operations"]
    presets = presets_data["presets"]

    dataset_options = {
        f"{dataset['id']} - {dataset['name']}": dataset["id"]
        for dataset in datasets
    }

    selected_dataset_label = st.selectbox(
        "Selecionar dataset",
        options=list(dataset_options.keys())
    )

    selected_dataset_id = dataset_options[selected_dataset_label]

    st.subheader("Amostra dos dados brutos")

    sample_posts = get_dataset_posts(
        dataset_id=selected_dataset_id,
        limit=5
    )

    if sample_posts:
        df_sample = pd.DataFrame(sample_posts)
        st.dataframe(
            df_sample[["id", "external_id", "original_text"]],
            use_container_width=True
        )
    else:
        st.warning("Não foi possível obter amostra dos dados brutos.")

    st.divider()

    st.subheader("Configuração do pipeline")

    preset_labels = {
        "minimal": "Mínima",
        "intermediate": "Intermédia",
        "aggressive": "Agressiva",
        "custom": "Personalizada"
    }

    preset_choice = st.selectbox(
        "Escolher configuração inicial",
        options=["minimal", "intermediate", "aggressive", "custom"],
        format_func=lambda value: preset_labels[value]
    )

    if preset_choice == "custom":
        base_config = {
            operation: False
            for operation in supported_operations
        }
    else:
        base_config = presets[preset_choice]

    configuration_name = st.text_input(
        "Nome da configuração/execução",
        value=preset_choice
    )

    st.markdown("### Operações disponíveis")

    with st.form("preprocessing_config_form"):
        st.markdown("#### Normalização básica")

        normalize_unicode = st.checkbox(
            supported_operations["normalize_unicode"],
            value=base_config.get("normalize_unicode", False)
        )

        lowercase = st.checkbox(
            supported_operations["lowercase"],
            value=base_config.get("lowercase", False)
        )

        normalize_spaces = st.checkbox(
            supported_operations["normalize_spaces"],
            value=base_config.get("normalize_spaces", False)
        )

        st.markdown("#### Privacidade e anonimização")

        replace_urls = st.checkbox(
            supported_operations["replace_urls"],
            value=base_config.get("replace_urls", False)
        )

        anonymize_mentions = st.checkbox(
            supported_operations["anonymize_mentions"],
            value=base_config.get("anonymize_mentions", False)
        )

        st.markdown("#### Elementos sociais e afetivos")

        extract_hashtags = st.checkbox(
            supported_operations["extract_hashtags"],
            value=base_config.get("extract_hashtags", False)
        )

        normalize_hashtags = st.checkbox(
            supported_operations["normalize_hashtags"],
            value=base_config.get("normalize_hashtags", False)
        )

        extract_emojis = st.checkbox(
            supported_operations["extract_emojis"],
            value=base_config.get("extract_emojis", False)
        )

        convert_emojis_to_text = st.checkbox(
            supported_operations["convert_emojis_to_text"],
            value=base_config.get("convert_emojis_to_text", False)
        )

        st.markdown("#### Redução de ruído textual")

        expand_abbreviations = st.checkbox(
            supported_operations["expand_abbreviations"],
            value=base_config.get("expand_abbreviations", False)
        )

        reduce_repeated_characters = st.checkbox(
            supported_operations["reduce_repeated_characters"],
            value=base_config.get("reduce_repeated_characters", False)
        )

        remove_special_characters = st.checkbox(
            supported_operations["remove_special_characters"],
            value=base_config.get("remove_special_characters", False)
        )

        remove_selected_punctuation = st.checkbox(
            supported_operations["remove_selected_punctuation"],
            value=base_config.get("remove_selected_punctuation", False)
        )

        st.markdown("#### Transformação linguística")

        tokenize = st.checkbox(
            supported_operations["tokenize"],
            value=base_config.get("tokenize", False)
        )

        remove_stopwords = st.checkbox(
            supported_operations["remove_stopwords"],
            value=base_config.get("remove_stopwords", False)
        )

        stemming = st.checkbox(
            supported_operations["stemming"],
            value=base_config.get("stemming", False)
        )

        lemmatization = st.checkbox(
            supported_operations["lemmatization"],
            value=base_config.get("lemmatization", False)
        )

        submitted = st.form_submit_button("Executar pré-processamento")

    config = {
        "normalize_unicode": normalize_unicode,
        "lowercase": lowercase,
        "normalize_spaces": normalize_spaces,
        "replace_urls": replace_urls,
        "anonymize_mentions": anonymize_mentions,
        "extract_hashtags": extract_hashtags,
        "normalize_hashtags": normalize_hashtags,
        "extract_emojis": extract_emojis,
        "convert_emojis_to_text": convert_emojis_to_text,
        "expand_abbreviations": expand_abbreviations,
        "reduce_repeated_characters": reduce_repeated_characters,
        "remove_special_characters": remove_special_characters,
        "remove_selected_punctuation": remove_selected_punctuation,
        "tokenize": tokenize,
        "remove_stopwords": remove_stopwords,
        "stemming": stemming,
        "lemmatization": lemmatization
    }

    if submitted:
        run_response = requests.post(
            f"{API_BASE_URL}/preprocessing/datasets/{selected_dataset_id}/run",
            json={
                "configuration_name": configuration_name,
                "config": config
            },
            timeout=180
        )

        if run_response.status_code == 200:
            result = run_response.json()

            st.success("Pré-processamento executado com sucesso.")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Run ID", result["processing_run_id"])
            col2.metric("Posts totais", result["total_posts"])
            col3.metric("Posts processados", result["processed_posts"])
            col4.metric("Duplicados", result["duplicate_posts"])

            st.metric(
                "Textos vazios após processamento",
                result["empty_after_processing"]
            )

        else:
            st.error("Erro ao executar pré-processamento.")
            st.code(run_response.text)

    st.divider()

    st.subheader("Execuções de pré-processamento")

    runs = get_processing_runs(selected_dataset_id)

    if not runs:
        st.info("Ainda não existem execuções de pré-processamento para este dataset.")
        st.stop()

    df_runs = pd.DataFrame(runs)

    st.dataframe(
        df_runs[
            [
                "id",
                "configuration_name",
                "total_posts",
                "processed_posts",
                "duplicate_posts",
                "empty_after_processing",
                "status",
                "started_at",
                "finished_at"
            ]
        ],
        use_container_width=True
    )

    run_options = {
        f"{run['id']} - {run['configuration_name']} - {run['status']}": run["id"]
        for run in runs
    }

    selected_run_label = st.selectbox(
        "Selecionar execução para visualizar resultados",
        options=list(run_options.keys())
    )

    selected_run_id = run_options[selected_run_label]

    summary_response = requests.get(
        f"{API_BASE_URL}/preprocessing/runs/{selected_run_id}/summary",
        timeout=30
    )

    posts_response = requests.get(
        f"{API_BASE_URL}/preprocessing/runs/{selected_run_id}/posts",
        params={
            "limit": 100,
            "offset": 0
        },
        timeout=30
    )

    if summary_response.status_code == 200:
        summary = summary_response.json()
        metrics = summary["metrics"]

        st.markdown("### Métricas da execução")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Registos", metrics["records"])
        col2.metric("Média tamanho original", round(metrics["avg_original_length"], 2))
        col3.metric("Média tamanho processado", round(metrics["avg_processed_length"], 2))
        col4.metric("Média palavras", round(metrics["avg_word_count"], 2))

        col5, col6, col7, col8 = st.columns(4)

        col5.metric("URLs detetados", metrics["total_urls"])
        col6.metric("Menções detetadas", metrics["total_mentions"])
        col7.metric("Hashtags detetadas", metrics["total_hashtags"])
        col8.metric("Emojis detetados", metrics["total_emojis"])

        social_metrics = pd.DataFrame(
            [
                {"Elemento": "Posts com URL", "Total": metrics["posts_with_url"]},
                {"Elemento": "Posts com menção", "Total": metrics["posts_with_mention"]},
                {"Elemento": "Posts com hashtag", "Total": metrics["posts_with_hashtag"]},
                {"Elemento": "Duplicados", "Total": metrics["duplicate_posts"]},
                {"Elemento": "Vazios após processamento", "Total": metrics["empty_after_processing"]}
            ]
        )

        st.markdown("### Indicadores do pipeline")
        st.bar_chart(social_metrics.set_index("Elemento"))

        st.markdown("### Configuração aplicada")
        st.json(summary["configuration_json"])

    else:
        st.error("Erro ao obter resumo da execução.")
        st.code(summary_response.text)

    if posts_response.status_code == 200:
        processed_posts = posts_response.json()

        if processed_posts:
            df_processed = pd.DataFrame(processed_posts)

            st.markdown("### Dados processados")

            st.dataframe(
                df_processed[
                    [
                        "post_id",
                        "original_text",
                        "processed_text",
                        "word_count",
                        "token_count",
                        "emoji_count",
                        "url_count",
                        "mention_count",
                        "hashtag_count",
                        "is_duplicate",
                        "is_empty_after_processing"
                    ]
                ],
                use_container_width=True
            )

            st.markdown("### Texto original vs texto processado")

            st.dataframe(
                df_processed[
                    [
                        "original_text",
                        "processed_text",
                        "tokens",
                        "emojis",
                        "hashtags",
                        "applied_steps"
                    ]
                ],
                use_container_width=True
            )

            st.download_button(
                label="Descarregar amostra processada em CSV",
                data=df_processed.to_csv(index=False).encode("utf-8"),
                file_name=f"processed_run_{selected_run_id}.csv",
                mime="text/csv"
            )

        else:
            st.info("Esta execução ainda não tem dados processados.")

    else:
        st.error("Erro ao obter posts processados.")
        st.code(posts_response.text)

except requests.exceptions.ConnectionError:
    st.error(
        "Não foi possível ligar ao backend FastAPI. "
        "Confirme que está em execução em http://127.0.0.1:8000."
    )

except Exception as error:
    st.error(f"Erro inesperado: {error}")