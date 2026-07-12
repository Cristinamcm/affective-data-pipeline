from fastapi import FastAPI

from app.api.routes_datasets import router as datasets_router

app = FastAPI(
    title="Sistema de Recolha e Preparação de Dados Afetivos"
)

app.include_router(datasets_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}