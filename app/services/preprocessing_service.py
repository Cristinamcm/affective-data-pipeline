from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.preprocessing.preprocessing_pipeline import preprocess_text
from app.repositories.preprocessing_repository import (
    create_processing_run,
    finish_processing_run,
    get_dataset_by_id,
    get_posts_by_dataset,
    save_processed_post
)

VALID_VARIANTS = ["minimal", "intermediate", "aggressive"]


def preprocess_dataset(
    db: Session,
    dataset_id: int,
    variant: str
):
    variant = variant.lower()

    if variant not in VALID_VARIANTS:
        raise ValueError(
            f"Invalid variant '{variant}'. Valid options: {VALID_VARIANTS}"
        )

    dataset = get_dataset_by_id(db, dataset_id)

    if dataset is None:
        raise ValueError("Dataset not found")

    posts = get_posts_by_dataset(db, dataset_id)

    run = create_processing_run(
        db=db,
        dataset_id=dataset_id,
        variant=variant,
        total_posts=len(posts)
    )

    seen_texts = set()
    duplicate_posts = 0
    processed_posts = 0

    try:
        for post in posts:
            normalized_original = post.original_text.strip().lower()

            is_duplicate = normalized_original in seen_texts

            if is_duplicate:
                duplicate_posts += 1
            else:
                seen_texts.add(normalized_original)

            processed_data = preprocess_text(
                text=post.original_text,
                variant=variant
            )

            save_processed_post(
                db=db,
                post=post,
                run=run,
                processed_data=processed_data,
                variant=variant,
                is_duplicate=is_duplicate
            )

            processed_posts += 1

        finish_processing_run(
            db=db,
            run=run,
            processed_posts=processed_posts,
            duplicate_posts=duplicate_posts,
            status="finished"
        )

        return {
            "processing_run_id": run.id,
            "dataset_id": dataset_id,
            "variant": variant,
            "total_posts": len(posts),
            "processed_posts": processed_posts,
            "duplicate_posts": duplicate_posts,
            "status": "finished"
        }

    except Exception as error:
        finish_processing_run(
            db=db,
            run=run,
            processed_posts=processed_posts,
            duplicate_posts=duplicate_posts,
            status="failed",
            error_message=str(error)
        )

        raise error