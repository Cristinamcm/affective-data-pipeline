import streamlit as st

st.set_page_config(
    page_title="Sistema de Recolha e Preparação de Dados Afetivos",
    page_icon="💬",
    layout="wide"
)

st.title("💬 Sistema de Recolha e Preparação de Dados Afetivos")

st.markdown(
    """
    Este protótipo permite importar datasets públicos, armazenar dados brutos,
    aplicar etapas de pré-processamento e preparar dados afetivos provenientes
    de fontes como redes sociais, comentários ou tweets.
    """
)

st.markdown(
    """
    Utilize o menu lateral para navegar entre as páginas:

    - **Recolha de Dados**
    - **Pré-visualização dos Dados**
    - **Pré-processamento**
    - **Dados Processados**
    """
)