from sqlalchemy.orm import Session

from app.preprocessing.preprocessing_pipeline import preprocess_text
from app.preprocessing.presets import normalize_config
from app.repositories.preprocessing_repository import (
    create_processing_run,
    finish_processing_run,
    get_dataset_by_id,
    get_posts_by_dataset,
    save_processed_post
)


def preprocess_dataset(
    db: Session,
    dataset_id: int,
    configuration_name: str,
    config: dict
):
    dataset = get_dataset_by_id(db, dataset_id)

    if dataset is None:
        raise ValueError("Dataset not found")

    normalized_config = normalize_config(config)

    posts = get_posts_by_dataset(db, dataset_id)

    run = create_processing_run(
        db=db,
        dataset_id=dataset_id,
        configuration_name=configuration_name,
        configuration_json=normalized_config,
        total_posts=len(posts)
    )

    seen_texts = set()
    duplicate_posts = 0
    empty_after_processing = 0
    processed_posts_count = 0

    try:
        for post in posts:
            original_normalized = post.original_text.strip().lower()

            is_duplicate = False

            if normalized_config.get("normalize_spaces"):
                original_normalized = " ".join(original_normalized.split())

            if original_normalized in seen_texts:
                is_duplicate = True
                duplicate_posts += 1
            else:
                seen_texts.add(original_normalized)

            processed_data = preprocess_text(
                text=post.original_text,
                config=normalized_config
            )

            if processed_data["is_empty_after_processing"]:
                empty_after_processing += 1

            save_processed_post(
                db=db,
                post=post,
                run=run,
                processed_data=processed_data,
                is_duplicate=is_duplicate
            )

            processed_posts_count += 1

        finish_processing_run(
            db=db,
            run=run,
            processed_posts_count=processed_posts_count,
            duplicate_posts=duplicate_posts,
            empty_after_processing=empty_after_processing,
            status="finished"
        )

        return {
            "processing_run_id": run.id,
            "dataset_id": dataset_id,
            "configuration_name": configuration_name,
            "total_posts": len(posts),
            "processed_posts": processed_posts_count,
            "duplicate_posts": duplicate_posts,
            "empty_after_processing": empty_after_processing,
            "status": "finished"
        }

    except Exception as error:
        finish_processing_run(
            db=db,
            run=run,
            processed_posts_count=processed_posts_count,
            duplicate_posts=duplicate_posts,
            empty_after_processing=empty_after_processing,
            status="failed",
            error_message=str(error)
        )

        raise error