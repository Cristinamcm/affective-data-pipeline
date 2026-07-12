import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.models import Dataset, Post, ProcessedPost, ProcessingRun


def get_dataset_by_id(db: Session, dataset_id: int):
    return (
        db.query(Dataset)
        .filter(Dataset.id == dataset_id)
        .first()
    )


def get_posts_by_dataset(db: Session, dataset_id: int):
    return (
        db.query(Post)
        .filter(Post.dataset_id == dataset_id)
        .order_by(Post.id.asc())
        .all()
    )


def create_processing_run(
    db: Session,
    dataset_id: int,
    variant: str,
    total_posts: int
) -> ProcessingRun:
    run = ProcessingRun(
        dataset_id=dataset_id,
        variant=variant,
        total_posts=total_posts,
        status="started"
    )

    db.add(run)
    db.commit()
    db.refresh(run)

    return run


def save_processed_post(
    db: Session,
    post: Post,
    run: ProcessingRun,
    processed_data: dict,
    variant: str,
    is_duplicate: bool = False
):
    processed_post = ProcessedPost(
        post_id=post.id,
        processing_run_id=run.id,
        variant=variant,
        original_text=processed_data["original_text"],
        processed_text=processed_data["processed_text"],
        tokens=json.dumps(processed_data["tokens"], ensure_ascii=False),
        emojis=json.dumps(processed_data["emojis"], ensure_ascii=False),
        emoji_count=processed_data["emoji_count"],
        original_length=processed_data["original_length"],
        processed_length=processed_data["processed_length"],
        word_count=processed_data["word_count"],
        has_url=processed_data["has_url"],
        has_mention=processed_data["has_mention"],
        has_hashtag=processed_data["has_hashtag"],
        is_duplicate=is_duplicate,
        applied_steps=json.dumps(processed_data["applied_steps"], ensure_ascii=False)
    )

    db.add(processed_post)


def finish_processing_run(
    db: Session,
    run: ProcessingRun,
    processed_posts: int,
    duplicate_posts: int,
    status: str = "finished",
    error_message: str | None = None
):
    run.processed_posts = processed_posts
    run.duplicate_posts = duplicate_posts
    run.status = status
    run.error_message = error_message
    run.finished_at = datetime.utcnow()

    db.commit()
    db.refresh(run)

    return run


def get_processing_runs_by_dataset(db: Session, dataset_id: int):
    return (
        db.query(ProcessingRun)
        .filter(ProcessingRun.dataset_id == dataset_id)
        .order_by(ProcessingRun.started_at.desc())
        .all()
    )


def get_processed_posts_by_run(
    db: Session,
    processing_run_id: int,
    limit: int = 100,
    offset: int = 0
):
    return (
        db.query(ProcessedPost)
        .filter(ProcessedPost.processing_run_id == processing_run_id)
        .order_by(ProcessedPost.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )