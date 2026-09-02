"""
Ponto de entrada da API do sistema.

Este módulo cria e configura a aplicação FastAPI responsável por disponibilizar
os endpoints do sistema de recolha, armazenamento e preparação de dados afetivos.

Os endpoints encontram-se organizados em routers separados, de acordo com a
responsabilidade funcional de cada módulo da aplicação.
"""

from fastapi import FastAPI

from app.api.routes_datasets import router as datasets_router
from app.api.routes_preprocessing import router as preprocessing_router
from app.api.routes_affective import (
    router as affective_router
)


# Instância principal da aplicação FastAPI.
#
# O título definido neste ponto é utilizado na documentação automática da API,
# disponibilizada pelo FastAPI através das interfaces Swagger UI e ReDoc.
app = FastAPI(
    title="Sistema de Recolha e Preparação de Dados Afetivos"
)


# Regista os endpoints associados à gestão de conjuntos de dados.
#
# Este router deverá incluir operações como:
# - carregamento de ficheiros;
# - registo de datasets;
# - consulta de datasets;
# - consulta das publicações armazenadas.
app.include_router(datasets_router)


# Regista os endpoints associados ao módulo de pré-processamento.
#
# Este router deverá permitir iniciar execuções de pré-processamento,
# definir configurações e consultar os respetivos resultados e métricas.
app.include_router(preprocessing_router)


# Regista os endpoints associados ao módulo de enriquecimento afetivo.
#
# Este router deverá permitir executar o enriquecimento afetivo, consultar
# características extraídas e obter estatísticas agregadas.
app.include_router(affective_router)


@app.get("/health")
def health_check():
    """
    Verifica se a API se encontra disponível.

    Este endpoint pode ser utilizado para testes de conectividade, monitorização
    da aplicação ou validação da comunicação entre o frontend Streamlit e o
    backend FastAPI.

    Returns:
        dict: Estado atual da API.
    """
    return {"status": "ok"}