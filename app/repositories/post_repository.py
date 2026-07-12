from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.models.models import (
    Dataset,
    EmotionLabel,
    Post,
    ProcessedPost,
    ProcessingRun
)

from sqlalchemy import case, func

def create_processing_run(
    db: Session,
    input_filename: str,
    status: str = "started"
) -> ProcessingRun:
    processing_run = ProcessingRun(
        input_filename=input_filename,
        status=status,
        started_at=datetime.utcnow()
    )

    db.add(processing_run)
    db.commit()
    db.refresh(processing_run)

    return processing_run


def finish_processing_run(
    db: Session,
    processing_run: ProcessingRun,
    dataset_id: int,
    output_filename: str,
    total_records: int,
    status: str = "finished",
    error_message: str | None = None
) -> ProcessingRun:
    processing_run.dataset_id = dataset_id
    processing_run.output_filename = output_filename
    processing_run.total_records = total_records
    processing_run.status = status
    processing_run.error_message = error_message
    processing_run.finished_at = datetime.utcnow()

    db.commit()
    db.refresh(processing_run)

    return processing_run


def create_dataset(
    db: Session,
    name: str,
    source: str,
    original_filename: str,
    rows_count: int
) -> Dataset:
    dataset = Dataset(
        name=name,
        source=source,
        original_filename=original_filename,
        rows_count=rows_count
    )

    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return dataset


def create_post_with_processed_data(
    db: Session,
    dataset_id: int,
    record: dict,
    processed_record: dict
) -> Post:
    original_text = str(record.get("text", ""))

    post = Post(
        dataset_id=dataset_id,
        external_id=str(record.get("id", "")) if record.get("id") is not None else None,
        source=str(record.get("source", "")) if record.get("source") is not None else None,
        original_text=original_text,
        original_label=str(record.get("label", "")) if record.get("label") is not None else None
    )

    db.add(post)
    db.flush()

    processed_post = ProcessedPost(
        post_id=post.id,
        cleaned_text=str(processed_record.get("cleaned_text", "")),
        text_with_emojis_as_words=str(
            processed_record.get("text_with_emojis_as_words", "")
        ),
        language=str(processed_record.get("language", "")),
        emojis=str(processed_record.get("emojis", "")),
        emoji_count=int(processed_record.get("emoji_count", 0) or 0),
        word_count=int(processed_record.get("word_count", 0) or 0),
        original_text_length=int(
            processed_record.get("original_text_length", 0) or 0
        ),
        cleaned_text_length=int(
            processed_record.get("cleaned_text_length", 0) or 0
        ),
        has_url=bool(processed_record.get("has_url", False)),
        has_mention=bool(processed_record.get("has_mention", False)),
        has_hashtag=bool(processed_record.get("has_hashtag", False)),
        processing_version=str(
            processed_record.get("processing_version", "v1")
        )
    )

    db.add(processed_post)

    emotion_labels = processed_record.get("emotion_labels", [])

    if isinstance(emotion_labels, str):
        emotion_labels = [
            label.strip()
            for label in emotion_labels.split(",")
            if label.strip()
        ]

    for emotion in emotion_labels:
        db.add(
            EmotionLabel(
                post_id=post.id,
                emotion=str(emotion),
                value=1,
                source="dataset"
            )
        )

    db.commit()
    db.refresh(post)

    return post

def get_datasets(db: Session, limit: int = 50, offset: int = 0):
    return (
        db.query(Dataset)
        .order_by(Dataset.created_at.desc())
        .offset(offset)
        .limit(limit)
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
        .options(
            joinedload(Post.processed_post),
            joinedload(Post.emotion_labels)
        )
        .filter(Post.dataset_id == dataset_id)
        .order_by(Post.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_processing_runs(db: Session, limit: int = 50, offset: int = 0):
    return (
        db.query(ProcessingRun)
        .order_by(ProcessingRun.started_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_dataset_summary(db: Session, dataset_id: int):
    dataset = get_dataset_by_id(db, dataset_id)

    if dataset is None:
        return None

    total_posts = (
        db.query(func.count(Post.id))
        .filter(Post.dataset_id == dataset_id)
        .scalar()
    )

    processed_posts = (
        db.query(func.count(ProcessedPost.id))
        .join(Post, ProcessedPost.post_id == Post.id)
        .filter(Post.dataset_id == dataset_id)
        .scalar()
    )

    averages = (
        db.query(
            func.avg(ProcessedPost.word_count),
            func.avg(ProcessedPost.emoji_count),
            func.avg(ProcessedPost.original_text_length),
            func.avg(ProcessedPost.cleaned_text_length)
        )
        .join(Post, ProcessedPost.post_id == Post.id)
        .filter(Post.dataset_id == dataset_id)
        .first()
    )

    social_counts = (
        db.query(
            func.sum(case((ProcessedPost.has_url == True, 1), else_=0)),
            func.sum(case((ProcessedPost.has_mention == True, 1), else_=0)),
            func.sum(case((ProcessedPost.has_hashtag == True, 1), else_=0))
        )
        .join(Post, ProcessedPost.post_id == Post.id)
        .filter(Post.dataset_id == dataset_id)
        .first()
    )

    language_distribution = (
        db.query(
            ProcessedPost.language,
            func.count(ProcessedPost.id)
        )
        .join(Post, ProcessedPost.post_id == Post.id)
        .filter(Post.dataset_id == dataset_id)
        .group_by(ProcessedPost.language)
        .all()
    )

    emotion_distribution = (
        db.query(
            EmotionLabel.emotion,
            func.count(EmotionLabel.id)
        )
        .join(Post, EmotionLabel.post_id == Post.id)
        .filter(Post.dataset_id == dataset_id)
        .group_by(EmotionLabel.emotion)
        .all()
    )

    multilabel_subquery = (
        db.query(
            EmotionLabel.post_id,
            func.count(EmotionLabel.id).label("emotion_count")
        )
        .join(Post, EmotionLabel.post_id == Post.id)
        .filter(Post.dataset_id == dataset_id)
        .group_by(EmotionLabel.post_id)
        .having(func.count(EmotionLabel.id) > 1)
        .subquery()
    )

    multilabel_posts = (
        db.query(func.count())
        .select_from(multilabel_subquery)
        .scalar()
    )

    return {
        "dataset_id": dataset.id,
        "dataset_name": dataset.name,
        "source": dataset.source,
        "original_filename": dataset.original_filename,
        "rows_count": dataset.rows_count,
        "created_at": dataset.created_at,
        "total_posts": total_posts or 0,
        "processed_posts": processed_posts or 0,
        "avg_word_count": float(averages[0] or 0),
        "avg_emoji_count": float(averages[1] or 0),
        "avg_original_text_length": float(averages[2] or 0),
        "avg_cleaned_text_length": float(averages[3] or 0),
        "posts_with_url": int(social_counts[0] or 0),
        "posts_with_mention": int(social_counts[1] or 0),
        "posts_with_hashtag": int(social_counts[2] or 0),
        "multilabel_posts": multilabel_posts or 0,
        "language_distribution": {
            language or "unknown": count
            for language, count in language_distribution
        },
        "emotion_distribution": {
            emotion: count
            for emotion, count in emotion_distribution
        }
    }