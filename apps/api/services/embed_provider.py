import hashlib, random
from core.config import EMB_DIM
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_ID = "gemini-embedding-001"

def embed_one(text: str):
    res = client.models.embed_content(
        model=MODEL_ID,
        contents=[text],
        config=types.EmbedContentConfig(output_dimensionality=EMB_DIM)
    )
    return res.embeddings[0].values


def embed_texts_batched(texts: list[str]) -> list[list[float]]:
    return [embed_one(t) for t in texts]
