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

# acrescentar as proximas tabelas mais tarde processed_posts, emotion_labels, processing_runs