from datetime import datetime

from sqlalchemy.orm import Session

from app.models.models import (
    Dataset,
    EmotionLabel,
    Post,
    ProcessedPost,
    ProcessingRun
)


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