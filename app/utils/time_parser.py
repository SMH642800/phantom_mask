# Utility functions for parsing pharmacy opening hours string into structured data.
import re
from datetime import time


def parse_opening_hours(opening_str):
    """
    Parse a string describing opening hours (e.g. 'Mon - Fri 08:00 - 18:00 / Sat, Sun 09:00 - 12:00')
    into a list of dicts with day, start, end, and is_overnight fields.
    Returns: List[dict]
    """
    results = []
    sections = [s.strip() for s in opening_str.split("/")]

    for section in sections:
        match = re.match(r"^([A-Za-z,\s\-]+)\s+(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})$", section)
        if not match:
            continue  # Skip invalid

        day_part = match.group(1).strip()
        start_time = to_time(match.group(2))
        end_time = to_time(match.group(3))
        is_overnight = (end_time <= start_time)

        for day in parse_days(day_part):
            results.append({
                "day": day,
                "start": start_time,
                "end": end_time,
                "is_overnight": is_overnight
            })

    return results


def parse_days(day_part):
    """
    Parse a day part string (e.g. 'Mon - Fri', 'Mon, Wed, Fri') into a list of weekday strings.
    Returns: List[str]
    """
    day_map = {
        "Mon": "Mon", "Tue": "Tue", "Wed": "Wed",
        "Thu": "Thu", "Thur": "Thu",
        "Fri": "Fri", "Sat": "Sat", "Sun": "Sun"
    }

    day_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    # Format 1: "Mon - Fri"
    if "-" in day_part:
        start_day, end_day = [d.strip() for d in day_part.split("-")]
        start_idx = day_order.index(day_map[start_day])
        end_idx = day_order.index(day_map[end_day])
        return day_order[start_idx:end_idx + 1]

    # Format 2: "Mon, Wed, Fri"
    else:
        parts = [d.strip() for d in day_part.split(",")]
        return [day_map[d] for d in parts if d in day_map]


def to_time(t_str):
    """
    Convert a string in HH:MM format to a datetime.time object.
    """
    hour, minute = map(int, t_str.split(":"))
    return time(hour, minute)
