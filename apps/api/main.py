from fastapi import FastAPI

app = FastAPI(title="RAG Audio Tutor")

@app.get("/health")
def health():
    return {"ok": True}