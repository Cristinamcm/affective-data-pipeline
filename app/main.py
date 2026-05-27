from fastapi import FastAPI
from app.api.routes_preprocessing import router as preprocessing_router

app = FastAPI(title="Affective Data Pipeline API")

app.include_router(preprocessing_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}