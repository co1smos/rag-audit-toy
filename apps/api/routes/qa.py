# apps/api/routes/qa.py
import numpy as np
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Float
from sqlalchemy.dialects.postgresql import ARRAY # 确保导入了正确的 ARRAY
from typing import List, Dict, Any

from core.config import EMB_DIM
from pgvector.sqlalchemy import Vector
from db.session import SessionLocal
from db.models import ChunkEmbedding, Chunk 
from services.embed_provider import embed_one 
from services.chat_provider import generate_answer

router = APIRouter()

class QARequest(BaseModel):
    question: str
    book_id: str

class QAResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]

# --- 数据库依赖注入 ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

SIMILARITY_THRESHOLD = 0.25
TOP_K = 5

@router.post("/qa", response_model=QAResponse)
def question_answer(req: QARequest, db: Session = Depends(get_db)):
    question = req.question
    book_id = req.book_id

    # 1. Embed the question
    query_embedding = embed_one(question)  # 维度必须一致
    print(f"Query embedding 输出结果: {query_embedding[:5]}...")  # 调试输出前5维

    # 2. pgvector similarity search
    distance_func = ChunkEmbedding.embedding.l2_distance(cast(query_embedding, Vector(EMB_DIM)))

    results = (
        db.query(ChunkEmbedding, Chunk, distance_func.label("distance"))
        .join(Chunk, ChunkEmbedding.chunk_id == Chunk.id)
        .filter(Chunk.book_id == book_id)
        .order_by("distance")
        .limit(TOP_K)
        .all()
    )

    print("Similarity search results (distance):")
    for r in results:
        print(f"  Distance: {r.distance}")

    if not results or results[0].distance < SIMILARITY_THRESHOLD:
        return QAResponse(
            answer="我在当前资料中找不到依据，你可以提供章节或关键词吗？",
            citations=[]
        )

    # 3. Construct prompt
    context_blocks = []
    citations = []

    for i, row in enumerate(results):
        block = f"[{i+1}] {row.Chunk.content.strip()}"
        context_blocks.append(block)
        citations.append({
            "chunk_index": row.Chunk.chunk_index,
            "section": row.Chunk.section,
            "content": row.Chunk.content
        })

    prompt = f"""
你是一位根据文档回答问题的助手。

以下是文档片段：
{chr(10).join(context_blocks)}

请根据上述资料回答以下问题，并在引用后注明数字索引（如 [2]）：
用户问题：{question}

请输出回答内容，注明引用的编号。
"""

    # 4. Call LLM
    try:
        answer = generate_answer(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"大模型调用失败: {str(e)}")

    return QAResponse(
        answer=answer.strip(),
        citations=citations
    )
