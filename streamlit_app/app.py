"""
Página inicial da aplicação Streamlit.

Este módulo configura a interface principal do protótipo e apresenta
ao utilizador uma descrição geral das funcionalidades disponíveis.

As restantes funcionalidades estão organizadas em páginas específicas,
acessíveis através do menu lateral disponibilizado pelo Streamlit.
"""

import streamlit as st

# Define as configurações gerais da aplicação Streamlit.
#
# Esta função deve ser executada antes de outros componentes visuais da página.
st.set_page_config(
    # Título apresentado no separador do navegador.
    page_title="Sistema de Recolha e Preparação de Dados Afetivos",
    # Ícone apresentado no separador do navegador.
    page_icon="💬",
    # Utiliza a largura disponível da janela, permitindo apresentar
    # tabelas e métricas com maior espaço horizontal.    
    layout="wide"
)

# Título principal apresentado na página inicial.
st.title("Sistema de Recolha e Preparação de Dados Afetivos")

# Apresenta uma descrição resumida do objetivo do protótipo.
st.markdown(
    """
    Este protótipo permite importar conjuntos de dados públicos, preservar
    os dados originais, aplicar operações configuráveis de pré-processamento
    e preparar publicações, comentários e outros conteúdos provenientes
    de redes sociais para posterior análise afetiva.
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