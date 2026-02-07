from fastapi import APIRouter, BackgroundTasks, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.models import Book, Chunk, ChunkEmbedding
from services.ingest import parse_txt_or_md
from services.chunking import chunk_paras
from services.embed_provider import embed_texts_batched  # 你实现的 provider
from core.config import EMB_DIM


router = APIRouter(prefix="/v1/books", tags=["books"])
BATCH_SIZE = 32

def run_embedding_job(book_id: str):
    s: Session = SessionLocal()
    try:
        chunks = (
            s.query(Chunk)
            .filter(Chunk.book_id == book_id)
            .order_by(Chunk.chunk_index)
            .all()
        )

        texts = [c.content for c in chunks]
        ids = [c.id for c in chunks]

        # 分批调用 embedding
        for i in range(0, len(texts), BATCH_SIZE):
            batch_texts = texts[i:i+BATCH_SIZE]
            batch_ids = ids[i:i+BATCH_SIZE]

            vectors = embed_texts_batched(batch_texts)  # -> List[List[float]]

            # 基本校验：维度固定
            for v in vectors:
                if len(v) != EMB_DIM:
                    raise ValueError(f"embedding dim mismatch: {len(v)} vs {EMB_DIM}")

            # upsert 写入
            for cid, vec in zip(batch_ids, vectors):
                existing = s.get(ChunkEmbedding, cid)
                if existing:
                    existing.embedding = vec
                else:
                    s.add(ChunkEmbedding(chunk_id=cid, embedding=vec))

            s.commit()

        book = s.get(Book, book_id)
        book.status = "indexed"
        s.commit()

    except Exception:
        # 失败标记（可选但很有用）
        book = s.get(Book, book_id)
        if book:
            book.status = "index_failed"
            s.commit()
        raise
    finally:
        s.close()

@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    raw = (await file.read()).decode("utf-8", errors="ignore")
    if not raw.strip():
        raise HTTPException(400, "empty file")

    paras = parse_txt_or_md(raw)
    if not paras:
        raise HTTPException(400, "no content after parsing")

    chunks = chunk_paras(paras, target_chars=1000, overlap_chars=200)

    s: Session = SessionLocal()
    try:
        book = Book(title=file.filename)
        s.add(book)
        s.flush()  # 生成 book.id

        for i, c in enumerate(chunks):
            s.add(Chunk(
                book_id=book.id,
                chunk_index=i,
                section=c["section"],
                content=c["content"],
            ))

        s.commit()
        return {
            "book_id": book.id,
            "title": book.title,
            "num_paras": len(paras),
            "num_chunks": len(chunks),
            "example_citation": f"{book.title} | {chunks[0]['section']} | chunk_index=0"
        }
    finally:
        s.close()

@router.post("/{book_id}/index")
def index_book(book_id: str, background: BackgroundTasks):
    s = SessionLocal()
    try:
        book = s.get(Book, book_id)
        if not book:
            raise HTTPException(404, "book not found")
        # 标记成 indexing（可选，但推荐）
        book.status = "indexing"
        s.commit()
    finally:
        s.close()

    # 关键：把真正耗时的 embedding 放后台跑
    background.add_task(run_embedding_job, book_id)
    return {"book_id": book_id, "status": "indexing"}

@router.get("/{book_id}/status")
def get_book_status(book_id: str):
    s = SessionLocal()
    try:
        book = s.get(Book, book_id)
        if not book:
            raise HTTPException(404, "book not found")
        return {"book_id": book_id, "status": book.status}
    finally:
        s.close()