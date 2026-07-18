import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.preprocessing.presets import PREPROCESSING_PRESETS, SUPPORTED_OPERATIONS
from app.repositories.preprocessing_repository import (
    get_processed_posts_by_run,
    get_processing_run_summary,
    get_processing_runs_by_dataset
)
from app.schemas.preprocessing_schema import PreprocessingRequest
from app.services.preprocessing_service import preprocess_dataset


router = APIRouter(prefix="/preprocessing", tags=["Preprocessing"])


@router.get("/presets")
def list_preprocessing_presets():
    return {
        "supported_operations": SUPPORTED_OPERATIONS,
        "presets": PREPROCESSING_PRESETS
    }


@router.post("/datasets/{dataset_id}/run")
def run_preprocessing(
    dataset_id: int,
    request: PreprocessingRequest,
    db: Session = Depends(get_db)
):
    try:
        result = preprocess_dataset(
            db=db,
            dataset_id=dataset_id,
            configuration_name=request.configuration_name,
            config=request.config
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
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
            "configuration_name": run.configuration_name,
            "configuration_json": json.loads(run.configuration_json),
            "total_posts": run.total_posts,
            "processed_posts": run.processed_posts_count,
            "duplicate_posts": run.duplicate_posts,
            "empty_after_processing": run.empty_after_processing,
            "status": run.status,
            "error_message": run.error_message,
            "started_at": run.started_at,
            "finished_at": run.finished_at
        }
        for run in runs
    ]


@router.get("/runs/{processing_run_id}/summary")
def get_run_summary(
    processing_run_id: int,
    db: Session = Depends(get_db)
):
    summary = get_processing_run_summary(
        db=db,
        processing_run_id=processing_run_id
    )

    if summary is None:
        raise HTTPException(
            status_code=404,
            detail="Processing run not found"
        )

    return summary


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
            "original_text": post.original_text,
            "processed_text": post.processed_text,
            "tokens": json.loads(post.tokens) if post.tokens else [],
            "emojis": json.loads(post.emojis) if post.emojis else [],
            "hashtags": json.loads(post.hashtags) if post.hashtags else [],
            "applied_steps": json.loads(post.applied_steps) if post.applied_steps else [],
            "original_length": post.original_length,
            "processed_length": post.processed_length,
            "word_count": post.word_count,
            "token_count": post.token_count,
            "emoji_count": post.emoji_count,
            "hashtag_count": post.hashtag_count,
            "url_count": post.url_count,
            "mention_count": post.mention_count,
            "has_url": post.has_url,
            "has_mention": post.has_mention,
            "has_hashtag": post.has_hashtag,
            "is_duplicate": post.is_duplicate,
            "is_empty_after_processing": post.is_empty_after_processing,
            "processed_at": post.processed_at
        }
        for post in processed_posts
    ]