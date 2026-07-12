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

# Definação da tabela Dataset, que representa um conjunto de dados processados.
class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    source = Column(String(100), nullable=True)
    original_filename = Column(String(255), nullable=False)
    rows_count = Column(Integer, nullable=True)

    id_column = Column(String(255), nullable=True)
    text_column = Column(String(255), nullable=False)
    
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
    original_text = Column(Text, nullable=False)
    inserted_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="posts")

    processed_posts = relationship(
        "ProcessedPost",
        back_populates="post",
        cascade="all, delete-orphan"
    )


class ProcessingRun(Base):
    __tablename__ = "processing_runs"

    id = Column(Integer, primary_key=True, index=True)

    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id"),
        nullable=False,
        index=True
    )

    variant = Column(String(50), nullable=False)

    total_posts = Column(Integer, default=0)
    processed_posts = Column(Integer, default=0)
    duplicate_posts = Column(Integer, default=0)

    status = Column(String(50), default="started")
    error_message = Column(Text, nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    dataset = relationship("Dataset", back_populates="processing_runs")

    processed_records = relationship(
        "ProcessedPost",
        back_populates="processing_run",
        cascade="all, delete-orphan"
    )


class ProcessedPost(Base):
    __tablename__ = "processed_posts"

    id = Column(Integer, primary_key=True, index=True)

    post_id = Column(
        Integer,
        ForeignKey("posts.id"),
        nullable=False,
        index=True
    )

    processing_run_id = Column(
        Integer,
        ForeignKey("processing_runs.id"),
        nullable=False,
        index=True
    )

    variant = Column(String(50), nullable=False)

    original_text = Column(Text, nullable=False)
    processed_text = Column(Text, nullable=False)

    tokens = Column(Text, nullable=True)
    emojis = Column(Text, nullable=True)
    emoji_count = Column(Integer, default=0)

    original_length = Column(Integer, default=0)
    processed_length = Column(Integer, default=0)
    word_count = Column(Integer, default=0)

    has_url = Column(Boolean, default=False)
    has_mention = Column(Boolean, default=False)
    has_hashtag = Column(Boolean, default=False)
    is_duplicate = Column(Boolean, default=False)

    applied_steps = Column(Text, nullable=True)

    processed_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="processed_posts")
    processing_run = relationship("ProcessingRun", back_populates="processed_records")
