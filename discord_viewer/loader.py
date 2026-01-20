import json
from typing import List
from .model import Message, Attachment

def load_messages(path: str) -> List[Message]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Top-level JSON must be a list of message objects.")

    out: List[Message] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        if not item.get("date"):
            continue

        atts = []
        raw_atts = item.get("attachments") or []
        if isinstance(raw_atts, list):
            for a in raw_atts:
                if not isinstance(a, dict):
                    continue
                fn = (a.get("filename") or "").strip() or "file"
                url = (a.get("url") or "").strip()
                if fn or url:
                    atts.append(Attachment(filename=fn, url=url))

        out.append(
            Message(
                server=item.get("server", "unknown"),
                category=item.get("category", ""),
                channel=item.get("channel", "unknown"),
                date=item["date"],
                content=(item.get("content") or ""),
                attachments=atts,
            )
        )

    # ISO strings sort lexicographically
    out.sort(key=lambda m: m.date)
    return out
