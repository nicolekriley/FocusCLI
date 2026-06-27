'''
Test functionality for helper functions in cli.py
'''
from focus.cli import OnTickFn, run_session_loop, trigger_session_and_break, trigger_session
from focus.storage import get_all_sessions
from focus.config import FocusConfig
from rich.console import Console
import io
from pathlib import Path
import pytest 
from unittest.mock import Mock

@pytest.fixture
def cfg(tmp_path: Path) -> FocusConfig:
    return FocusConfig(
        focus_minutes=1,
        break_minutes=2,
        long_break_minutes=5,
        long_focus_minutes=3,
        cycles=2,
        data_path= tmp_path / "test_data.json",
    )

# module level helpers for simple functions 
def always_complete(duration: float, on_tick: OnTickFn, tick_interval: float = 1.0) -> tuple[float, str]:
    return duration, "completed"

def always_interrupt(duration: float, on_tick: OnTickFn, tick_interval: float = 1.0) -> tuple[float, str]:
    return 0, "interrupted"

def fake_reflection(console: Console) -> str:
    return "test reflection"

def no_sessions_since_long_break(data_path: Path, long_break_minutes: int) -> int:
    return 0

def accept_long_break(console: Console, cycles: int, break_duration: int, long_break_minutes: int) -> bool:
    return True 

def decline_long_break(console: Console, cycles: int, break_duration: int, long_break_minutes: int) -> bool:
    return False

def continue_to_session() -> bool: 
    return True 

def decline_to_continue() -> bool:
    return False 

def test_trigger_session_complete(cfg: FocusConfig) -> None:
    
    console = Console(file=io.StringIO(), force_terminal=False)
    
    status = trigger_session(console, 1, "Test Task", cfg.data_path, "focus", _countdown_function=always_complete, _reflection_function=fake_reflection)
    assert status == "completed"

    # Check that the session record was saved correctly
    records = get_all_sessions(cfg.data_path)
    assert len(records) == 1

    session = records[0]
    assert session["session_type"] == "focus"
    assert session["task"] == "Test Task"
    assert session["status"] == "completed"
    assert session["planned_duration"] == 1 * 60  # Convert minutes to seconds
    assert session["actual_duration"] == 1 * 60 # Convert minutes to seconds
    assert "reflection" in session
    if "reflection" in session:
        assert session["reflection"] == "test reflection"


def test_trigger_session_interrupted(cfg: FocusConfig) -> None:
    
    console = Console(file=io.StringIO(), force_terminal=False)
    
    status = trigger_session(console, 1, "Test Task", cfg.data_path, "focus", _countdown_function=always_interrupt, _reflection_function=fake_reflection)
    assert status == "interrupted"

    # Check that the session record was saved correctly
    records = get_all_sessions(cfg.data_path)
    assert len(records) == 1

    session = records[0]
    assert session["session_type"] == "focus"
    assert session["task"] == "Test Task"
    assert session["status"] == "interrupted"
    assert session["planned_duration"] == 1 * 60 # Convert minutes to seconds
    assert session["actual_duration"] == 0 * 60 # Convert minutes to seconds
    assert "reflection" in session
    if "reflection" in session:
        assert session["reflection"] == "test reflection"


def test_trigger_session_and_break_complete(cfg: FocusConfig) -> None: 

    console = Console(file=io.StringIO(), force_terminal=False)
    status = trigger_session_and_break(console, 1, "Test Task", 1, cfg, _countdown_function=always_complete, _reflection_function=fake_reflection, _sessions_since_break_function=no_sessions_since_long_break, _long_break_notification_function=decline_long_break)
    assert status == "completed"

    # Check that the session records were saved correctly
    records = get_all_sessions(cfg.data_path)
    assert len(records) == 2 

    session = records[0]
    assert session["session_type"] == "focus"
    assert session["task"] == "Test Task"
    assert session["status"] == "completed"
    assert session["planned_duration"] == 1 * 60 # Convert minutes to seconds
    assert session["actual_duration"] == 1 * 60 # Convert minutes to seconds
    assert "reflection" in session
    if "reflection" in session:
        assert session["reflection"] == "test reflection"

    session_break = records[1]
    assert session_break["session_type"] == "break"
    assert session_break["task"] == "Test Task - Break"
    assert session_break["status"] == "completed"
    assert session_break["planned_duration"] == 1 * 60 # Convert minutes to seconds
    assert session_break["actual_duration"] == 1 * 60 # Convert minutes to seconds
    assert "reflection" in session_break
    if "reflection" in session_break:
        assert session_break["reflection"] == "test reflection"


def test_trigger_session_and_break_focus_interrupted(cfg: FocusConfig) -> None: 
    
    console = Console(file=io.StringIO(), force_terminal=False)
    status = trigger_session_and_break(console, 1, "Test Task", 1, cfg, _countdown_function=always_interrupt, _reflection_function=fake_reflection, _sessions_since_break_function=no_sessions_since_long_break, _long_break_notification_function=decline_long_break)
    assert status == "interrupted"

    # Check that the session records were saved correctly
    records = get_all_sessions(cfg.data_path)
    assert len(records) == 1 # should only save the focus session, not the break session

    session = records[0]
    assert session["session_type"] == "focus"
    assert session["task"] == "Test Task"
    assert session["status"] == "interrupted"
    assert session["planned_duration"] == 1 * 60 # Convert minutes to seconds
    assert session["actual_duration"] == 0 * 60 # Convert minutes to seconds
    assert "reflection" in session
    if "reflection" in session:
        assert session["reflection"] == "test reflection"


def test_trigger_session_and_break_break_interrupted(cfg: FocusConfig) -> None: 
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        if duration == 1.0 * 60: #Focus session duration in seconds
            return duration, "completed"  # Focus session completes
        else:
            return 0, "interrupted"  # Break session is interrupted

    console = Console(file=io.StringIO(), force_terminal=False)
    status = trigger_session_and_break(console, 1, "Test Task", 2, cfg, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _sessions_since_break_function=no_sessions_since_long_break, _long_break_notification_function=decline_long_break)
    assert status == "interrupted"

    # Check that the session records were saved correctly
    records = get_all_sessions(cfg.data_path)
    assert len(records) == 2  # Both focus and break sessions should be saved

    focus_session = records[0]
    assert focus_session["session_type"] == "focus"
    assert focus_session["task"] == "Test Task"
    assert focus_session["status"] == "completed"
    assert focus_session["planned_duration"] == 1 * 60 # Convert minutes to seconds
    assert focus_session["actual_duration"] == 1 * 60 # Convert minutes to seconds
    assert "reflection" in focus_session
    if "reflection" in focus_session:
        assert focus_session["reflection"] == "test reflection"

    break_session = records[1]
    assert break_session["session_type"] == "break"
    assert break_session["task"] == "Test Task - Break"
    assert break_session["status"] == "interrupted"
    assert break_session["planned_duration"] == 2 * 60 # Convert minutes to seconds
    assert break_session["actual_duration"] == 0 * 60 # Convert minutes to seconds
    assert "reflection" in break_session
    if "reflection" in break_session:
        assert break_session["reflection"] == "test reflection"


def test_trigger_session_and_break_with_long_break_notification_accept_complete(cfg: FocusConfig) -> None:
    
    def fake_break_sessions_since_last_long_break(data_path: Path, long_break_minutes: int) -> int:
        return cfg.cycles  # For testing, always return default cycles to trigger a long break

    console = Console(file=io.StringIO(), force_terminal=False)
    status = trigger_session_and_break(console, 1, "Test Task", 2, cfg, _countdown_function=always_complete, _reflection_function=fake_reflection, _sessions_since_break_function=fake_break_sessions_since_last_long_break, _long_break_notification_function=accept_long_break)
    assert status == "completed"

    # Check that the session records were saved correctly
    records = get_all_sessions(cfg.data_path)
    assert len(records) == 2  # Both focus and break sessions should be saved

    focus_session = records[0]
    assert focus_session["session_type"] == "focus"
    assert focus_session["task"] == "Test Task"
    assert focus_session["status"] == "completed"
    assert focus_session["planned_duration"] == 1 * 60 # Convert minutes to seconds
    assert focus_session["actual_duration"] == 1 * 60 # Convert minutes to seconds
    assert "reflection" in focus_session
    if "reflection" in focus_session:
        assert focus_session["reflection"] == "test reflection"

    break_session = records[1]
    assert break_session["session_type"] == "break"
    assert break_session["task"] == "Test Task - Break"
    assert break_session["status"] == "completed"
    assert break_session["planned_duration"] == cfg.long_break_minutes * 60 # Convert minutes to seconds (long break)
    assert break_session["actual_duration"] == cfg.long_break_minutes * 60 # Convert minutes to seconds (long break)
    assert "reflection" in break_session
    if "reflection" in break_session:
        assert break_session["reflection"] == "test reflection"


def test_trigger_session_and_break_with_long_break_notification_decline_focus_complete_break_interrupted(cfg: FocusConfig) -> None:
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        if duration == 1.0 * 60: #Focus session duration in seconds
            return duration, "completed"  # Focus session completes
        else:
            return 0, "interrupted"  # Break session is interrupted
    
    def fake_break_sessions_since_last_long_break(data_path: Path, long_break_minutes: int) -> int:
        return cfg.cycles  # For testing, always return 4 to trigger long break notification

    console = Console(file=io.StringIO(), force_terminal=False)
    status = trigger_session_and_break(console, 1, "Test Task", 2, cfg, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _sessions_since_break_function=fake_break_sessions_since_last_long_break, _long_break_notification_function=decline_long_break)
    assert status == "interrupted"

    # Check that the session records were saved correctly
    records = get_all_sessions(cfg.data_path)
    assert len(records) == 2  # Both focus and break sessions should be saved

    focus_session = records[0]
    assert focus_session["session_type"] == "focus"
    assert focus_session["task"] == "Test Task"
    assert focus_session["status"] == "completed"
    assert focus_session["planned_duration"] == 1 * 60 # Convert minutes to seconds
    assert focus_session["actual_duration"] == 1 * 60 # Convert minutes to seconds
    assert "reflection" in focus_session 
    if "reflection" in focus_session:
        assert focus_session["reflection"] == "test reflection"

    break_session = records[1]
    assert break_session["session_type"] == "break"
    assert break_session["task"] == "Test Task - Break"
    assert break_session["status"] == "interrupted"
    assert break_session["planned_duration"] == 2 * 60 # Convert minutes to seconds (no long break)
    assert break_session["actual_duration"] == 0 * 60 # Convert minutes to seconds (long break)
    assert "reflection" in break_session
    if "reflection" in break_session:
        assert break_session["reflection"] == "test reflection"


def test_run_session_loop_complete(cfg: FocusConfig) -> None:

    console = Console(file=io.StringIO(), force_terminal=False)
    run_session_loop(console, 2, 1, "Test Task", 1, False, cfg, _countdown_function=always_complete, _reflection_function=fake_reflection, _continue_function=continue_to_session, _sessions_since_break_function=no_sessions_since_long_break, _long_break_notification_function=decline_long_break)

    # Check that the session records were saved correctly
    records = get_all_sessions(cfg.data_path)
    assert len(records) == 4  # 2 focus sessions and 2 break sessions

    for i in range(2):
        focus_session = records[i * 2]
        break_session = records[i * 2 + 1]

        assert focus_session["session_type"] == "focus"
        assert focus_session["task"] == f"Test Task - Cycle {i+1}"
        assert focus_session["status"] == "completed"
        assert focus_session["planned_duration"] == 1 * 60 # Convert minutes to seconds
        assert focus_session["actual_duration"] == 1 * 60 # Convert minutes to seconds
        assert "reflection" in focus_session
        if "reflection" in focus_session:
            assert focus_session["reflection"] == "test reflection"

        assert break_session["session_type"] == "break"
        assert break_session["task"] == f"Test Task - Cycle {i+1} - Break"
        assert break_session["status"] == "completed"
        assert break_session["planned_duration"] == 1 * 60 # Convert minutes to seconds
        assert break_session["actual_duration"] == 1 * 60 # Convert minutes to seconds
        assert "reflection" in break_session
        if "reflection" in break_session:
            assert break_session["reflection"] == "test reflection"


def test_run_session_loop_completed_no_break(cfg: FocusConfig) -> None:
     
    console = Console(file=io.StringIO(), force_terminal=False)
    run_session_loop(console, 2, 1, "Test Task", 1, True, cfg, _countdown_function=always_complete, _reflection_function=fake_reflection, _continue_function=continue_to_session, _sessions_since_break_function=no_sessions_since_long_break, _long_break_notification_function=decline_long_break)

    # Check that the session records were saved correctly
    records = get_all_sessions(cfg.data_path)
    assert len(records) == 2  # Only 2 focus sessions, no break sessions

    for i in range(2):
        focus_session = records[i]

        assert focus_session["session_type"] == "focus"
        assert focus_session["task"] == f"Test Task - Cycle {i+1}"
        assert focus_session["status"] == "completed"
        assert focus_session["planned_duration"] == 1 * 60 # Convert minutes to seconds
        assert focus_session["actual_duration"] == 1 * 60 # Convert minutes to seconds
        assert "reflection" in focus_session
        if "reflection" in focus_session:
            assert focus_session["reflection"] == "test reflection"


def test_run_session_loop_interrupted_no_break(cfg: FocusConfig) -> None:

    console = Console(file=io.StringIO(), force_terminal=False)
    run_session_loop(console, 2, 1, "Test Task", 1, True, cfg, _countdown_function=always_interrupt, _reflection_function=fake_reflection, _continue_function=continue_to_session, _sessions_since_break_function=no_sessions_since_long_break, _long_break_notification_function=decline_long_break)

    # Check that the session records were saved correctly
    records = get_all_sessions(cfg.data_path)
    assert len(records) == 1  # the first session is interrupted, so only one record should be saved

    focus_session = records[0]

    assert focus_session["session_type"] == "focus"
    assert focus_session["task"] == "Test Task - Cycle 1"
    assert focus_session["status"] == "interrupted"
    assert focus_session["planned_duration"] == 1 * 60 # Convert minutes to seconds
    assert focus_session["actual_duration"] == 0 * 60 # Convert minutes to seconds
    assert "reflection" in focus_session
    if "reflection" in focus_session:
        assert focus_session["reflection"] == "test reflection"


def test_run_session_loop_not_continue(cfg: FocusConfig) -> None:

    console = Console(file=io.StringIO(), force_terminal=False)
    run_session_loop(console, 2, 1, "Test Task", 1, False, cfg, _countdown_function=always_complete, _reflection_function=fake_reflection, _continue_function=decline_to_continue, _sessions_since_break_function=no_sessions_since_long_break, _long_break_notification_function=decline_long_break)

    # Check that the session records were saved correctly
    records = get_all_sessions(cfg.data_path)
    assert len(records) == 2  # Only the first focus and break sessions should be saved

    focus_session = records[0]
    break_session = records[1]

    assert focus_session["session_type"] == "focus"
    assert focus_session["task"] == "Test Task - Cycle 1"
    assert focus_session["status"] == "completed"
    assert focus_session["planned_duration"] == 1 * 60 # Convert minutes to seconds
    assert focus_session["actual_duration"] == 1 * 60 # Convert minutes to seconds
    assert "reflection" in focus_session
    if "reflection" in focus_session:
        assert focus_session["reflection"] == "test reflection"

    assert break_session["session_type"] == "break"
    assert break_session["task"] == "Test Task - Cycle 1 - Break"
    assert break_session["status"] == "completed"
    assert break_session["planned_duration"] == 1 * 60 # Convert minutes to seconds
    assert break_session["actual_duration"] == 1 * 60 # Convert minutes to seconds
    assert "reflection" in focus_session
    if "reflection" in break_session:
        assert break_session["reflection"] == "test reflection"


def test_run_session_loop_focus_interrupted(cfg: FocusConfig) -> None:
    
    console = Console(file=io.StringIO(), force_terminal=False)
    run_session_loop(console, 2, 1, "Test Task", 1, False, cfg, _countdown_function=always_interrupt, _reflection_function=fake_reflection, _continue_function=continue_to_session, _sessions_since_break_function=no_sessions_since_long_break, _long_break_notification_function=decline_long_break)

    # Check that the session records were saved correctly
    records = get_all_sessions(cfg.data_path)
    assert len(records) == 1  # Only the first focus session should be saved

    focus_session = records[0]
    assert focus_session["session_type"] == "focus"
    assert focus_session["planned_duration"] == 1 * 60 # Convert minutes to seconds
    assert focus_session["actual_duration"] == 0 * 60 # Convert minutes to seconds
    assert focus_session["task"] == "Test Task - Cycle 1"
    assert focus_session["status"] == "interrupted"
    assert "reflection" in focus_session
    if "reflection" in focus_session:
        assert focus_session["reflection"] == "test reflection"


def test_run_session_loop_break_interrupted(cfg: FocusConfig) -> None:
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        if duration == 1.0 * 60: #Focus session duration in seconds
            return duration, "completed"  # Focus session completes
        else:
            return 0, "interrupted"  # Break session is interrupted
        
    console = Console(file=io.StringIO(), force_terminal=False)
    run_session_loop(console, 2, 1, "Test Task", 2, False, cfg, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _continue_function=continue_to_session, _sessions_since_break_function=no_sessions_since_long_break, _long_break_notification_function=decline_long_break)

    # Check that the session records were saved correctly
    records = get_all_sessions(cfg.data_path)
    assert len(records) == 2  # One focus session and one break session

    focus_session_1 = records[0]
    break_session_1 = records[1]

    assert focus_session_1["session_type"] == "focus"
    assert focus_session_1["task"] == "Test Task - Cycle 1"
    assert focus_session_1["planned_duration"] == 1 * 60 # Convert minutes to seconds
    assert focus_session_1["actual_duration"] == 1 * 60 # Convert minutes to seconds
    assert focus_session_1["status"] == "completed"
    assert "reflection" in focus_session_1
    if "reflection" in focus_session_1:
        assert focus_session_1["reflection"] == "test reflection"

    assert break_session_1["session_type"] == "break"
    assert break_session_1["task"] == "Test Task - Cycle 1 - Break" 
    assert break_session_1["planned_duration"] == 2 * 60 # Convert minutes to seconds
    assert break_session_1["actual_duration"] == 0 * 60 # Convert minutes to seconds
    assert break_session_1["status"] == "interrupted"
    assert "reflection" in break_session_1
    if "reflection" in break_session_1:
        assert break_session_1["reflection"] == "test reflection"


def test_run_session_loop_no_break(cfg: FocusConfig) -> None:

    console = Console(file=io.StringIO(), force_terminal=False)
    run_session_loop(console, 2, 1, "Test Task", 1, True, cfg, _countdown_function=always_complete, _reflection_function=fake_reflection, _continue_function=continue_to_session, _sessions_since_break_function=no_sessions_since_long_break, _long_break_notification_function=decline_long_break)

    # Check that the session records were saved correctly
    records = get_all_sessions(cfg.data_path)
    assert len(records) == 2  # Only 2 focus sessions, no break sessions

    for i in range(2):
        focus_session = records[i]

        assert focus_session["session_type"] == "focus"
        assert focus_session["task"] == "Test Task" + f" - Cycle {i+1}"
        assert focus_session["planned_duration"] == 1 * 60 # Convert minutes to seconds
        assert focus_session["actual_duration"] == 1 * 60 # Convert minutes to seconds
        assert focus_session["status"] == "completed"
        assert "reflection" in focus_session
        if "reflection" in focus_session:
            assert focus_session["reflection"] == "test reflection"


def test_run_session_loop_focus_interrupt_second_focus(cfg: FocusConfig) -> None:

    fake_countdown = Mock(side_effect =[
        (1.0 * 60, "completed"), # First focus session 
        (2.0 * 60, "completed"), # First break session
        (0, "interrupted") # interrupted on third break call. 
    ])

    console = Console(file=io.StringIO(), force_terminal=False)
    run_session_loop(console, 2, 1, "Test Task", 2, False, cfg, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _continue_function=continue_to_session, _sessions_since_break_function=no_sessions_since_long_break, _long_break_notification_function=decline_long_break)

    # Check that the session records were saved correctly
    records = get_all_sessions(cfg.data_path)
    assert len(records) == 3  # Two focus sessions and one break session

    focus_session_1 = records[0]
    break_session_1 = records[1]
    focus_session_2 = records[2]

    assert focus_session_1["session_type"] == "focus"
    assert focus_session_1["task"] == "Test Task - Cycle 1"
    assert focus_session_1["planned_duration"] == 1 * 60 # Convert minutes to seconds
    assert focus_session_1["actual_duration"] == 1 * 60 # Convert minutes to seconds
    assert focus_session_1["status"] == "completed"
    assert "reflection" in focus_session_1
    if "reflection" in focus_session_1:
        assert focus_session_1["reflection"] == "test reflection"

    assert break_session_1["session_type"] == "break"
    assert break_session_1["task"] == "Test Task - Cycle 1 - Break" 
    assert break_session_1["planned_duration"] == 2 * 60 # Convert minutes to seconds
    assert break_session_1["actual_duration"] == 2 * 60 # Convert minutes to seconds
    assert break_session_1["status"] == "completed"
    assert "reflection" in break_session_1
    if "reflection" in break_session_1:
        assert break_session_1["reflection"] == "test reflection"

    assert focus_session_2["session_type"] == "focus"
    assert focus_session_2["task"] == "Test Task - Cycle 2"
    assert focus_session_2["planned_duration"] == 1 * 60 # Convert minutes to seconds
    assert focus_session_2["actual_duration"] == 0 * 60 # Convert minutes to seconds
    assert focus_session_2["status"] == "interrupted"
    assert "reflection" in focus_session_2
    if "reflection" in focus_session_2:
        assert focus_session_2["reflection"] == "test reflection"


def test_run_session_loop_long_break_notification_accept(cfg: FocusConfig) -> None:
    
    def break_sessions_effect(data_path: Path, long_break_minutes: int) -> int:
        if fake_break_sessions_since_last_long_break.call_count % cfg.cycles != 0:
            return 0 
        return cfg.cycles # For testing return cfg.cycles once cfg.cycles focus sessions have happened
    
    fake_break_sessions_since_last_long_break = Mock(side_effect=break_sessions_effect)

    console = Console(file=io.StringIO(), force_terminal=False)
    run_session_loop(console, 5, 1, "Test Task", 2, False, cfg, _countdown_function=always_complete, _reflection_function=fake_reflection, _continue_function=continue_to_session, _sessions_since_break_function=fake_break_sessions_since_last_long_break, _long_break_notification_function=accept_long_break)

    # Check that the session records were saved correctly
    records = get_all_sessions(cfg.data_path)
    assert len(records) == 10  # Five focus sessions and five break sessions

    for i in range(5):
        focus_session = records[i * 2]
        break_session = records[i * 2 + 1]

        assert focus_session["session_type"] == "focus"
        assert focus_session["task"] == f"Test Task - Cycle {i+1}"
        assert focus_session["planned_duration"] == 1 * 60 # Convert minutes to seconds
        assert focus_session["actual_duration"] == 1 * 60 # Convert minutes to seconds
        assert focus_session["status"] == "completed"
        assert "reflection" in focus_session
        if "reflection" in focus_session:
            assert focus_session["reflection"] == "test reflection"

        assert break_session["session_type"] == "break"
        assert break_session["task"] == f"Test Task - Cycle {i+1} - Break"
        if (i + 1) % cfg.cycles != 0:
            assert break_session["planned_duration"] == 2 * 60 # Convert minutes to seconds
            assert break_session["actual_duration"] == 2 * 60 # Convert minutes to seconds
        else:
            assert break_session["planned_duration"] == cfg.long_break_minutes * 60 # Convert minutes to seconds (long break)
            assert break_session["actual_duration"] == cfg.long_break_minutes * 60 # Convert minutes to seconds (long break)
        assert "reflection" in break_session
        if "reflection" in break_session:
            assert break_session["reflection"] == "test reflection"


def test_run_session_loop_long_break_notification_decline(cfg: FocusConfig) -> None:
    
    def break_sessions_effect(data_path: Path, long_break_minutes: int) -> int:
        if fake_break_sessions_since_last_long_break.call_count < cfg.cycles:
            return 0 
        return cfg.cycles # For testing return cfg.cycles once cfg.cycles focus sessions have happened
    
    fake_break_sessions_since_last_long_break = Mock(side_effect=break_sessions_effect)

    console = Console(file=io.StringIO(), force_terminal=False)
    run_session_loop(console, 5, 1, "Test Task", 2, False, cfg, _countdown_function=always_complete, _reflection_function=fake_reflection, _continue_function=continue_to_session, _sessions_since_break_function=fake_break_sessions_since_last_long_break, _long_break_notification_function=decline_long_break)

    # Check that the session records were saved correctly
    records = get_all_sessions(cfg.data_path)
    assert len(records) == 10  # Five focus sessions and five break sessions

    for i in range(5):
        focus_session = records[i * 2]
        break_session = records[i * 2 + 1]

        assert focus_session["session_type"] == "focus"
        assert focus_session["task"] == f"Test Task - Cycle {i+1}"
        assert focus_session["planned_duration"] == 1 * 60 # Convert minutes to seconds
        assert focus_session["actual_duration"] == 1 * 60 # Convert minutes to seconds
        assert focus_session["status"] == "completed"
        assert "reflection" in focus_session
        if "reflection" in focus_session:
            assert focus_session["reflection"] == "test reflection"

        assert break_session["session_type"] == "break"
        assert break_session["task"] == f"Test Task - Cycle {i+1} - Break"
        assert break_session["planned_duration"] == 2 * 60 # Convert minutes to seconds
        assert break_session["actual_duration"] == 2 * 60 # Convert minutes to seconds
        assert break_session["status"] == "completed"
        assert "reflection" in break_session
        if "reflection" in break_session:
            assert break_session["reflection"] == "test reflection"


def test_run_session_loop_long_break_notification_accept_break_interrupted(cfg: FocusConfig) -> None:

    fake_countdown = Mock(side_effect=[
        (1.0 * 60, "completed"), # first focus session
        (2.0 * 60, "completed"), #first break session
        (1.0 * 60, "completed"),  #second focus session 
        (0 * 60, "interrupted") #second break session (long break) that is interrupted
    ])
    
    def break_sessions_effect(data_path: Path, long_break_minutes: int) -> int:
        if fake_break_sessions_since_last_long_break.call_count % cfg.cycles != 0:
            return 0
        return cfg.cycles # For testing , return cfg.cycles when call count is divisible by cfg.cycles to trigger long break notification

    fake_break_sessions_since_last_long_break = Mock(side_effect=break_sessions_effect)

    console = Console(file=io.StringIO(), force_terminal=False)
    run_session_loop(console, 5, 1, "Test Task", 2, False, cfg, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _continue_function=continue_to_session, _sessions_since_break_function=fake_break_sessions_since_last_long_break, _long_break_notification_function=accept_long_break)

    # Check that the session records were saved correctly
    records = get_all_sessions(cfg.data_path)
    assert len(records) == 2 * cfg.cycles  # Four focus sessions and four break sessions as 4th long break is interrupted

    for i in range(cfg.cycles):
        focus_session = records[i * 2]
        break_session = records[i * 2 + 1]

        assert focus_session["session_type"] == "focus"
        assert focus_session["task"] == f"Test Task - Cycle {i+1}"
        assert focus_session["planned_duration"] == 1 * 60 # Convert minutes to seconds
        assert focus_session["actual_duration"] == 1 * 60 # Convert minutes to seconds
        assert focus_session["status"] == "completed"
        assert "reflection" in focus_session
        if "reflection" in focus_session:
            assert focus_session["reflection"] == "test reflection"

        assert break_session["session_type"] == "break"
        assert break_session["task"] == f"Test Task - Cycle {i+1} - Break"
        if (i + 1) % cfg.cycles != 0:
            assert break_session["planned_duration"] == 2 * 60 # Convert minutes to seconds
            assert break_session["actual_duration"] == 2 * 60 # Convert minutes to seconds
            assert break_session["status"] == "completed"
        else:
            assert break_session["planned_duration"] == cfg.long_break_minutes * 60 # Convert minutes to seconds (long break)
            assert break_session["actual_duration"] == 0 * 60 # Convert minutes to seconds (long break)
            assert break_session["status"] == "interrupted"
        assert "reflection" in break_session
        if "reflection" in break_session:
            assert break_session["reflection"] == "test reflection"


def test_run_session_loop_long_break_notification_decline_break_interrupted(cfg: FocusConfig) -> None:
    
    fake_countdown = Mock(side_effect=[
        (1.0 * 60, "completed"),  # call 1: focus
        (2.0 * 60, "completed"),  # call 2: short break
        (1.0 * 60, "completed"),  # call 3: focus
        (2.0 * 60, "completed"),  # call 4: short break
        (1.0 * 60, "completed"),  # call 5: focus
        (2.0 * 60, "completed"),  # call 6: short break
        (1.0 * 60, "completed"),  # call 7: focus
        (0, "interrupted"),       # call 8: break interrupted (long break declined)
    ])
    
    # fake_break_sessions: behavior depends on call number, so use a side_effect function
    # Note: inside a side_effect function, mock.call_count has already been incremented
    def break_sessions_effect(data_path: Path, long_break_minutes: int) -> int:
        if fake_break_sessions_since_last_long_break.call_count % cfg.cycles != 0:
            return 0
        return cfg.cycles

    fake_break_sessions_since_last_long_break = Mock(side_effect=break_sessions_effect)

    console = Console(file=io.StringIO(), force_terminal=False)
    run_session_loop(console, 5, 1, "Test Task", 2, False, cfg, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _continue_function=continue_to_session, _sessions_since_break_function=fake_break_sessions_since_last_long_break, _long_break_notification_function=decline_long_break)

    # Check that the session records were saved correctly
    records = get_all_sessions(cfg.data_path)
    assert len(records) == 8  

    for i in range(4):
        focus_session = records[i * 2]
        break_session = records[i * 2 + 1]

        assert focus_session["session_type"] == "focus"
        assert focus_session["task"] == f"Test Task - Cycle {i+1}"
        assert focus_session["planned_duration"] == 1 * 60 # Convert minutes to seconds
        assert focus_session["actual_duration"] == 1 * 60 # Convert minutes to seconds
        assert focus_session["status"] == "completed"
        assert "reflection" in focus_session
        if "reflection" in focus_session:
            assert focus_session["reflection"] == "test reflection"

        assert break_session["session_type"] == "break"
        assert break_session["task"] == f"Test Task - Cycle {i+1} - Break"
        if 2 * i + 2 != 8:
            assert break_session["planned_duration"] == 2 * 60 # Convert minutes to seconds
            assert break_session["actual_duration"] == 2 * 60 # Convert minutes to seconds
            assert break_session["status"] == "completed"
        else:
            assert break_session["planned_duration"] == 2 * 60 # Convert minutes to seconds (long break rejected)
            assert break_session["actual_duration"] == 0 * 60 # Convert minutes to seconds (long break rejected)
            assert break_session["status"] == "interrupted"
        assert "reflection" in break_session
        if "reflection" in break_session:
            assert break_session["reflection"] == "test reflection"
