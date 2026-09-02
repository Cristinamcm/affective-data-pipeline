"""
Página inicial da aplicação Streamlit.

Este módulo configura a interface principal do protótipo e apresenta
ao utilizador uma descrição geral das funcionalidades disponíveis.

As restantes funcionalidades estão organizadas em páginas específicas,
acessíveis através do menu lateral disponibilizado pelo Streamlit.
"""

import streamlit as st

# =============================================================================
# CONFIGURAÇÃO GERAL
# =============================================================================

st.set_page_config(
    page_title="Sistema de Recolha e Preparação de Dados Afetivos",
    page_icon="💬",
    layout="wide"
)


# =============================================================================
# PÁGINA INICIAL
# =============================================================================

def pagina_inicial():
    """
    Apresenta a página inicial do protótipo.
    """

    st.title(
        "💬 Sistema de Recolha e Preparação de Dados Afetivos"
    )

    st.markdown(
        """
        Este protótipo permite realizar a **recolha, preparação, estruturação
        e enriquecimento de dados afetivos provenientes de redes sociais
        e conjuntos de dados públicos**.

        O sistema foi concebido através de uma arquitetura modular, permitindo
        aplicar diferentes operações de preparação de acordo com as
        características dos dados em análise.
        """
    )

    st.divider()

    # -------------------------------------------------------------------------
    # FLUXO PRINCIPAL
    # -------------------------------------------------------------------------

    st.subheader(
        "Fluxo de utilização"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(
            """
            ### 📥 1. Recolha de Dados

            Importação de conjuntos de dados e definição do mapeamento das
            colunas relevantes.

            São preservados os dados originais e os respetivos metadados.
            """
        )

    with col2:

        st.markdown(
            """
            ### 🔎 2. Pré-visualização

            Consulta dos dados brutos armazenados antes da aplicação de
            qualquer transformação.

            Permite verificar os textos, identificadores e rótulos originais.
            """
        )

    with col3:

        st.markdown(
            """
            ### ⚙️ 3. Pré-processamento

            Configuração de um pipeline modular através da seleção individual
            das operações de preparação a aplicar aos dados.
            """
        )

    col4, col5 = st.columns(2)

    with col4:

        st.markdown(
            """
            ### 📊 4. Dados Processados e Métricas

            Consulta dos resultados produzidos pelo pipeline, das etapas
            executadas e das métricas de qualidade e desempenho.
            """
        )

    with col5:

        st.markdown(
            """
            ### 💬 5. Enriquecimento Afetivo

            Identificação e estruturação de elementos potencialmente relevantes
            para posterior análise afetiva, como emojis, hashtags e outros
            indicadores textuais.
            """
        )

    st.divider()

    # -------------------------------------------------------------------------
    # FLUXO CONCEPTUAL
    # -------------------------------------------------------------------------

    st.subheader(
        "Pipeline do sistema"
    )

    st.markdown(
        """
        O fluxo implementado pelo protótipo segue, de forma simplificada,
        a seguinte sequência:
        """
    )

    st.code(
        """
Recolha de Dados
        ↓
Armazenamento dos Dados Brutos
        ↓
Pré-processamento Configurável
        ↓
Armazenamento dos Dados Processados
        ↓
Métricas e Avaliação do Pipeline
        ↓
Enriquecimento Afetivo
        ↓
Dados Estruturados para Análise Afetiva
        """,
        language=None
    )

    st.info(
        "Utilize o menu lateral para aceder aos diferentes módulos "
        "do protótipo."
    )


# =============================================================================
# DEFINIÇÃO DAS PÁGINAS
# =============================================================================

inicio = st.Page(
    pagina_inicial,
    title="Página Inicial",
    icon="🏠",
    default=True
)


recolha_dados = st.Page(
    "pages/1_recolha_de_dados.py",
    title="Recolha de Dados",
    icon="📥"
)


pre_visualizacao = st.Page(
    "pages/2_pre_visualizacao_dados.py",
    title="Pré-visualização dos Dados",
    icon="🔎"
)


pre_processamento = st.Page(
    "pages/3_pre_processamento.py",
    title="Pré-processamento",
    icon="⚙️"
)


dados_processados = st.Page(
    "pages/4_dados_processados.py",
    title="Dados Processados e Métricas",
    icon="📊"
)


enriquecimento_afetivo = st.Page(
    "pages/5_enriquecimento_afetivo.py",
    title="Enriquecimento Afetivo",
    icon="💬"
)


# =============================================================================
# NAVEGAÇÃO
# =============================================================================

navigation = st.navigation(
    {
        "Início": [
            inicio
        ],

        "Dados": [
            recolha_dados,
            pre_visualizacao
        ],

        "Preparação": [
            pre_processamento,
            dados_processados
        ],

        "Análise Afetiva": [
            enriquecimento_afetivo
        ]
    }
)


# Executa a página atualmente selecionada.
navigation.run()