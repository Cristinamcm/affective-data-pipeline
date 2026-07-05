from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.preprocessing_service import (
    preprocess_csv,
    preprocess_csv_and_store
)

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


@router.post("/csv/store")
def preprocess_dataset_and_store(
    input_filename: str = Query(default="dev.csv"),
    dataset_name: str = Query(default="Development dataset"),
    source: str = Query(default="csv"),
    db: Session = Depends(get_db)
):
    input_path = f"data/raw/{input_filename}"
    output_path = f"data/processed/processed_{input_filename}"

    result = preprocess_csv_and_store(
        db=db,
        input_path=input_path,
        output_path=output_path,
        dataset_name=dataset_name,
        source=source
    )

    return result