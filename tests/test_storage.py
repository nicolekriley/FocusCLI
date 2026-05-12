'''
Tests for storage module.
'''

from focus.storage import save_session, get_sessions_last_n_days, get_max_sessions_per_day, get_longest_streak, get_streak, SessionRecord
from datetime import datetime, timedelta

def test_save_and_load(tmp_path):
    data_path = tmp_path / "sessions.json"
    record = SessionRecord(
        id=1, 
        task="Test Task",
        planned_duration=25,
        actual_duration=20,
        started_at="2024-01-01T10:00:00",
        ended_at="2024-01-01T10:20:00",
        reflection="Felt good",
        status="completed",
        session_type="focus"
    )
    save_session(data_path, record)
    loaded = get_sessions_last_n_days(data_path, days=7)
    assert len(loaded) == 1
    assert loaded[0] == record

def test_streak(tmp_path):
    data_path = tmp_path / "sessions.json"
    # Create records for 3 consecutive days
    for i in range(3):
        record = SessionRecord(
            id=i, 
            task=f"Task {i}",
            planned_duration=25,
            actual_duration=25,
            started_at=f"2024-01-0{i+1}T10:00:00",
            ended_at=f"2024-01-0{i+1}T10:25:00",
            reflection="Felt good",
            status="completed",
            session_type="focus"
        )
        save_session(data_path, record)
    assert get_streak(data_path) == 3

def test_streak_with_gaps(tmp_path):
    data_path = tmp_path / "sessions.json"
    # Create records for 3 days with a gap
    for i in [0, 1, 3]:  # Skip day 2
        record = SessionRecord(
            id=i, 
            task=f"Task {i}",
            planned_duration=25,
            actual_duration=25,
            started_at=f"2024-01-0{i+1}T10:00:00",
            ended_at=f"2024-01-0{i+1}T10:25:00",
            reflection="Felt good",
            status="completed",
            session_type="focus"
        )
        save_session(data_path, record)
    assert get_streak(data_path) == 2  # Streak should reset after the gap

def test_streak_no_sessions(tmp_path):
    data_path = tmp_path / "sessions.json"
    assert get_streak(data_path) == 0  # No sessions, so streak should be 0

def test_streak_all_interrupted(tmp_path):
    data_path = tmp_path / "sessions.json"
    # Create interrupted sessions for 3 consecutive days
    for i in range(3):
        record = SessionRecord(
            id=i, 
            task=f"Task {i}",
            planned_duration=25,
            actual_duration=10,
            started_at=f"2024-01-0{i+1}T10:00:00",
            ended_at=f"2024-01-0{i+1}T10:10:00",
            reflection="Felt bad",
            status="interrupted",
            session_type="focus"
        )
        save_session(data_path, record)
    assert get_streak(data_path) == 0  # All sessions interrupted, so streak should be 0

def test_streak_mixed_status(tmp_path):
    data_path = tmp_path / "sessions.json"
    # Create mixed sessions for 3 consecutive days
    for i in range(3):
        record = SessionRecord(
            id=i, 
            task=f"Task {i}",
            planned_duration=25,
            actual_duration=25 if i % 2 == 0 else 10,
            started_at=f"2024-01-0{i+1}T10:00:00",
            ended_at=f"2024-01-0{i+1}T10:25:00" if i % 2 == 0 else f"2024-01-0{i+1}T10:10:00",
            reflection="Felt good" if i % 2 == 0 else "Felt bad",
            status="completed" if i % 2 == 0 else "interrupted",
            session_type="focus"
        )
        save_session(data_path, record)
    assert get_streak(data_path) == 1  # Only the first day is completed, so streak should be 1

def test_longest_streak(tmp_path):
    data_path = tmp_path / "sessions.json"
    # Create records for 5 days with a gap in the middle
    for i in [0, 1, 3, 4]:  # Skip day 2
        record = SessionRecord(
            id=i, 
            task=f"Task {i}",
            planned_duration=25,
            actual_duration=25,
            started_at=f"2024-01-0{i+1}T10:00:00",
            ended_at=f"2024-01-0{i+1}T10:25:00",
            reflection="Felt good",
            status="completed",
            session_type="focus"
        )
        save_session(data_path, record)
    assert get_longest_streak(data_path) == 2  # Longest streak should be 2 (days 0-1 and days 3-4)

def test_get_sessions_last_n_days(tmp_path):
    data_path = tmp_path / "sessions.json"
    # Create records for 10 days
    for i in range(10):
        date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=9-i)
        record = SessionRecord(
            id=i, 
            task=f"Task {i}",
            planned_duration=25,
            actual_duration=25,
            started_at= date.isoformat(),  # Start from 10 days ago
            ended_at= (date + timedelta(minutes=25)).isoformat(),
            status="completed",
            session_type="focus" if i % 2 == 0 else "break"
        )
        save_session(data_path, record)
    last_7_days = get_sessions_last_n_days(data_path, days=7)
    assert len(last_7_days) == 7
    assert last_7_days[0]["started_at"] == (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)).isoformat()  # Should start from day 7

def test_get_sessions_last_n_days_no_sessions(tmp_path):
    data_path = tmp_path / "sessions.json"
    last_7_days = get_sessions_last_n_days(data_path, days=7)
    assert len(last_7_days) == 0  # No sessions, so should return empty list

def test_get_sessions_last_n_days_all_old(tmp_path):
    data_path = tmp_path / "sessions.json"
    # Create records for 10 days, all older than 7 days
    for i in range(10):
        record = SessionRecord(
            id=i, 
            task=f"Task {i}",
            planned_duration=25,
            actual_duration=25,
            started_at=f"2023-12-{i+1:02d}T10:00:00",
            ended_at=f"2023-12-{i+1:02d}T10:25:00",
            status="completed",
            session_type="focus"
        )
        save_session(data_path, record)
    last_7_days = get_sessions_last_n_days(data_path, days=7)
    assert len(last_7_days) == 0  # All sessions are old, so should return empty list

def test_get_sessions_last_n_days_mixed(tmp_path):
    data_path = tmp_path / "sessions.json"
    # Create records for 10 days, with some in the last 7 days and some older. Some are incomplete, which should be filtered out.
    for i in range(10):
        date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=9-i)
        record = SessionRecord(
            id=i, 
            task=f"Task {i}",
            planned_duration=25,
            actual_duration=25,
            started_at= date.isoformat(),
            ended_at= (date + timedelta(minutes=25)).isoformat(),
            status="completed" if i % 2 == 0 else "interrupted",  # Only even days are completed
            session_type="focus"
        )
        save_session(data_path, record)
    last_7_days = get_sessions_last_n_days(data_path, days=7)
    assert len(last_7_days) == 7
    assert last_7_days[0]["started_at"] == (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)).isoformat()
    completed_sessions = [r for r in last_7_days if r["status"] == "completed"]
    assert len(completed_sessions) == 4  # Only even days are completed
    interrupted_sessions = [r for r in last_7_days if r["status"] == "interrupted"]
    assert len(interrupted_sessions) == 3  # Only odd days are interrupted



