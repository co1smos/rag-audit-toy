from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.models import Book, Chunk
from services.ingest import parse_txt_or_md
from services.chunking import chunk_paras

router = APIRouter(prefix="/v1/books", tags=["books"])

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
