'''
Storage.py 
Storage logic for timer results. Separated from timer logic so it's easy to unit-test and swap out storage backends. 
Saves timer results to a JSON file.
'''
from __future__ import annotations

import json 
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import TypedDict, cast
from typing_extensions import Required

class SessionRecord(TypedDict, total=False):
    id: str # unique identifier for the session, e.g. a UUID
    task: Required[str] # description of the task worked on during the session
    planned_duration: Required[int] # planned duration of the session in seconds
    actual_duration: Required[int] # actual duration of the session in seconds
    started_at: Required[str] # ISO 8601 timestamp of when the session started
    ended_at: Required[str] # ISO 8601 timestamp of when the session ended
    status: Required[str] # "completed" or "interrupted"
    session_type: Required[str] # "focus" or "break"
    reflection: str # optional reflection on how the session went, e.g. "Felt good", "Got distracted by phone"


def _load_all(data_path: Path) -> list[SessionRecord]:
    if not data_path.exists():
        return []
    with open(data_path) as f:
        return cast(list[SessionRecord], json.load(f))


def get_all_sessions(data_path: Path) -> list[SessionRecord]:
    return _load_all(data_path)


def get_all_focus_sessions(data_path: Path) -> list[SessionRecord]:
    return [session for session in get_all_sessions(data_path) if session["session_type"] == "focus"]


def get_all_break_sessions(data_path: Path) -> list[SessionRecord]:
    return [session for session in get_all_sessions(data_path) if session["session_type"] == "break"]

def get_all_completed_break_sessions(data_path: Path) -> list[SessionRecord]:
    return [session for session in get_all_break_sessions(data_path) if session["status"] == "completed"]


def get_all_completed_focus_sessions(data_path: Path) -> list[SessionRecord]:
    return [session for session in get_all_focus_sessions(data_path) if session["status"] == "completed"]


def _save_all(data_path: Path, records: list[SessionRecord]) -> None:
    data_path.parent.mkdir(parents=True, exist_ok=True)
    with open(data_path, "w") as f:
        json.dump(records, f, indent=2)


def save_session(data_path: Path, record: SessionRecord) -> None:
    records = _load_all(data_path)
    records.append(record)
    _save_all(data_path, records)


def get_sessions_last_n_days(data_path: Path, days: int = 7) -> list[SessionRecord]:
    records = _load_all(data_path)
    completed_sessions: list[SessionRecord] =[]
    for r in records: 
        if r.get("session_type") == "focus":
            try:
                d = datetime.fromisoformat(r["started_at"]).date()
                if d >= datetime.now().date() - timedelta(days=days-1):
                    completed_sessions.append(r)
            except ValueError:
                continue
    return completed_sessions


def _get_completed_focus_dates(data_path: Path) -> set[date]:
    records = _load_all(data_path)
    completed_dates: set[date] = set()
    for r in records:
        if r.get("status") == "completed" and r.get("session_type") == "focus":
            try:
                d = datetime.fromisoformat(r["started_at"]).date()
                completed_dates.add(d)
            except ValueError:
                continue
    return completed_dates


def get_streak(data_path: Path) -> int:
    """Return the number of consecutive days with at least one completed focus session from current day."""
    completed_dates: set[date] = _get_completed_focus_dates(data_path) 
    streak = 0
    while (datetime.now().date() - timedelta(days=streak)) in completed_dates:
        streak += 1
    return streak
        

def get_longest_streak(data_path: Path) -> int:
    """Return the longest streak of consecutive days with at least one completed focus session."""
    completed_dates: set[date] = _get_completed_focus_dates(data_path)
    if not completed_dates:
        return 0
    sorted_dates = sorted(completed_dates)
    longest_streak = 1
    current_streak = 1
    for i in range(1, len(sorted_dates)):
        if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
            current_streak += 1
        else:
            longest_streak = max(longest_streak, current_streak)
            current_streak = 1
    longest_streak = max(longest_streak, current_streak)
    return longest_streak


def get_max_sessions_per_day(data_path: Path) -> int:
    """Return the maximum number of completed focus sessions in a single day."""
    records = _load_all(data_path)
    sessions_per_day: dict[date, int] = {}
    for r in records:
        if r.get("status") == "completed" and r.get("session_type") == "focus":
            try:
                d = datetime.fromisoformat(r["started_at"]).date()
                sessions_per_day[d] = sessions_per_day.get(d, 0) + 1
            except ValueError:
                continue
    return max(sessions_per_day.values(), default=0)


def get_number_completed_focus_sessions_today(data_path: Path) -> int:
    """Return the number of completed focus sessions today."""
    records = _load_all(data_path)
    today = datetime.now().date()
    count = 0
    for r in records:
        if r.get("status") == "completed" and r.get("session_type") == "focus":
            try:
                d = datetime.fromisoformat(r["started_at"]).date()
                if d == today:
                    count += 1
            except ValueError:
                continue
    return count


def get_number_completed_focus_sessions_today_since_last_long_break(data_path: Path, long_break_minutes: int) -> int:
    """Return the number of completed focus sessions today since the last long break."""
    records = _load_all(data_path)
    today = datetime.now().date()
    last_break_time = None
    for r in reversed(records):
        if r.get("session_type") == "break" and r.get("actual_duration",0) >= long_break_minutes * 60:
            try:
                last_break_time = datetime.fromisoformat(r["started_at"])
                break
            except ValueError:
                continue
    count = 0
    for r in records:
        if r.get("status") == "completed" and r.get("session_type") == "focus":
            try:
                start_time = datetime.fromisoformat(r["started_at"])
                if start_time.date() == today and (last_break_time is None or start_time > last_break_time):
                    count += 1
            except ValueError:
                continue
    return count


def get_total_focus_mins(data_path: Path, include_interrupted: bool = False) -> int:
    """Return total focus time in minutes."""
    records = _load_all(data_path)

    if include_interrupted:
        return round(sum(r.get("actual_duration", 0) for r in records if r.get("session_type") == "focus") / 60 )
    else:
        return round(sum(r.get("actual_duration", 0) for r in records if r.get("status") == "completed" and r.get("session_type") == "focus") / 60)


def get_most_focus_min(data_path: Path, include_interrupted: bool = False) -> int:
    """Return the longest focus session in minutes."""
    records = _load_all(data_path)
    if include_interrupted:
        return round(max((r.get("actual_duration", 0) for r in records if r.get("session_type") == "focus"), default=0)/60)
    else: 
        return round(max((r.get("actual_duration", 0) for r in records if r.get("status") == "completed" and r.get("session_type") == "focus"), default=0)/60)
    