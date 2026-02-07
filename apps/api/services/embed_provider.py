import hashlib, random
from core.config import EMB_DIM
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def embed_one(text: str):
    # h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    # seed = int(h[:16], 16)
    # rnd = random.Random(seed)
    # vec = [rnd.uniform(-1.0, 1.0) for _ in range(EMB_DIM)]
    # norm = (sum(x*x for x in vec) ** 0.5) or 1.0
    # return [x / norm for x in vec]
    res = client.embeddings.create(
        input=[text],
        model="text-embedding-3-small"
    )
    return res.data[0].embedding


def embed_texts_batched(texts: list[str]) -> list[list[float]]:
    return [embed_one(t) for t in texts]
