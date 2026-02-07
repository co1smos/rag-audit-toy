# apps/api/routes/qa.py

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, cast
from typing import List, Dict, Any

from db.session import get_db
from db.models import ChunkEmbedding, Chunk # 确保导入 Book 模型    
from services.embed_provider import embed_one  # 你实现的 provider
from services.openai_chat import get_answer_from_openai

router = APIRouter()

class QARequest(BaseModel):
    question: str
    book_id: str

class QAResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]

SIMILARITY_THRESHOLD = 0.75
TOP_K = 5

@router.post("/qa", response_model=QAResponse)
def question_answer(req: QARequest, db: Session = next(get_db())):
    question = req.question
    book_id = req.book_id

    # 1. Embed the question
    query_embedding = np.array(embed_one(question))  # 维度必须一致

    # 2. pgvector similarity search
    results = (
        db.query(ChunkEmbedding, Chunk)
        .join(Chunk, ChunkEmbedding.chunk_id == Chunk.id)
        .filter(ChunkEmbedding.book_id == book_id)
        .order_by(func.l2_distance(ChunkEmbedding.embedding, cast(query_embedding.tolist(), ARRAY(Float))))
        .limit(TOP_K)
        .all()
    )

    if not results or results[0].similarity < SIMILARITY_THRESHOLD:
        return QAResponse(
            answer="我在当前资料中找不到依据，你可以提供章节或关键词吗？",
            citations=[]
        )

    # 3. Construct prompt
    context_blocks = []
    citations = []

    for i, row in enumerate(results):
        block = f"[{i+1}] {row.content.strip()}"
        context_blocks.append(block)
        citations.append({
            "chunk_index": row.chunk_index,
            "section": row.section,
            "content": row.content
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
    answer = get_answer_from_openai(prompt)

    return QAResponse(
        answer=answer.strip(),
        citations=citations
    )
