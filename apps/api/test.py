from services.ingest import parse_txt_or_md
from services.chunking import chunk_paras

md = """# Chapter 1
This is para 1.

This is para 2.

## Section A
A1 line 1.
A1 line 2.

A2 para.

# Chapter 2
Second chapter para.
"""

paras = parse_txt_or_md(md)
print("PARAS:", len(paras))
for i, p in enumerate(paras[:6]):
    print(f"\n--- PARA {i} ---")
    print("section =", p.section)
    print("text =", p.text[:80], "...")

chunks = chunk_paras(paras, target_chars=80, overlap_chars=20)  # 故意设小，方便看到切块效果
print("\nCHUNKS:", len(chunks))
for i, c in enumerate(chunks[:6]):
    print(f"\n=== CHUNK {i} ===")
    print("section =", c["section"])
    print("len =", len(c["content"]))
    print(c["content"])
