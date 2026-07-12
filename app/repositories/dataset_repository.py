import pandas as pd
from sqlalchemy.orm import Session

from app.models.models import Dataset, Post


def create_dataset_with_posts(
    db: Session,
    name: str,
    source: str,
    original_filename: str,
    id_column: str | None,
    text_column: str,
    df: pd.DataFrame
) -> Dataset:
    dataset = Dataset(
        name=name,
        source=source,
        original_filename=original_filename,
        rows_count=len(df),
        id_column=id_column,
        text_column=text_column
    )

    db.add(dataset)
    db.flush()

    for index, row in df.iterrows():
        if id_column and id_column in df.columns:
            external_id = row[id_column]
        else:
            external_id = index + 1

        original_text = row[text_column]

        if pd.isna(original_text):
            original_text = ""

        post = Post(
            dataset_id=dataset.id,
            external_id=str(external_id),
            original_text=str(original_text)
        )

        db.add(post)

    db.commit()
    db.refresh(dataset)

    return dataset


def get_datasets(db: Session):
    return (
        db.query(Dataset)
        .order_by(Dataset.created_at.desc())
        .all()
    )


def get_dataset_by_id(db: Session, dataset_id: int):
    return (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id)
        .first()
    )


def get_posts_by_dataset(
    db: Session,
    dataset_id: int,
    limit: int = 100,
    offset: int = 0
):
    return (
        db.query(Post)
        .filter(Post.dataset_id == dataset_id)
        .order_by(Post.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )