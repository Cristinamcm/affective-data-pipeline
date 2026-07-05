from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.preprocessing.preprocessing_pipeline import preprocess_record
from app.repositories.post_repository import (
    create_dataset,
    create_post_with_processed_data,
    create_processing_run,
    finish_processing_run
)


def preprocess_csv(input_path: str, output_path: str):
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_file)

    records = df.to_dict(orient="records")
    processed_records = [preprocess_record(record) for record in records]

    processed_df = pd.DataFrame(processed_records)
    processed_df.to_csv(output_file, index=False)

    return {
        "input_path": str(input_file),
        "output_path": str(output_file),
        "total_records": len(processed_df),
        "columns": list(processed_df.columns)
    }


def preprocess_csv_and_store(
    db: Session,
    input_path: str,
    output_path: str,
    dataset_name: str,
    source: str = "csv"
):
    input_file = Path(input_path)
    output_file = Path(output_path)

    processing_run = create_processing_run(
        db=db,
        input_filename=input_file.name
    )

    try:
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        output_file.parent.mkdir(parents=True, exist_ok=True)

        df = pd.read_csv(input_file)

        dataset = create_dataset(
            db=db,
            name=dataset_name,
            source=source,
            original_filename=input_file.name,
            rows_count=len(df)
        )

        records = df.to_dict(orient="records")
        processed_records = []

        for record in records:
            processed_record = preprocess_record(record)
            processed_records.append(processed_record)

            create_post_with_processed_data(
                db=db,
                dataset_id=dataset.id,
                record=record,
                processed_record=processed_record
            )

        processed_df = pd.DataFrame(processed_records)
        processed_df.to_csv(output_file, index=False)

        finish_processing_run(
            db=db,
            processing_run=processing_run,
            dataset_id=dataset.id,
            output_filename=output_file.name,
            total_records=len(processed_df),
            status="finished"
        )

        return {
            "dataset_id": dataset.id,
            "processing_run_id": processing_run.id,
            "input_path": str(input_file),
            "output_path": str(output_file),
            "total_records": len(processed_df),
            "columns": list(processed_df.columns),
            "stored_in_database": True
        }

    except Exception as error:
        finish_processing_run(
            db=db,
            processing_run=processing_run,
            dataset_id=None,
            output_filename=output_file.name,
            total_records=0,
            status="failed",
            error_message=str(error)
        )

        raise error