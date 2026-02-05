import re
from dataclasses import dataclass

@dataclass
class RawPara:
    section: str
    text: str

def parse_txt_or_md(text: str) -> list[RawPara]:
    lines = text.splitlines()
    section = "Unknown"
    buf = []
    out: list[RawPara] = []

    def flush():
        nonlocal buf
        p = "\n".join(buf).strip()
        if p:
            out.append(RawPara(section=section, text=p))
        buf = []

    for line in lines:
        s = line.strip()
        m = re.match(r"^(#{1,6})\s+(.+)$", s)
        if m:  # markdown title
            flush()
            section = m.group(2).strip()
            continue
        if s == "":
            flush()
        else:
            buf.append(line)

    flush()
    return out
