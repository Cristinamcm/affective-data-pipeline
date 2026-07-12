from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from pathlib import Path
import pandas as pd
from fastapi import HTTPException

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
    text_column: str = Query(default="text"),
    id_column: str | None = Query(default=None),
    label_column: str | None = Query(default=None),
    db: Session = Depends(get_db)
):
    input_path = f"data/raw/{input_filename}"
    output_path = f"data/processed/processed_{input_filename}"

    result = preprocess_csv_and_store(
        db=db,
        input_path=input_path,
        output_path=output_path,
        dataset_name=dataset_name,
        source=source,
        text_column=text_column,
        id_column=id_column,
        label_column=label_column
    )

    return result

@router.get("/csv/preview")
def preview_csv(
    input_filename: str = Query(...)
):
    input_path = Path("data/raw") / input_filename

    if not input_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {input_path}"
        )

    df = pd.read_csv(input_path)

    preview_df = df.head(10)

    return {
        "input_path": str(input_path),
        "rows": len(df),
        "columns": list(df.columns),
        "preview": preview_df.to_dict(orient="records")
    }