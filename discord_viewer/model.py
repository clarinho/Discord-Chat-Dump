from dataclasses import dataclass
from typing import List, Optional

@dataclass(frozen=True)
class Attachment:
    filename: str
    url: str

@dataclass(frozen=True)
class Message:
    server: str
    category: str
    channel: str
    date: str  # ISO string
    content: str
    attachments: List[Attachment]

@dataclass(frozen=True)
class Row:
    # type: "date" | "header" | "msg"
    type: str
    date: str = ""
    time: str = ""
    server: str = ""
    channel: str = ""
    category: str = ""
    content: str = ""
    attachments: Optional[List[Attachment]] = None
