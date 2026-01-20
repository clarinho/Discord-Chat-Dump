from typing import List
from .model import Message, Row
from .formatters import parse_dt, format_date_time

def build_rows(messages: List[Message]) -> List[Row]:
    rows: List[Row] = []

    current_date = None
    current_server = None
    current_channel = None

    for m in messages:
        dt = parse_dt(m.date)
        date_str, time_str = format_date_time(dt)

        content = (m.content or "").strip()
        has_attachments = bool(m.attachments)

        if current_date != date_str:
            rows.append(Row(type="date", date=date_str, attachments=[]))
            current_date = date_str
            current_server = None
            current_channel = None

        if m.server != current_server or m.channel != current_channel:
            rows.append(Row(type="header", server=m.server, channel=m.channel, category=m.category, attachments=[]))
            current_server = m.server
            current_channel = m.channel

        if content or has_attachments:
            display = content if content else "[attachment]"
            rows.append(Row(type="msg", time=time_str, content=display, attachments=m.attachments))

    return rows
