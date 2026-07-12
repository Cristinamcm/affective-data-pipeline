import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.preprocessing_repository import (
    get_processed_posts_by_run,
    get_processing_runs_by_dataset
)
from app.services.preprocessing_service import preprocess_dataset


router = APIRouter(prefix="/preprocessing", tags=["Preprocessing"])


@router.post("/datasets/{dataset_id}/run")
def run_preprocessing(
    dataset_id: int,
    variant: str = Query(default="intermediate"),
    db: Session = Depends(get_db)
):
    try:
        result = preprocess_dataset(
            db=db,
            dataset_id=dataset_id,
            variant=variant
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@router.get("/datasets/{dataset_id}/runs")
def list_dataset_processing_runs(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    runs = get_processing_runs_by_dataset(
        db=db,
        dataset_id=dataset_id
    )

    return [
        {
            "id": run.id,
            "dataset_id": run.dataset_id,
            "variant": run.variant,
            "total_posts": run.total_posts,
            "processed_posts": run.processed_posts,
            "duplicate_posts": run.duplicate_posts,
            "status": run.status,
            "error_message": run.error_message,
            "started_at": run.started_at,
            "finished_at": run.finished_at
        }
        for run in runs
    ]


@router.get("/runs/{processing_run_id}/posts")
def list_processed_posts_by_run(
    processing_run_id: int,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    processed_posts = get_processed_posts_by_run(
        db=db,
        processing_run_id=processing_run_id,
        limit=limit,
        offset=offset
    )

    return [
        {
            "id": post.id,
            "post_id": post.post_id,
            "processing_run_id": post.processing_run_id,
            "variant": post.variant,
            "original_text": post.original_text,
            "processed_text": post.processed_text,
            "tokens": json.loads(post.tokens) if post.tokens else [],
            "emojis": json.loads(post.emojis) if post.emojis else [],
            "emoji_count": post.emoji_count,
            "original_length": post.original_length,
            "processed_length": post.processed_length,
            "word_count": post.word_count,
            "has_url": post.has_url,
            "has_mention": post.has_mention,
            "has_hashtag": post.has_hashtag,
            "is_duplicate": post.is_duplicate,
            "applied_steps": json.loads(post.applied_steps)
            if post.applied_steps else [],
            "processed_at": post.processed_at
        }
        for post in processed_posts
    ]