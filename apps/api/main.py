from fastapi import FastAPI
from sqlalchemy import text
from db.session import engine
from db.init_db import init_db
from routes.books import router as books_router
from routes.qa import router as qa_router

app = FastAPI(title="RAG Audio Tutor")
app.include_router(books_router)
app.include_router(qa_router)

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True}