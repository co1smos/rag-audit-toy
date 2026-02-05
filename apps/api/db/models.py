import uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey, Text, DateTime, func
from pgvector.sqlalchemy import Vector

class Base(DeclarativeBase):
    pass

class Book(Base):
    __tablename__ = "books"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String, nullable=False)  # source_title
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chunks = relationship("Chunk", back_populates="book", cascade="all, delete-orphan")

class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    book_id: Mapped[str] = mapped_column(String, ForeignKey("books.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)   # 0..N
    section: Mapped[str] = mapped_column(String, nullable=False, default="Unknown")
    content: Mapped[str] = mapped_column(Text, nullable=False)

    book = relationship("Book", back_populates="chunks")
    embedding = relationship("ChunkEmbedding", back_populates="chunk", uselist=False, cascade="all, delete-orphan")

class ChunkEmbedding(Base):
    __tablename__ = "chunk_embeddings"

    chunk_id: Mapped[str] = mapped_column(String, ForeignKey("chunks.id"), primary_key=True)
    # 维度先不强行写死，后面接真实 embedding 再固定，比如 Vector(1536)
    embedding: Mapped[list[float]] = mapped_column(Vector())

    chunk = relationship("Chunk", back_populates="embedding")
