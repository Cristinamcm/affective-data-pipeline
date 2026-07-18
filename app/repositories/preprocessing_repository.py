import json
from datetime import datetime

from sqlalchemy import case, func
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
    configuration_name: str,
    configuration_json: dict,
    total_posts: int
) -> ProcessingRun:
    run = ProcessingRun(
        dataset_id=dataset_id,
        configuration_name=configuration_name,
        configuration_json=json.dumps(configuration_json, ensure_ascii=False),
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
    is_duplicate: bool = False
):
    processed_post = ProcessedPost(
        post_id=post.id,
        processing_run_id=run.id,
        original_text=processed_data["original_text"],
        processed_text=processed_data["processed_text"],
        tokens=json.dumps(processed_data["tokens"], ensure_ascii=False),
        emojis=json.dumps(processed_data["emojis"], ensure_ascii=False),
        hashtags=json.dumps(processed_data["hashtags"], ensure_ascii=False),
        applied_steps=json.dumps(processed_data["applied_steps"], ensure_ascii=False),
        original_length=processed_data["original_length"],
        processed_length=processed_data["processed_length"],
        word_count=processed_data["word_count"],
        token_count=processed_data["token_count"],
        emoji_count=processed_data["emoji_count"],
        hashtag_count=processed_data["hashtag_count"],
        url_count=processed_data["url_count"],
        mention_count=processed_data["mention_count"],
        has_url=processed_data["has_url"],
        has_mention=processed_data["has_mention"],
        has_hashtag=processed_data["has_hashtag"],
        is_duplicate=is_duplicate,
        is_empty_after_processing=processed_data["is_empty_after_processing"]
    )

    db.add(processed_post)


def finish_processing_run(
    db: Session,
    run: ProcessingRun,
    processed_posts_count: int,
    duplicate_posts: int,
    empty_after_processing: int,
    status: str = "finished",
    error_message: str | None = None
):
    run.processed_posts_count = processed_posts_count
    run.duplicate_posts = duplicate_posts
    run.empty_after_processing = empty_after_processing
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


def get_processing_run_by_id(db: Session, processing_run_id: int):
    return (
        db.query(ProcessingRun)
        .filter(ProcessingRun.id == processing_run_id)
        .first()
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


def get_processing_run_summary(db: Session, processing_run_id: int):
    run = get_processing_run_by_id(db, processing_run_id)

    if run is None:
        return None

    summary = (
        db.query(
            func.count(ProcessedPost.id),
            func.avg(ProcessedPost.original_length),
            func.avg(ProcessedPost.processed_length),
            func.avg(ProcessedPost.word_count),
            func.avg(ProcessedPost.token_count),
            func.sum(ProcessedPost.emoji_count),
            func.sum(ProcessedPost.url_count),
            func.sum(ProcessedPost.mention_count),
            func.sum(ProcessedPost.hashtag_count),
            func.sum(case((ProcessedPost.has_url == True, 1), else_=0)),
            func.sum(case((ProcessedPost.has_mention == True, 1), else_=0)),
            func.sum(case((ProcessedPost.has_hashtag == True, 1), else_=0)),
            func.sum(case((ProcessedPost.is_duplicate == True, 1), else_=0)),
            func.sum(case((ProcessedPost.is_empty_after_processing == True, 1), else_=0))
        )
        .filter(ProcessedPost.processing_run_id == processing_run_id)
        .first()
    )

    return {
        "processing_run_id": run.id,
        "dataset_id": run.dataset_id,
        "configuration_name": run.configuration_name,
        "configuration_json": json.loads(run.configuration_json),
        "status": run.status,
        "total_posts": run.total_posts,
        "processed_posts": run.processed_posts_count,
        "duplicate_posts": run.duplicate_posts,
        "empty_after_processing": run.empty_after_processing,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "metrics": {
            "records": int(summary[0] or 0),
            "avg_original_length": float(summary[1] or 0),
            "avg_processed_length": float(summary[2] or 0),
            "avg_word_count": float(summary[3] or 0),
            "avg_token_count": float(summary[4] or 0),
            "total_emojis": int(summary[5] or 0),
            "total_urls": int(summary[6] or 0),
            "total_mentions": int(summary[7] or 0),
            "total_hashtags": int(summary[8] or 0),
            "posts_with_url": int(summary[9] or 0),
            "posts_with_mention": int(summary[10] or 0),
            "posts_with_hashtag": int(summary[11] or 0),
            "duplicate_posts": int(summary[12] or 0),
            "empty_after_processing": int(summary[13] or 0)
        }
    }