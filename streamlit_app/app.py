from pathlib import Path

import pandas as pd
import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"

RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")


st.set_page_config(
    page_title="Affective Data Pipeline",
    page_icon="💬",
    layout="wide"
)


st.title("💬 Affective Data Pipeline")
st.markdown(
    """
    Prototype for collecting, preprocessing and structuring affective data 
    from social media datasets.
    """
)


RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)


st.sidebar.header("Dataset Input")

uploaded_file = st.sidebar.file_uploader(
    "Upload a CSV file",
    type=["csv"]
)


if uploaded_file is not None:
    input_filename = uploaded_file.name
    input_path = RAW_DATA_DIR / input_filename

    with open(input_path, "wb") as file:
        file.write(uploaded_file.getbuffer())

    st.sidebar.success(f"File uploaded: {input_filename}")

else:
    input_filename = st.sidebar.text_input(
        "Or use an existing file in data/raw/",
        value="dev.csv"
    )


st.sidebar.divider()

process_button = st.sidebar.button("Process Dataset")


tab1, tab2, tab3 = st.tabs(
    [
        "Dataset Preview",
        "Processing Result",
        "Processed Data"
    ]
)


with tab1:
    st.subheader("Original Dataset")

    input_path = RAW_DATA_DIR / input_filename

    if input_path.exists():
        try:
            df_original = pd.read_csv(input_path)

            st.write("Preview of the original dataset:")
            st.dataframe(df_original.head(20), use_container_width=True)

            col1, col2, col3 = st.columns(3)
            col1.metric("Rows", len(df_original))
            col2.metric("Columns", len(df_original.columns))
            col3.metric("Selected file", input_filename)

            st.write("Columns:")
            st.code(", ".join(df_original.columns))

        except Exception as error:
            st.error(f"Error reading CSV file: {error}")

    else:
        st.info("Upload a CSV file or provide the name of an existing file in data/raw/.")


with tab2:
    st.subheader("Processing Result")

    if process_button:
        try:
            response = requests.post(
                f"{API_BASE_URL}/preprocessing/csv",
                params={"input_filename": input_filename},
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                st.success("Dataset processed successfully.")

                col1, col2 = st.columns(2)
                col1.metric("Total records", result["total_records"])
                col2.metric("Total columns", len(result["columns"]))

                st.write("Input path:")
                st.code(result["input_path"])

                st.write("Output path:")
                st.code(result["output_path"])

                st.write("Generated columns:")
                st.code(", ".join(result["columns"]))

            else:
                st.error("The API returned an error.")
                st.code(response.text)

        except requests.exceptions.ConnectionError:
            st.error(
                "Could not connect to the FastAPI backend. "
                "Make sure it is running on http://127.0.0.1:8000."
            )

        except Exception as error:
            st.error(f"Unexpected error: {error}")

    else:
        st.info("Click 'Process Dataset' in the sidebar to run the preprocessing pipeline.")


with tab3:
    st.subheader("Processed Dataset")

    processed_filename = f"processed_{input_filename}"
    processed_path = PROCESSED_DATA_DIR / processed_filename

    if processed_path.exists():
        try:
            df_processed = pd.read_csv(processed_path)

            st.write("Preview of the processed dataset:")
            st.dataframe(df_processed.head(20), use_container_width=True)

            st.download_button(
                label="Download processed CSV",
                data=df_processed.to_csv(index=False).encode("utf-8"),
                file_name=processed_filename,
                mime="text/csv"
            )

            if "cleaned_text" in df_processed.columns:
                st.subheader("Original Text vs Cleaned Text")

                columns_to_show = []

                if "text" in df_processed.columns:
                    columns_to_show.append("text")

                columns_to_show.append("cleaned_text")

                st.dataframe(
                    df_processed[columns_to_show].head(20),
                    use_container_width=True
                )

            if "emoji_count" in df_processed.columns:
                st.subheader("Emoji Count Distribution")
                st.bar_chart(df_processed["emoji_count"].value_counts().sort_index())

            if "language" in df_processed.columns:
                st.subheader("Language Distribution")
                st.bar_chart(df_processed["language"].value_counts())

        except Exception as error:
            st.error(f"Error reading processed CSV file: {error}")

    else:
        st.info("No processed file found yet. Process a dataset first.")