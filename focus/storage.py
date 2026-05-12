'''
Storage.py 
Storage logic for timer results. Separated from timer logic so it's easy to unit-test and swap out storage backends. 
Saves timer results to a JSON file.
'''
from __future__ import annotations

import json 
from typing import List
from focus.timer import TimerResult
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import TypedDict, Required

class SessionRecord(TypedDict, total=False):
    id: int # unique identifier for the session, e.g. a UUID
    task: str # description of the task worked on during the session
    planned_duration: Required[int] # planned duration of the session in seconds
    actual_duration: Required[int] # actual duration of the session in seconds
    started_at: Required[str] # ISO 8601 timestamp of when the session started
    ended_at: Required[str] # ISO 8601 timestamp of when the session ended
    status: Required[str] # "completed" or "interrupted"
    session_type: Required[str] # "focus" or "break"
    reflection: str # optional reflection on how the session went, e.g. "Felt good", "Got distracted by phone"

def _load_all(data_path: Path) -> List[SessionRecord]:
    if not data_path.exists():
        return []
    with open(data_path) as f:
        return json.load(f)
    
def _save_all(data_path: Path, records: List[SessionRecord]) -> None:
    data_path.parent.mkdir(parents=True, exist_ok=True)
    with open(data_path, "w") as f:
        json.dump(records, f, indent=2)

def save_session(data_path: Path, record: SessionRecord) -> None:
    records = _load_all(data_path)
    records.append(record)
    _save_all(data_path, records)

def get_sessions_last_n_days(data_path: Path, days: int = 7) -> List[SessionRecord]:
    records = _load_all(data_path)
    cutoff = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days - 1)
    return [
        r for r in records
        if r.get("session_type") == "focus"
        and r.get("started_at", "") >= cutoff.isoformat()
    ]

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
    completed_dates:set[date] = _get_completed_focus_dates(data_path) 
    streak = 0
    today = datetime.now().date()
    while (today - timedelta(days=streak)) in completed_dates:
        streak += 1
    return streak
        
def get_longest_streak(data_path: Path) -> int:
    """Return the longest streak of consecutive days with at least one completed focus session."""
    completed_dates:set[date] = _get_completed_focus_dates(data_path)
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


