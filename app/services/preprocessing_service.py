import pandas as pd
from app.preprocessing.preprocessing_pipeline import preprocess_record


def preprocess_csv(input_path: str, output_path: str):
    df = pd.read_csv(input_path)

    records = df.to_dict(orient="records")
    processed_records = [preprocess_record(record) for record in records]

    processed_df = pd.DataFrame(processed_records)
    processed_df.to_csv(output_path, index=False)

    return {
        "input_path": input_path,
        "output_path": output_path,
        "total_records": len(processed_df),
        "columns": list(processed_df.columns)
    }