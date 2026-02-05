from session import SessionLocal
from models import Book, Chunk

session = SessionLocal()

print("\n=== Books ===")
books = session.query(Book).all()
for b in books:
    print(b.id, b.title)

if books:
    book_id = books[0].id

    print("\n=== Chunks ===")
    chunks = (
        session.query(Chunk)
        .filter(Chunk.book_id == book_id)
        .order_by(Chunk.chunk_index)
        .limit(5)
        .all()
    )

    for c in chunks:
        print(
            f"index={c.chunk_index}",
            f"section={c.section}",
            f"text={c.content[:60]}..."
        )

session.close()
