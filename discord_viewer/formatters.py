from datetime import datetime

def parse_dt(dt_str: str) -> datetime:
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))

def format_date_time(dt: datetime):
    # Windows-safe M/D/YY and h:mm AM/PM
    date_part = f"{dt.month}/{dt.day}/{dt.strftime('%y')}"
    hour = dt.strftime("%I").lstrip("0") or "12"
    time_part = f"{hour}:{dt.strftime('%M')} {dt.strftime('%p')}"
    return date_part, time_part
