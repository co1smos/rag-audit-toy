from typing import List
from services.ingest import RawPara

def chunk_paras(
    paras: List[RawPara],
    target_chars: int = 1000,
    overlap_chars: int = 200
):
    chunks = []
    cur_section = paras[0].section if paras else "Unknown"
    cur = ""

    def push(sec: str, content: str):
        chunks.append({"section": sec or "Unknown", "content": content.strip()})

    for p in paras:
        # 如果 section 变了且当前已经积累了一些内容，先切一块，避免跨章太多
        if p.section != cur_section and len(cur) >= 300:
            push(cur_section, cur)
            tail = cur[-overlap_chars:] if overlap_chars > 0 else ""
            cur_section = p.section
            cur = (tail + "\n\n" + p.text).strip()
            continue

        candidate = (cur + "\n\n" + p.text).strip() if cur else p.text
        if len(candidate) <= target_chars:
            cur = candidate
            cur_section = p.section
        else:
            # 当前 chunk 满了
            if cur.strip():
                push(cur_section, cur)
                tail = cur[-overlap_chars:] if overlap_chars > 0 else ""
                cur_section = p.section
                cur = (tail + "\n\n" + p.text).strip()
            else:
                # 单段落本身就很长：直接切（简单处理）
                push(p.section, p.text[:target_chars])
                cur = p.text[max(0, target_chars - overlap_chars):]

    if cur.strip():
        push(cur_section, cur)

    return chunks
