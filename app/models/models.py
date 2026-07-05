from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text
)
from sqlalchemy.orm import relationship

from app.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    source = Column(String(100), nullable=True)
    original_filename = Column(String(255), nullable=False)
    rows_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    posts = relationship(
        "Post",
        back_populates="dataset",
        cascade="all, delete-orphan"
    )

    processing_runs = relationship(
        "ProcessingRun",
        back_populates="dataset",
        cascade="all, delete-orphan"
    )


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)

    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id"),
        nullable=False,
        index=True
    )

    external_id = Column(String(255), nullable=True)
    source = Column(String(100), nullable=True)

    original_text = Column(Text, nullable=False)
    original_label = Column(String(255), nullable=True)

    created_at = Column(DateTime, nullable=True)
    inserted_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="posts")

    processed_post = relationship(
        "ProcessedPost",
        back_populates="post",
        uselist=False,
        cascade="all, delete-orphan"
    )

    emotion_labels = relationship(
        "EmotionLabel",
        back_populates="post",
        cascade="all, delete-orphan"
    )


class ProcessedPost(Base):
    __tablename__ = "processed_posts"

    id = Column(Integer, primary_key=True, index=True)

    post_id = Column(
        Integer,
        ForeignKey("posts.id"),
        nullable=False,
        unique=True,
        index=True
    )

    cleaned_text = Column(Text, nullable=False)
    text_with_emojis_as_words = Column(Text, nullable=True)

    language = Column(String(20), nullable=True)

    emojis = Column(Text, nullable=True)
    emoji_count = Column(Integer, default=0)

    word_count = Column(Integer, default=0)
    original_text_length = Column(Integer, default=0)
    cleaned_text_length = Column(Integer, default=0)

    has_url = Column(Boolean, default=False)
    has_mention = Column(Boolean, default=False)
    has_hashtag = Column(Boolean, default=False)

    processing_version = Column(String(50), default="v1")
    processed_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="processed_post")


class EmotionLabel(Base):
    __tablename__ = "emotion_labels"

    id = Column(Integer, primary_key=True, index=True)

    post_id = Column(
        Integer,
        ForeignKey("posts.id"),
        nullable=False,
        index=True
    )

    emotion = Column(String(100), nullable=False)
    value = Column(Integer, default=1)

    confidence = Column(Float, nullable=True)
    source = Column(String(100), default="dataset")

    post = relationship("Post", back_populates="emotion_labels")


class ProcessingRun(Base):
    __tablename__ = "processing_runs"

    id = Column(Integer, primary_key=True, index=True)

    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id"),
        nullable=True,
        index=True
    )

    input_filename = Column(String(255), nullable=False)
    output_filename = Column(String(255), nullable=True)

    total_records = Column(Integer, default=0)
    status = Column(String(50), default="started")

    error_message = Column(Text, nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    dataset = relationship("Dataset", back_populates="processing_runs")