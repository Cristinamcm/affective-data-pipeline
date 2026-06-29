from pathlib import Path
import pandas as pd

from app.preprocessing.preprocessing_pipeline import preprocess_record


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