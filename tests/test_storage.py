'''
Tests for storage module.
'''

from focus.storage import (
    _load_all,
    save_session, 
    get_sessions_last_n_days, 
    get_max_sessions_per_day, 
    get_longest_streak, 
    get_streak, 
    SessionRecord, 
    get_number_completed_focus_sessions_today, 
    get_number_completed_focus_sessions_today_since_last_long_break, 
    get_all_sessions, 
    get_most_focus_min, 
    get_total_focus_mins, 
    get_all_completed_focus_sessions, 
    get_all_break_sessions, 
    get_all_focus_sessions, 
    get_all_completed_break_sessions
)
from datetime import datetime, timedelta
from pathlib import Path

## Helper functions

def _today_midnight() -> datetime:
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

def _focus_record(id: str, status: str = "completed", minute_length: int = 25, hour_shift: int = 0) -> SessionRecord:
    return SessionRecord(
        id=id,
        task=f"Task {id}",
        planned_duration=minute_length * 60,
        actual_duration=minute_length * 60,
        started_at= (_today_midnight() + timedelta(hours=hour_shift)).isoformat(),
        ended_at=(_today_midnight() + timedelta(hours=hour_shift, minutes=minute_length)).isoformat(),
        status=status,
        session_type="focus",
    )
 
 
def _break_record(id: str, status: str = "completed", minute_length: int = 5, hour_shift: int = 0) -> SessionRecord:
    return SessionRecord(
        id=id,
        task=f"Task {id}",
        planned_duration=minute_length * 60,
        actual_duration=minute_length * 60,
        started_at=(_today_midnight() + timedelta(hours=hour_shift)).isoformat(),
        ended_at=(_today_midnight() + timedelta(hours=hour_shift, minutes=minute_length)).isoformat(),
        status=status,
        session_type="break",
    )
 
 
def _save_all(data_path: Path, records: list[SessionRecord]) -> None:
    for r in records:
        save_session(data_path, r)
 

def test_save_session_and_load_all(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    record = SessionRecord(
        id="1", 
        task="Test Task",
        planned_duration=25 * 60,
        actual_duration=20 * 60,
        started_at=_today_midnight().isoformat(),
        ended_at=(_today_midnight() + timedelta(hours=0, minutes=20)).isoformat(),
        reflection="Felt good",
        status="completed", 
        session_type="focus"
    )
    save_session(data_path, record)
    loaded = _load_all(data_path)
    assert len(loaded) == 1
    assert loaded[0] == record


def test_save_all_and_load_multiple(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _focus_record("1"), 
        _break_record("2"),
        _focus_record("3"),
    ])
    results = get_all_sessions(data_path)
    assert len(results) == 3


def test_load_all_with_corrupt_file(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    data_path.write_text("not a valid json")
    results = get_all_sessions(data_path)
    assert results == []  # Should return empty list, not raise an exception


def test_get_all_focus_sessions_no_sessions(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    assert get_all_focus_sessions(data_path) == []
 
 
def test_get_all_focus_sessions_only_focus(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _focus_record("1"),
        _focus_record("2"),
        _focus_record("3"),
    ])
    results = get_all_focus_sessions(data_path)
    assert len(results) == 3
    assert all(r["session_type"] == "focus" for r in results)
 
 
def test_get_all_focus_sessions_only_breaks(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _break_record("1"),
        _break_record("2"),
    ])
    assert get_all_focus_sessions(data_path) == []
 
 
def test_get_all_focus_sessions_mixed(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _focus_record("1"),
        _break_record("2"),
        _focus_record("3"),
        _break_record("4"),
    ])
    results = get_all_focus_sessions(data_path)
    assert len(results) == 2
    assert all(r["session_type"] == "focus" for r in results)
    assert ["id" in r and r["id"] for r in results] == ["1", "3"]
 
 
def test_get_all_focus_sessions_with_interrupted(tmp_path: Path) -> None:
    '''Interrupted focus sessions should still be returned — the function
    filters by type only, not by status.'''
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _focus_record("1", status="completed"),
        _focus_record("2", status="interrupted"),
        _break_record("3", status="completed"),
        _focus_record("4", status="interrupted"),
    ])
    results = get_all_focus_sessions(data_path)
    assert len(results) == 3
    assert all(r["session_type"] == "focus" for r in results)
    statuses = [r["status"] for r in results]
    assert "completed" in statuses
    assert "interrupted" in statuses
 
 
def test_get_all_focus_sessions_all_interrupted(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _focus_record("1", status="interrupted"),
        _focus_record("2", status="interrupted"),
    ])
    results = get_all_focus_sessions(data_path)
    assert len(results) == 2
    assert all(r["session_type"] == "focus" for r in results)
 
 
# ---------------------------------------------------------------------------
# get_all_break_sessions
# ---------------------------------------------------------------------------
 
def test_get_all_break_sessions_no_sessions(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    assert get_all_break_sessions(data_path) == []
 
 
def test_get_all_break_sessions_only_breaks(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _break_record("1"),
        _break_record("2"),
        _break_record("3"),
    ])
    results = get_all_break_sessions(data_path)
    assert len(results) == 3
    assert all(r["session_type"] == "break" for r in results)
 
 
def test_get_all_break_sessions_only_focus(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _focus_record("1"),
        _focus_record("2"),
    ])
    assert get_all_break_sessions(data_path) == []
 
 
def test_get_all_break_sessions_mixed(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _focus_record("1"),
        _break_record("2"),
        _focus_record("3"),
        _break_record("4"),
    ])
    results = get_all_break_sessions(data_path)
    assert len(results) == 2
    assert all(r["session_type"] == "break" for r in results)
    assert ["id" in r and r["id"] for r in results] == ["2", "4"]
 
 
def test_get_all_break_sessions_with_interrupted(tmp_path: Path) -> None:
    '''Interrupted break sessions should still be returned — the function
    filters by type only, not by status.'''
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _break_record("1", status="completed"),
        _break_record("2", status="interrupted"),
        _focus_record("3", status="completed"),
        _break_record("4", status="interrupted"),
    ])
    results = get_all_break_sessions(data_path)
    assert len(results) == 3
    assert all(r["session_type"] == "break" for r in results)
    statuses = [r["status"] for r in results]
    assert "completed" in statuses
    assert "interrupted" in statuses
 
 
def test_get_all_break_sessions_all_interrupted(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _break_record("1", status="interrupted"),
        _break_record("2", status="interrupted"),
    ])
    results = get_all_break_sessions(data_path)
    assert len(results) == 2
    assert all(r["session_type"] == "break" for r in results)
 
 
# ---------------------------------------------------------------------------
# get_all_completed_focus_sessions
# ---------------------------------------------------------------------------
 
def test_get_all_completed_focus_sessions_no_sessions(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    assert get_all_completed_focus_sessions(data_path) == []
 
 
def test_get_all_completed_focus_sessions_all_completed(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _focus_record("1", status="completed"),
        _focus_record("2", status="completed"),
        _focus_record("3", status="completed"),
    ])
    results = get_all_completed_focus_sessions(data_path)
    assert len(results) == 3
    assert all(r["session_type"] == "focus" for r in results)
    assert all(r["status"] == "completed" for r in results)
 
 
def test_get_all_completed_focus_sessions_with_interrupted(tmp_path: Path) -> None:
    '''Interrupted focus sessions should be excluded.'''
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _focus_record("1", status="completed"),
        _focus_record("2", status="interrupted"),
        _focus_record("3", status="completed"),
    ])
    results = get_all_completed_focus_sessions(data_path)
    assert len(results) == 2
    assert all(r["status"] == "completed" for r in results)
    assert ["id" in r and r["id"] for r in results] == ["1", "3"]
 
 
def test_get_all_completed_focus_sessions_all_interrupted(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _focus_record("1", status="interrupted"),
        _focus_record("2", status="interrupted"),
    ])
    assert get_all_completed_focus_sessions(data_path) == []
 
 
def test_get_all_completed_focus_sessions_only_breaks(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _break_record("1", status="completed"),
        _break_record("2", status="completed"),
    ])
    assert get_all_completed_focus_sessions(data_path) == []
 
 
def test_get_all_completed_focus_sessions_mixed_types_and_statuses(tmp_path: Path) -> None:
    '''Only sessions that are both focus AND completed should be returned.'''
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _focus_record("1", status="completed"),   # included
        _focus_record("2", status="interrupted"),  # excluded: interrupted
        _break_record("3", status="completed"),    # excluded: break
        _break_record("4", status="interrupted"),  # excluded: break + interrupted
        _focus_record("5", status="completed"),   # included
    ])
    results = get_all_completed_focus_sessions(data_path)
    assert len(results) == 2
    assert all(r["session_type"] == "focus" for r in results)
    assert all(r["status"] == "completed" for r in results)
    assert ["id" in r and r["id"] for r in results] == ["1", "5"]


def test_get_all_completed_break_sessions_no_sessions(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    assert get_all_completed_break_sessions(data_path) == []
 
 
def test_get_all_completed_break_sessions_all_completed(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _break_record("1", status="completed"),
        _break_record("2", status="completed"),
        _break_record("3", status="completed"),
    ])
    results = get_all_completed_break_sessions(data_path)
    assert len(results) == 3
    assert all(r["session_type"] == "break" for r in results)
    assert all(r["status"] == "completed" for r in results)
 
 
def test_get_all_completed_break_sessions_with_interrupted(tmp_path: Path) -> None:
    '''Interrupted break sessions should be excluded.'''
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _break_record("1", status="completed"),
        _break_record("2", status="interrupted"),
        _break_record("3", status="completed"),
    ])
    results = get_all_completed_break_sessions(data_path)
    assert len(results) == 2
    assert all(r["status"] == "completed" for r in results)
    assert ["id" in r and r["id"] for r in results] == ["1", "3"]
 
 
def test_get_all_completed_break_sessions_all_interrupted(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _break_record("1", status="interrupted"),
        _break_record("2", status="interrupted"),
    ])
    assert get_all_completed_break_sessions(data_path) == []
 
 
def test_get_all_completed_break_sessions_only_focus(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _focus_record("1", status="completed"),
        _focus_record("2", status="completed"),
    ])
    assert get_all_completed_break_sessions(data_path) == []
 
 
def test_get_all_completed_break_sessions_mixed_types_and_statuses(tmp_path: Path) -> None:
    '''Only sessions that are both break AND completed should be returned.'''
    data_path = tmp_path / "sessions.json"
    _save_all(data_path, [
        _break_record("1", status="completed"),   # included
        _break_record("2", status="interrupted"),  # excluded: interrupted
        _focus_record("3", status="completed"),    # excluded: focus
        _focus_record("4", status="interrupted"),  # excluded: focus + interrupted
        _break_record("5", status="completed"),   # included
    ])
    results = get_all_completed_break_sessions(data_path)
    assert len(results) == 2
    assert all(r["session_type"] == "break" for r in results)
    assert all(r["status"] == "completed" for r in results)
    assert ["id" in r and r["id"] for r in results] == ["1", "5"]
 

def test_streak(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 4 consecutive days
    for i in range(4):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60,
            actual_duration=25 * 60,
            started_at= (_today_midnight() -timedelta(days=3-i)+ timedelta(hours=10, minutes=0)).isoformat(),
            ended_at= (_today_midnight() -timedelta(days=3-i)+ timedelta(hours=10, minutes=25)).isoformat(),
            reflection="Felt good",
            status="completed",
            session_type="focus"
        )
        save_session(data_path, record)
    assert get_streak(data_path) == 4


def test_streak_with_gaps(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 3 days with a gap
    for i in [0, 1, 3]:  # Skip day 2
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60,
            actual_duration=25 * 60,
            started_at= (_today_midnight() -timedelta(days=3-i)+ timedelta(hours=10, minutes=0)).isoformat(),
            ended_at= (_today_midnight() -timedelta(days=3-i)+ timedelta(hours=10, minutes=25)).isoformat(),
            reflection="Felt good",
            status="completed",
            session_type="focus"
        )
        save_session(data_path, record)
    assert get_streak(data_path) == 1  # Streak should reset after the gap


def test_streak_no_sessions(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    assert get_streak(data_path) == 0  # No sessions, so streak should be 0


def test_streak_all_interrupted(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create interrupted sessions for 3 consecutive days
    for i in range(3):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60,
            actual_duration=10 * 60,
            started_at= (_today_midnight() - timedelta(days=3-i) + timedelta(hours=10, minutes=0)).isoformat(),
            ended_at= (_today_midnight() - timedelta(days=3-i) + timedelta(hours=10, minutes=10)).isoformat(),
            reflection="Felt bad",
            status="interrupted",
            session_type="focus"
        )
        save_session(data_path, record)
    assert get_streak(data_path) == 0  # All sessions interrupted, so streak should be 0


def test_streak_mixed_status(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create mixed sessions for 4 consecutive days
    for i in range(4):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60,
            actual_duration=25 * 60 if i % 2 == 0 else 10 * 60,
            started_at= (_today_midnight() - timedelta(days=3-i) + timedelta(hours=10, minutes=0)).isoformat(),
            ended_at= (_today_midnight() - timedelta(days=3-i) + timedelta(hours=10, minutes=25)).isoformat() if i % 2 == 0 
                else (_today_midnight() - timedelta(days=3-i) + timedelta(hours=10, minutes=10)).isoformat(),
            reflection="Felt good" if i % 2 == 1 else "Felt bad",
            status="completed" if i % 2 == 1 else "interrupted",
            session_type="focus"
        )
        save_session(data_path, record)
    assert get_streak(data_path) == 1  # Current day and two days are completed, but one day is interrupted, so streak should be 1


def test_longest_streak(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 5 days with a gap in the middle
    for i in [0, 1, 3, 4]:  # Skip day 2
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60,
            actual_duration=25 * 60,
            started_at=f"2024-01-0{i+1}T10:00:00",
            ended_at=f"2024-01-0{i+1}T10:25:00",
            reflection="Felt good",
            status="completed",
            session_type="focus"
        )
        save_session(data_path, record)
    assert get_longest_streak(data_path) == 2  # Longest streak should be 2 (days 0-1 and days 3-4)


def test_get_sessions_last_n_days(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 10 days
    for i in range(10):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60,
            actual_duration=25 * 60,
            started_at= (_today_midnight() - timedelta(days=9-i) + timedelta(hours=10, minutes=0)).isoformat(),  # Start from 10 days ago
            ended_at= (_today_midnight() - timedelta(days=9-i) + timedelta(hours=10, minutes=25)).isoformat(),
            status="completed",
            session_type="focus"
        )
        save_session(data_path, record)
    last_7_days = get_sessions_last_n_days(data_path, days=7)
    assert len(last_7_days) == 7
    assert last_7_days[0]["started_at"] == (_today_midnight() + timedelta(hours=10, minutes=0) - timedelta(days=6)).isoformat()  # Should start from day 7


def test_get_sessions_last_n_days_no_sessions(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    last_7_days = get_sessions_last_n_days(data_path, days=7)
    assert len(last_7_days) == 0  # No sessions, so should return empty list


def test_get_sessions_last_n_days_all_old(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 10 days, all older than 7 days
    for i in range(10):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60,
            actual_duration=25 * 60,
            started_at=f"2023-12-{i+1:02d}T10:00:00",
            ended_at=f"2023-12-{i+1:02d}T10:25:00",
            status="completed",
            session_type="focus"
        )
        save_session(data_path, record)
    last_7_days = get_sessions_last_n_days(data_path, days=7)
    assert len(last_7_days) == 0  # All sessions are old, so should return empty list


def test_get_sessions_last_n_days_mixed(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 10 days, with some in the last 7 days and some older. Some are incomplete.
    for i in range(10):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60,
            actual_duration=25 * 60,
            started_at= (_today_midnight() - timedelta(days=9-i) + timedelta(hours=10, minutes=0)).isoformat(),
            ended_at= (_today_midnight() - timedelta(days=9-i) + timedelta(hours=10, minutes=25)).isoformat(),
            status="completed" if i % 2 == 0 else "interrupted",  # Only even days are completed
            session_type="focus"
        )
        save_session(data_path, record)
    last_7_days = get_sessions_last_n_days(data_path, days=7)
    assert len(last_7_days) == 7
    assert last_7_days[0]["started_at"] == (_today_midnight() + timedelta(hours=10, minutes=0) - timedelta(days=6)).isoformat()
    completed_sessions = [r for r in last_7_days if r["status"] == "completed"]
    assert len(completed_sessions) == 3  # Only even days are completed
    interrupted_sessions = [r for r in last_7_days if r["status"] == "interrupted"]
    assert len(interrupted_sessions) == 4  # Only odd days are interrupted


def test_get_sessions_last_n_days_only_breaks(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 10 days, all are break sessions
    for i in range(10):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=5 * 60,
            actual_duration=5 * 60,
            started_at= (_today_midnight() - timedelta(days=9-i) + timedelta(hours=10, minutes=0)).isoformat(),
            ended_at= (_today_midnight() - timedelta(days=9-i) + timedelta(hours=10, minutes=5)).isoformat(),
            status="completed",
            session_type="break"
        )
        save_session(data_path, record)
    last_7_days = get_sessions_last_n_days(data_path, days=7)
    assert len(last_7_days) == 0  # All sessions are breaks, so should return empty list


def test_get_sessions_mixed_session_types(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 10 days, with a mix of focus and break sessions
    for i in range(10):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60 if i % 2 == 0 else 5 * 60,
            actual_duration=25 * 60 if i % 2 == 0 else 5 * 60,
            started_at= (_today_midnight() - timedelta(days=9-i) + timedelta(hours=10, minutes=0)).isoformat(),
            ended_at= (_today_midnight() - timedelta(days=9-i) + timedelta(hours=10, minutes=25 if i % 2 == 0 else 5)).isoformat(),
            status="completed",
            session_type="focus" if i % 2 == 0 else "break"
        )
        save_session(data_path, record)
    last_7_days = get_sessions_last_n_days(data_path, days=7)
    assert len(last_7_days) == 3 # Only the focus sessions on even days should be returned 


def test_get_max_sessions_per_day(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 3 days with varying number of sessions
    for i in range(3):
        for j in range(i + 1):  # Day 0 has 1 session, Day 1 has 2 sessions, Day 2 has 3 sessions
            record = SessionRecord(
                id=str(i*10+j), 
                task=f"Task {i*10+j}",
                planned_duration=25 * 60,
                actual_duration=25 * 60,
                started_at=f"2024-01-0{i+1}T10:00:00",
                ended_at=f"2024-01-0{i+1}T10:25:00",
                status="completed",
                session_type="focus"
            )
            save_session(data_path, record)
    assert get_max_sessions_per_day(data_path) == 3  # Maximum sessions in a single day should be 3


def test_get_max_sessions_per_day_no_sessions(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    assert get_max_sessions_per_day(data_path) == 0  # No sessions, so should return 0


def test_get_max_sessions_per_day_mixed_session_types(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 3 days with a mix of focus and break sessions
    for i in range(3):
        for j in range(i + 1):  # Day 0 has 1 session, Day 1 has 2 sessions, Day 2 has 3 sessions
            record = SessionRecord(
                id=str(i*10+j), 
                task=f"Task {i*10+j}",
                planned_duration=25 * 60 if j % 2 == 0 else 5 * 60,
                actual_duration=25 * 60 if j % 2 == 0 else 5 * 60,
                started_at=f"2024-01-0{i+1}T10:00:00",
                ended_at=f"2024-01-0{i+1}T10:25:00" if j % 2 == 0 else f"2024-01-0{i+1}T10:05:00",
                status="completed",
                session_type="focus" if j % 2 == 0 else "break"
            )
            save_session(data_path, record)
    assert get_max_sessions_per_day(data_path) == 2  # Only the focus sessions should be counted, so max should be 2


def test_get_max_sessions_per_day_all_breaks(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 3 days, all are break sessions
    for i in range(3):
        for j in range(i + 1):  # Day 0 has 1 session, Day 1 has 2 sessions, Day 2 has 3 sessions
            record = SessionRecord(
                id=str(i*10+j), 
                task=f"Task {i*10+j}",
                planned_duration=5 * 60,
                actual_duration=5 * 60,
                started_at=f"2024-01-0{i+1}T10:00:00",
                ended_at=f"2024-01-0{i+1}T10:05:00",
                status="completed",
                session_type="break"
            )
            save_session(data_path, record)
    assert get_max_sessions_per_day(data_path) == 0  # All sessions are breaks, so should return 0


def test_get_all_sessions(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 3 days with varying number of sessions
    for i in range(3):
        for j in range(i + 1):  # Day 0 has 1 session, Day 1 has 2 sessions, Day 2 has 3 sessions
            record = SessionRecord(
                id=str(i*10+j), 
                task=f"Task {i*10+j}",
                planned_duration=25 * 60,
                actual_duration=25 * 60,
                started_at=f"2024-01-0{i+1}T10:00:00",
                ended_at=f"2024-01-0{i+1}T10:25:00",
                status="completed",
                session_type="focus"
            )
            save_session(data_path, record)
    all_sessions = get_all_sessions(data_path)
    assert len(all_sessions) == 6  # Total sessions should be 1 + 2 + 3 = 6


def test_get_all_sessions_no_sessions(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    all_sessions = get_all_sessions(data_path)
    assert len(all_sessions) == 0  # No sessions, so should return empty list


def test_get_all_sessions_mixed_session_types(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 3 days with a mix of focus and break sessions
    for i in range(3):
        for j in range(i + 1):  # Day 0 has 1 session, Day 1 has 2 sessions, Day 2 has 3 sessions
            record = SessionRecord(
                id=str(i*10+j), 
                task=f"Task {i*10+j}",
                planned_duration=25 * 60 if j % 2 == 0 else 5 * 60,
                actual_duration=25 * 60 if j % 2 == 0 else 5 * 60,
                started_at=f"2024-01-0{i+1}T10:00:00",
                ended_at=f"2024-01-0{i+1}T10:25:00" if j % 2 == 0 else f"2024-01-0{i+1}T10:05:00",
                status="completed",
                session_type="focus" if j % 2 == 0 else "break"
            )
            save_session(data_path, record)
    all_sessions = get_all_sessions(data_path)
    assert len(all_sessions) == 6  # Total sessions should be 1 + 2 + 3 = 6, regardless of type


def test_get_all_sessions_only_breaks(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 3 days, all are break sessions
    for i in range(3):
        for j in range(i + 1):  # Day 0 has 1 session, Day 1 has 2 sessions, Day 2 has 3 sessions
            record = SessionRecord(
                id=str(i*10+j), 
                task=f"Task {i*10+j}",
                planned_duration=5 * 60,
                actual_duration=5 * 60,
                started_at=f"2024-01-0{i+1}T10:00:00",
                ended_at=f"2024-01-0{i+1}T10:05:00",
                status="completed",
                session_type="break"
            )
            save_session(data_path, record)
    all_sessions = get_all_sessions(data_path)
    assert len(all_sessions) == 6  # Total sessions should be 1 + 2 + 3 = 6, regardless of type


def test_get_all_sessions_with_interrupted(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 3 days with a mix of completed and interrupted sessions
    for i in range(3):
        for j in range(i + 1):  # Day 0 has 1 session, Day 1 has 2 sessions, Day 2 has 3 sessions
            record = SessionRecord(
                id=str(i*10+j), 
                task=f"Task {i*10+j}",
                planned_duration=25 * 60,
                actual_duration=25 * 60 if j % 2 == 0 else 10 * 60,
                started_at=f"2024-01-0{i+1}T10:00:00",
                ended_at=f"2024-01-0{i+1}T10:25:00" if j % 2 == 0 else f"2024-01-0{i+1}T10:10:00",
                status="completed" if j % 2 == 0 else "interrupted",
                session_type="focus"
            )
            save_session(data_path, record)
    all_sessions = get_all_sessions(data_path)
    assert len(all_sessions) == 6  # Total sessions should be 1 + 2 + 3 = 6, regardless of status


def test_get_number_completed_focus_sessions_today(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for today and previous days
    for i in range(5):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60,
            actual_duration=25 * 60,
            started_at= (_today_midnight() + timedelta(hours=10, minutes=0)).isoformat(),
            ended_at= (_today_midnight() + timedelta(hours=10, minutes=25)).isoformat(),
            status="completed",
            session_type="focus"
        )
        save_session(data_path, record)
    today_sessions = get_number_completed_focus_sessions_today(data_path)
    assert today_sessions == 5  # Only the session for today should be returned


def test_get_number_completed_focus_sessions_today_no_sessions(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    today_sessions = get_number_completed_focus_sessions_today(data_path)
    assert today_sessions == 0  # No sessions, so should return 0


def test_get_number_completed_focus_sessions_today_all_old(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 5 days, all older than today
    for i in range(4):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60,
            actual_duration=25 * 60,
            started_at= (_today_midnight() - timedelta(days=4-i) + timedelta(hours=10, minutes=0)).isoformat(),
            ended_at= (_today_midnight() - timedelta(days=4-i) + timedelta(hours=10, minutes=25)).isoformat(),
            status="completed",
            session_type="focus"
        )
        save_session(data_path, record)
    today_sessions = get_number_completed_focus_sessions_today(data_path)
    assert today_sessions == 0  # All sessions are old, so should return 0


def test_get_number_completed_focus_sessions_today_mixed_session_types(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for today and previous days, with a mix of focus and break sessions
    for i in range(5):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60 if i % 2 == 0 else 5 * 60,
            actual_duration=25 * 60 if i % 2 == 0 else 5 * 60,
            started_at= (_today_midnight() + timedelta(hours=10, minutes=0)).isoformat(),
            ended_at= (_today_midnight() + timedelta(hours=10, minutes=25 if i % 2 == 0 else 5)).isoformat(),
            status="completed",
            session_type="focus" if i % 2 == 0 else "break"
        )
        save_session(data_path, record)
    today_sessions = get_number_completed_focus_sessions_today(data_path)
    assert today_sessions == 3  # Only the focus sessions should be counted, so should return 3


def test_get_number_completed_focus_sessions_today_only_breaks(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for today and previous days, all are break sessions
    for i in range(5):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=5 * 60,
            actual_duration=5 * 60,
            started_at= (_today_midnight() - timedelta(days=4-i) + timedelta(hours=10, minutes=0)).isoformat(),
            ended_at= (_today_midnight() - timedelta(days=4-i) + timedelta(hours=10, minutes=5)).isoformat(),
            status="completed",
            session_type="break"
        )
        save_session(data_path, record)
    today_sessions = get_number_completed_focus_sessions_today(data_path)
    assert today_sessions == 0  # All sessions are breaks, so should return 0


def test_get_number_completed_focus_sessions_today_with_interrupted(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for today and previous days, with a mix of completed and interrupted sessions
    for i in range(5):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60,
            actual_duration=25 * 60 if i % 2 == 0 else 10 * 60,
            started_at= (_today_midnight() + timedelta(hours=10, minutes=0)).isoformat(),
            ended_at= (_today_midnight() + timedelta(hours=10, minutes=25 if i % 2 == 0 else 10)).isoformat() if i % 2 == 0 else f"2024-01-0{5-i}T10:10:00",
            status="completed" if i % 2 == 0 else "interrupted",
            session_type="focus"
        )
        save_session(data_path, record)
    today_sessions = get_number_completed_focus_sessions_today(data_path)
    assert today_sessions == 3  # Completed focus sessions should be counted, so should return 3


def test_get_number_completed_focus_sessions_today_since_last_long_break(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for today and previous days, with a break session in between
    for i in range(5):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60 if i % 2 == 0 else 15 * 60,
            actual_duration=25 * 60 if i % 2 == 0 else 15 * 60,
            started_at= (_today_midnight() + timedelta(hours=10 + i, minutes=0)).isoformat(),
            ended_at= (_today_midnight() + timedelta(hours=10 + i, minutes=25 if i % 2 == 0 else 15)).isoformat(),
            status="completed",
            session_type="focus" if i != 2 else "break"  # 3rd session is a break session, so should reset the count of focus sessions since the last long break session
        )
        save_session(data_path, record)
    sessions_since_break = get_number_completed_focus_sessions_today_since_last_long_break(data_path, 15)
    assert sessions_since_break == 2  # Should count the two focus sessions on the current day since the break session


def test_get_number_completed_focus_sessions_today_since_last_long_break_no_break(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for today and previous days, with no break session
    for i in range(5):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60,
            actual_duration=25 * 60,
            started_at= (_today_midnight() + timedelta(hours=10 + i, minutes=0)).isoformat(),
            ended_at= (_today_midnight() + timedelta(hours=10, minutes=25)).isoformat(),
            status="completed", 
            session_type="focus"
        )
        save_session(data_path, record)
    sessions_since_break = get_number_completed_focus_sessions_today_since_last_long_break(data_path, 15)
    assert sessions_since_break == 5  # Should count all 5 focus sessions today since there is no break session


def test_get_number_completed_focus_sessions_today_since_last_long_break_only_old_sessions(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for previous days, all are focus sessions
    for i in range(4):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60,
            actual_duration=25 * 60,
            started_at= (_today_midnight() - timedelta(days=4-i) + timedelta(hours=10 + i, minutes=0)).isoformat(),
            ended_at= (_today_midnight() - timedelta(days=4-i) + timedelta(hours=10 + i, minutes=25)).isoformat(),
            status="completed",
            session_type="focus"
        )
        save_session(data_path, record)
    sessions_since_break = get_number_completed_focus_sessions_today_since_last_long_break(data_path, 15)
    assert sessions_since_break == 0  # Should return 0 since there are no focus sessions on the current day since the break session


def test_get_number_completed_focus_sessions_today_since_last_long_break_all_breaks(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for today and previous days, all are break sessions
    for i in range(5):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=5 * 60,
            actual_duration=5 * 60,
            started_at= (_today_midnight() + timedelta(hours=10 + i, minutes=0)).isoformat(),
            ended_at= (_today_midnight() + timedelta(hours=10 + i, minutes=5)).isoformat(),
            status="completed",
            session_type="break"
        )
        save_session(data_path, record)
    sessions_since_break = get_number_completed_focus_sessions_today_since_last_long_break(data_path, 10)
    assert sessions_since_break == 0  # Should return 0 since there are no focus sessions before the last long break session


def test_get_number_completed_focus_sessions_today_since_last_long_break_only_short_breaks_and_focus(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for today and previous days, with a mix of focus sessions and short break sessions, but no long break sessions
    for i in range(5):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=5 * 60 if i % 2 == 1 else 10 * 60,
            actual_duration=5 * 60 if i % 2 == 1 else 10 * 60,
            started_at= (_today_midnight() + timedelta(hours=10 + i, minutes=0)).isoformat(),
            ended_at= (_today_midnight() + timedelta(hours=10 + i, minutes=5 if i % 2 == 1 else 10)).isoformat(),
            status="completed",
            session_type="break" if i == 1 else "focus"
        )
        save_session(data_path, record)
    sessions_since_break = get_number_completed_focus_sessions_today_since_last_long_break(data_path, 15)
    assert sessions_since_break == 4  # Should count all 5 focus sessions today (not the short break session) since there are no long break sessions


def test_get_number_completed_focus_sessions_today_since_last_long_break_mixed_session_types(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for today and previous days, with a mix of focus and break sessions
    for i in range(5):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60 if i == 4 else 5 * 60,
            actual_duration=25 * 60 if i == 4 else 5 * 60,
            started_at= (_today_midnight() + timedelta(hours=10 + i, minutes=0)).isoformat(),
            ended_at= (_today_midnight() + timedelta(hours=10 + i, minutes=25 if i % 2 == 0 else 5)).isoformat(),
            status="completed",
            session_type="focus" if i % 2 == 0 else "break"
        )
        save_session(data_path, record)
    sessions_since_break = get_number_completed_focus_sessions_today_since_last_long_break(data_path, 5)
    assert sessions_since_break == 1  # Should count the one focus session since the last long break session.


def test_get_number_completed_focus_sessions_today_since_last_long_break_with_interrupted(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for today and previous days, with a mix of completed and interrupted sessions, and a break session in between
    for i in range(5):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60 if i != 2 else 15 * 60,
            actual_duration=25 * 60 if i % 2 == 0 else 15 * 60,
            started_at= (_today_midnight() + timedelta(hours=10 + i, minutes=0)).isoformat(),
            ended_at= (_today_midnight() + timedelta(hours=10 + i, minutes=25 if i % 2 == 0 else 15)).isoformat() if i % 2 == 0 else f"2024-01-0{5-i}T10:10:00",
            status="completed" if i % 2 == 0 else "interrupted",
            session_type="focus" if i != 2 else "break"  # Day 2 is a break session
        )
        save_session(data_path, record)
    sessions_since_break = get_number_completed_focus_sessions_today_since_last_long_break(data_path, 10) 
    assert sessions_since_break == 1  # Should count the one completed focus session since the break session


def test_get_most_focus_min(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 3 days with varying focus minutes
    for i in range(3):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60,
            actual_duration=25 * (i + 1) * 60,  # Day 0 has 25 mins, Day 1 has 50 mins, Day 2 has 75 mins
            started_at=f"2024-01-0{i+1}T10:00:00",
            ended_at=f"2024-01-0{i+1}T10:25:00" if i == 0 else f"2024-01-0{i+1}T10:{25 * (i + 1) % 60:02d}:00",
            status="completed",
            session_type="focus"
        )
        save_session(data_path, record)
    most_focus_min = get_most_focus_min(data_path, include_interrupted=False)
    assert most_focus_min == 75  # The maximum focus minutes in a single session should be 75


def test_get_most_focus_min_with_interrupted(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 3 days with varying focus minutes, including an interrupted session
    for i in range(3):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60,
            actual_duration=25 * (i + 1) * 60 if i != 1 else 10 * 60,  # Day 0 has 25 mins, Day 1 has 10 mins (interrupted), Day 2 has 75 mins
            started_at=f"2024-01-0{i+1}T10:00:00",
            ended_at=f"2024-01-0{i+1}T10:25:00" if i == 0 else f"2024-01-0{i+1}T10:{25 * (i + 1) % 60:02d}:00",
            status="completed" if i != 1 else "interrupted",
            session_type="focus"
        )
        save_session(data_path, record)
    most_focus_min = get_most_focus_min(data_path, include_interrupted=True)
    assert most_focus_min == 75  # The maximum focus minutes in a single session should still be 75, even with the interrupted session included


def test_get_most_focus_min_only_breaks(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 3 days, all are break sessions
    for i in range(3):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=5 * 60,
            actual_duration=5 * 60,
            started_at=f"2024-01-0{i+1}T10:00:00",
            ended_at=f"2024-01-0{i+1}T10:05:00",
            status="completed",
            session_type="break"
        )
        save_session(data_path, record)
    most_focus_min = get_most_focus_min(data_path, include_interrupted=True)
    assert most_focus_min == 0  # All sessions are breaks, so maximum focus minutes should be 0


def test_get_most_focus_min_no_interrupted_mixed_session_types(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 3 days with a mix of focus and break sessions
    for i in range(3):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60 if i % 2 == 0 else 5 * 60,
            actual_duration=25 * 60 if i % 2 == 0 else 5 * 60,
            started_at=f"2024-01-0{i+1}T10:00:00",
            ended_at=f"2024-01-0{i+1}T10:25:00" if i % 2 == 0 else f"2024-01-0{i+1}T10:05:00",
            status="completed",
            session_type="focus" if i % 2 == 0 else "break"
        )
        save_session(data_path, record)
    most_focus_min = get_most_focus_min(data_path, include_interrupted=False)
    assert most_focus_min == 25  # The maximum focus minutes in a single session should be 25, since the break sessions should not be counted


def test_get_most_focus_min_with_interrupted_mixed_session_types(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 3 days with a mix of focus and break sessions, including an interrupted session
    for i in range(3):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60 if i % 2 == 0 else 5 * 60,
            actual_duration=25 * 60 if i % 2 == 0 else 5 * 60 if i != 1 else 10 * 60,
            started_at=f"2024-01-0{i+1}T10:00:00",
            ended_at=f"2024-01-0{i+1}T10:25:00" if i % 2 == 0 else f"2024-01-0{i+1}T10:05:00",
            status="completed" if i != 1 else "interrupted",
            session_type="focus" if i % 2 == 0 else "break"
        )
        save_session(data_path, record)
    most_focus_min = get_most_focus_min(data_path, include_interrupted=True)
    assert most_focus_min == 25  # The maximum focus minutes in a single session should still be 25, since the break sessions should not be counted, even with the interrupted session included


def test_get_total_focus_mins(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 3 days with varying focus minutes
    for i in range(3):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60,
            actual_duration=25 * (i + 1) * 60,  # Day 0 has 25 mins, Day 1 has 50 mins, Day 2 has 75 mins
            started_at=f"2024-01-0{i+1}T10:00:00",
            ended_at=f"2024-01-0{i+1}T10:25:00" if i == 0 else f"2024-01-0{i+1}T10:{25 * (i + 1) % 60:02d}:00",
            status="completed",
            session_type="focus"
        )
        save_session(data_path, record)
    total_focus_mins = get_total_focus_mins(data_path, include_interrupted=False)
    assert total_focus_mins == 150  # The total focus minutes across all sessions should be 25 + 50 + 75 = 150


def test_get_total_focus_mins_with_interrupted(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 3 days with varying focus minutes, including an interrupted session
    for i in range(3):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60,
            actual_duration=25 * 60 if i != 1 else 10 * 60,  # Day 0 has 25 mins, Day 1 has 10 mins (interrupted), Day 2 has 75 mins
            started_at=f"2024-01-0{i+1}T10:00:00",
            ended_at=f"2024-01-0{i+1}T10:25:00" if i == 0 else f"2024-01-0{i+1}T10:{25 * (i + 1) % 60:02d}:00",
            status="completed" if i != 1 else "interrupted",
            session_type="focus"
        )
        save_session(data_path, record)
    total_focus_mins = get_total_focus_mins(data_path, include_interrupted=True)
    assert total_focus_mins == 60  # The total focus minutes across all sessions should be 25 + 10 + 25 = 60, including the interrupted session


def test_get_total_focus_mins_only_breaks(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 3 days, all are break sessions
    for i in range(3):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=5 * 60,
            actual_duration=5 * 60,
            started_at=f"2024-01-0{i+1}T10:00:00",
            ended_at=f"2024-01-0{i+1}T10:05:00",
            status="completed",
            session_type="break"
        )
        save_session(data_path, record)
    total_focus_mins = get_total_focus_mins(data_path, include_interrupted=True)
    assert total_focus_mins == 0  # All sessions are breaks, so total focus minutes should be 0


def test_get_total_focus_mins_no_interrupted_mixed_session_types(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 3 days with a mix of focus and break sessions
    for i in range(3):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60 if i % 2 == 0 else 5 * 60,
            actual_duration=25 * 60 if i % 2 == 0 else 5 * 60,
            started_at=f"2024-01-0{i+1}T10:00:00",
            ended_at=f"2024-01-0{i+1}T10:25:00" if i % 2 == 0 else f"2024-01-0{i+1}T10:05:00",
            status="completed",
            session_type="focus" if i % 2 == 0 else "break"
        )
        save_session(data_path, record)
    total_focus_mins = get_total_focus_mins(data_path, include_interrupted=False)
    assert total_focus_mins == 50  # Only the focus sessions on even days should be counted, so total should be 25 + 25 = 50


def test_get_total_focus_mins_with_interrupted_mixed_session_types(tmp_path: Path) -> None:
    data_path = tmp_path / "sessions.json"
    # Create records for 3 days with a mix of focus and break sessions, including an interrupted session
    for i in range(3):
        record = SessionRecord(
            id=str(i), 
            task=f"Task {i}",
            planned_duration=25 * 60,
            actual_duration=25 * 60 if i != 1 else 10 * 60,  # Day 1 has an interrupted session with 10 mins
            started_at=f"2024-01-0{i+1}T10:00:00",
            ended_at=f"2024-01-0{i+1}T10:25:00" if i % 2 == 0 else f"2024-01-0{i+1}T10:05:00",
            status="completed" if i != 1 else "interrupted",
            session_type="focus" if i != 1 else "break"
        )
        save_session(data_path, record)
    total_focus_mins = get_total_focus_mins(data_path, include_interrupted=True)
    assert total_focus_mins == 50  # The total focus minutes should be 25 (day 0) + 25 (day 2) = 50

