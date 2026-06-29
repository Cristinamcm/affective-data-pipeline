from fastapi import APIRouter, Query
from app.services.preprocessing_service import preprocess_csv

router = APIRouter(prefix="/preprocessing", tags=["Preprocessing"])


@router.post("/csv")
def preprocess_dataset(
    input_filename: str = Query(default="dev.csv")
):
    input_path = f"data/raw/{input_filename}"
    output_path = f"data/processed/processed_{input_filename}"

    result = preprocess_csv(
        input_path=input_path,
        output_path=output_path
    )

    return result