'''
Test functionality for helper functions in cli.py
'''
from zipfile import Path

from focus.cli import OnTickFn, run_session_loop, trigger_session_and_break, trigger_session
from focus.storage import get_all_sessions
from rich.console import Console
import io
from pathlib import Path

def test_trigger_session_complete(tmp_path) -> None:
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        return duration, "completed"
    
    def fake_reflection(console: Console) -> str:
        return "test reflection"
    
    console = Console(file=io.StringIO(), force_terminal=False)
    
    status = trigger_session(console, 1, "Test Task", tmp_path / ".focus_data.json", "focus", _countdown_function=fake_countdown, _reflection_function=fake_reflection)
    assert status == "completed"

    # Check that the session record was saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 1

    session = records[0]
    assert session["session_type"] == "focus"
    assert session["task"] == "Test Task"
    assert session["status"] == "completed"
    assert session["planned_duration"] == 1
    assert session["actual_duration"] == 1
    if "reflection" in session:
        assert session["reflection"] == "test reflection"


def test_trigger_session_interrupted(tmp_path) -> None:
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        return 0, "interrupted"

    def fake_reflection(console: Console) -> str:
        return "test reflection"
    
    console = Console(file=io.StringIO(), force_terminal=False)
    
    status = trigger_session(console, 1, "Test Task", tmp_path / ".focus_data.json", "focus", _countdown_function=fake_countdown, _reflection_function=fake_reflection)
    assert status == "interrupted"

    # Check that the session record was saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 1

    session = records[0]
    assert session["session_type"] == "focus"
    assert session["task"] == "Test Task"
    assert session["status"] == "interrupted"
    assert session["planned_duration"] == 1
    assert session["actual_duration"] == 0
    if "reflection" in session:
        assert session["reflection"] == "test reflection"


def test_trigger_session_and_break_complete(tmp_path) -> None: 
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        return duration, "completed"

    def fake_reflection(console: Console) -> str:
        return "test reflection"
    
    def fakeBreakSessionsSinceLastLongBreak(data_path: Path, long_break_minutes: int) -> int:
        return 0  # For testing, always return 0 to avoid triggering long break notification

    console = Console(file=io.StringIO(), force_terminal=False)
    status = trigger_session_and_break(console, 1, "Test Task", 1, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _sessions_since_break_function=fakeBreakSessionsSinceLastLongBreak)
    assert status == "completed"

    # Check that the session records were saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 2 

    session = records[0]
    assert session["session_type"] == "focus"
    assert session["task"] == "Test Task"
    assert session["status"] == "completed"
    assert session["planned_duration"] == 1
    assert session["actual_duration"] == 1
    if "reflection" in session:
        assert session["reflection"] == "test reflection"

    session_break = records[1]
    assert session_break["session_type"] == "break"
    assert session_break["task"] == "Test Task - Break"
    assert session_break["status"] == "completed"
    assert session_break["planned_duration"] == 1
    assert session_break["actual_duration"] == 1
    if "reflection" in session_break:
        assert session_break["reflection"] == "test reflection"


def test_trigger_session_and_break_focus_interrupted(tmp_path) -> None: 
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        return 0, "interrupted"

    def fake_reflection(console: Console) -> str:
        return "test reflection"
    
    def fakeBreakSessionsSinceLastLongBreak(data_path: Path, long_break_minutes: int) -> int:
        return 0  # For testing, always return 0 to avoid triggering long break notification

    console = Console(file=io.StringIO(), force_terminal=False)
    status = trigger_session_and_break(console, 1, "Test Task", 1, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _sessions_since_break_function=fakeBreakSessionsSinceLastLongBreak)
    assert status == "interrupted"

    # Check that the session records were saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 1 # should only save the focus session, not the break session

    session = records[0]
    assert session["session_type"] == "focus"
    assert session["task"] == "Test Task"
    assert session["status"] == "interrupted"
    assert session["planned_duration"] == 1
    assert session["actual_duration"] == 0
    if "reflection" in session:
        assert session["reflection"] == "test reflection"


def test_trigger_session_and_break_break_interrupted(tmp_path) -> None: 
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        if duration == 1:
            return duration, "completed"  # Focus session completes
        else:
            return 0, "interrupted"  # Break session is interrupted

    def fake_reflection(console: Console) -> str:
        return "test reflection"
    
    def fakeBreakSessionsSinceLastLongBreak(data_path: Path, long_break_minutes: int) -> int:
        return 0  # For testing, always return 0 to avoid triggering long break notification

    console = Console(file=io.StringIO(), force_terminal=False)
    status = trigger_session_and_break(console, 1, "Test Task", 2, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _sessions_since_break_function=fakeBreakSessionsSinceLastLongBreak)
    assert status == "interrupted"

    # Check that the session records were saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 2  # Both focus and break sessions should be saved

    focus_session = records[0]
    assert focus_session["session_type"] == "focus"
    assert focus_session["task"] == "Test Task"
    assert focus_session["status"] == "completed"
    assert focus_session["planned_duration"] == 1
    assert focus_session["actual_duration"] == 1
    if "reflection" in focus_session:
        assert focus_session["reflection"] == "test reflection"

    break_session = records[1]
    assert break_session["session_type"] == "break"
    assert break_session["task"] == "Test Task  - Break"
    assert break_session["status"] == "interrupted"
    assert break_session["planned_duration"] == 2
    assert break_session["actual_duration"] == 0
    if "reflection" in break_session:
        assert break_session["reflection"] == "test reflection"


def test_run_session_loop_complete(tmp_path) -> None:
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        return duration, "completed"

    def fake_reflection(console: Console) -> str:
        return "test reflection"
    
    def fake_continue_to_next_session() -> bool:
        return True  # Always continue for testing
    
    def fakeBreakSessionsSinceLastLongBreak(data_path: Path, long_break_minutes: int) -> int:
        return 0  # For testing, always return 0 to avoid triggering long break notification

    console = Console(file=io.StringIO(), force_terminal=False)
    run_session_loop(console, 2, 1, "Test Task", 1, False, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _continue_function=fake_continue_to_next_session, _sessions_since_break_function=fakeBreakSessionsSinceLastLongBreak)

    # Check that the session records were saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 4  # 2 focus sessions and 2 break sessions

    for i in range(2):
        focus_session = records[i * 2]
        break_session = records[i * 2 + 1]

        assert focus_session["session_type"] == "focus"
        assert focus_session["task"] == f"Test Task - Cycle {i+1}"
        assert focus_session["status"] == "completed"
        assert focus_session["planned_duration"] == 1
        assert focus_session["actual_duration"] == 1
        if "reflection" in focus_session:
            assert focus_session["reflection"] == "test reflection"

        assert break_session["session_type"] == "break"
        assert break_session["task"] == f"Test Task - Cycle {i+1} - Break"
        assert break_session["status"] == "completed"
        assert break_session["planned_duration"] == 1
        assert break_session["actual_duration"] == 1
        if "reflection" in break_session:
            assert break_session["reflection"] == "test reflection"


def test_run_session_loop_completed_no_break(tmp_path) -> None:
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        return duration, "completed"

    def fake_reflection(console: Console) -> str:
        return "test reflection"
    
    def fake_continue_to_next_session() -> bool:
        return True  # Always continue for testing
    
    def fakeBreakSessionsSinceLastLongBreak(data_path: Path, long_break_minutes: int) -> int:
        return 0  # For testing, always return 0 to avoid triggering long break notification

    console = Console(file=io.StringIO(), force_terminal=False)
    run_session_loop(console, 2, 1, "Test Task", 1, True, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _continue_function=fake_continue_to_next_session, _sessions_since_break_function=fakeBreakSessionsSinceLastLongBreak)

    # Check that the session records were saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 2  # Only 2 focus sessions, no break sessions

    for i in range(2):
        focus_session = records[i]

        assert focus_session["session_type"] == "focus"
        assert focus_session["task"] == f"Test Task - Cycle {i+1}"
        assert focus_session["status"] == "completed"
        assert focus_session["planned_duration"] == 1
        assert focus_session["actual_duration"] == 1
        if "reflection" in focus_session:
            assert focus_session["reflection"] == "test reflection"


def test_run_session_loop_interrupted_no_break(tmp_path) -> None:
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        return 0, "interrupted"

    def fake_reflection(console: Console) -> str:
        return "test reflection"
    
    def fake_continue_to_next_session() -> bool:
        return True  # Always continue for testing

    def fakeBreakSessionsSinceLastLongBreak(data_path: Path, long_break_minutes: int) -> int:
        return 0  # For testing, always return 0 to avoid triggering long break notification
    
    console = Console(file=io.StringIO(), force_terminal=False)
    run_session_loop(console, 2, 1, "Test Task", 1, True, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _continue_function=fake_continue_to_next_session, _sessions_since_break_function=fakeBreakSessionsSinceLastLongBreak)

    # Check that the session records were saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 1  # the first session is interrupted, so only one record should be saved

    focus_session = records[0]

    assert focus_session["session_type"] == "focus"
    assert focus_session["task"] == "Test Task - Cycle 1"
    assert focus_session["status"] == "interrupted"
    assert focus_session["planned_duration"] == 1
    assert focus_session["actual_duration"] == 0
    if "reflection" in focus_session:
        assert focus_session["reflection"] == "test reflection"


def test_run_session_loop_not_continue(tmp_path) -> None:
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        return duration, "completed"

    def fake_reflection(console: Console) -> str:
        return "test reflection"
    
    def fake_continue_to_next_session() -> bool:
        return False  # Stop after the first cycle for testing
    
    def fakeBreakSessionsSinceLastLongBreak(data_path: Path, long_break_minutes: int) -> int:
        return 0  # For testing, always return 0 to avoid triggering long break notification

    console = Console(file=io.StringIO(), force_terminal=False)
    run_session_loop(console, 2, 1, "Test Task", 1, False, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _continue_function=fake_continue_to_next_session, _sessions_since_break_function=fakeBreakSessionsSinceLastLongBreak)

    # Check that the session records were saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 2  # Only the first focus and break sessions should be saved

    focus_session = records[0]
    break_session = records[1]

    assert focus_session["session_type"] == "focus"
    assert focus_session["task"] == "Test Task - Cycle 1"
    assert focus_session["status"] == "completed"
    assert focus_session["planned_duration"] == 1
    assert focus_session["actual_duration"] == 1
    if "reflection" in focus_session:
        assert focus_session["reflection"] == "test reflection"

    assert break_session["session_type"] == "break"
    assert break_session["task"] == "Test Task - Cycle 1 - Break"
    assert break_session["status"] == "completed"
    assert break_session["planned_duration"] == 1
    assert break_session["actual_duration"] == 1
    if "reflection" in break_session:
        assert break_session["reflection"] == "test reflection"


def test_run_session_loop_focus_interrupted(tmp_path) -> None:
    
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        return 0, "interrupted"

    def fake_reflection(console: Console) -> str:
        return "test reflection"

    def fake_continue() -> bool:
        return True  # Always continue for testing

    def fakeBreakSessionsSinceLastLongBreak(data_path: Path, long_break_minutes: int) -> int:
        return 0  # For testing, always return 0 to avoid triggering long break notification
    
    console = Console(file=io.StringIO(), force_terminal=False)
    run_session_loop(console, 2, 1, "Test Task", 1, False, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _continue_function=fake_continue, _sessions_since_break_function=fakeBreakSessionsSinceLastLongBreak)

    # Check that the session records were saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 1  # Only the first focus session should be saved

    focus_session = records[0]
    assert focus_session["session_type"] == "focus"
    assert focus_session["planned_duration"] == 1
    assert focus_session["actual_duration"] == 0
    assert focus_session["task"] == "Test Task - Cycle 1"
    assert focus_session["status"] == "interrupted"
    if "reflection" in focus_session:
        assert focus_session["reflection"] == "test reflection"


def test_run_session_loop_break_interrupted(tmp_path) -> None:
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        if duration == 1:
            return duration, "completed"  # Focus session completes
        else:
            return 0, "interrupted"  # Break session is interrupted

    def fake_reflection(console: Console) -> str:
        return "test reflection"

    def fake_continue() -> bool:
        return True  # Always continue for testing
    
    def fakeBreakSessionsSinceLastLongBreak(data_path: Path, long_break_minutes: int) -> int:
        return 0  # For testing, always return 0 to avoid triggering long break notification

    console = Console(file=io.StringIO(), force_terminal=False)
    run_session_loop(console, 2, 1, "Test Task", 2, False, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _continue_function=fake_continue, _sessions_since_break_function=fakeBreakSessionsSinceLastLongBreak)

    # Check that the session records were saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 2  # One focus session and one break session

    focus_session_1 = records[0]
    break_session_1 = records[1]

    assert focus_session_1["session_type"] == "focus"
    assert focus_session_1["task"] == "Test Task - Cycle 1"
    assert focus_session_1["planned_duration"] == 1
    assert focus_session_1["actual_duration"] == 1
    assert focus_session_1["status"] == "completed"
    if "reflection" in focus_session_1:
        assert focus_session_1["reflection"] == "test reflection"

    assert break_session_1["session_type"] == "break"
    assert break_session_1["task"] == "Test Task - Cycle 1 - Break" 
    assert break_session_1["planned_duration"] == 2
    assert break_session_1["actual_duration"] == 0
    assert break_session_1["status"] == "interrupted"
    if "reflection" in break_session_1:
        assert break_session_1["reflection"] == "test reflection"


def test_run_session_loop_no_break(tmp_path) -> None:
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        return duration, "completed"

    def fake_reflection(console: Console) -> str:
        return "test reflection"
    
    def fake_continue_to_next_session() -> bool:
        return True  # Always continue for testing

    def fakeBreakSessionsSinceLastLongBreak(data_path: Path, long_break_minutes: int) -> int:
        return 0  # For testing, always return 0 to avoid triggering long break notification
    
    console = Console(file=io.StringIO(), force_terminal=False)
    run_session_loop(console, 2, 1, "Test Task", 1, True, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _continue_function=fake_continue_to_next_session, _sessions_since_break_function=fakeBreakSessionsSinceLastLongBreak)

    # Check that the session records were saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 2  # Only 2 focus sessions, no break sessions

    for i in range(2):
        focus_session = records[i]

        assert focus_session["session_type"] == "focus"
        assert focus_session["task"] == "Test Task" + f" - Cycle {i+1}"
        assert focus_session["planned_duration"] == 1
        assert focus_session["actual_duration"] == 1
        assert focus_session["status"] == "completed"
        if "reflection" in focus_session:
            assert focus_session["reflection"] == "test reflection"


def test_run_session_loop_focus_interrupt_second_focus(tmp_path):

    # countdown will show as interrupted on the third call, which is the second focus session
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        fake_countdown.counter += 1
        if fake_countdown.counter < 3:
            return duration, "completed"  # session completes
        else: 
            return 0, "interrupted"  # session is interrupted
        
    fake_countdown.counter = 0  # Initialize a counter to track the number of calls

    def fake_reflection(console: Console) -> str:
        return "test reflection"

    def fake_continue() -> bool:
        return True  # Always continue for testing
    
    def fakeBreakSessionsSinceLastLongBreak(data_path: Path, long_break_minutes: int) -> int:
        return 0  # For testing, always return 0 to avoid triggering long break notification

    console = Console(file=io.StringIO(), force_terminal=False)
    run_session_loop(console, 2, 1, "Test Task", 2, False, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _continue_function=fake_continue, _sessions_since_break_function=fakeBreakSessionsSinceLastLongBreak)

    # Check that the session records were saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 3  # Two focus sessions and one break session

    focus_session_1 = records[0]
    break_session_1 = records[1]
    focus_session_2 = records[2]

    assert focus_session_1["session_type"] == "focus"
    assert focus_session_1["task"] == "Test Task - Cycle 1"
    assert focus_session_1["planned_duration"] == 1
    assert focus_session_1["actual_duration"] == 1
    assert focus_session_1["status"] == "completed"
    if "reflection" in focus_session_1:
        assert focus_session_1["reflection"] == "test reflection"

    assert break_session_1["session_type"] == "break"
    assert break_session_1["task"] == "Test Task - Cycle 1 - Break" 
    assert break_session_1["planned_duration"] == 2
    assert break_session_1["actual_duration"] == 2
    assert break_session_1["status"] == "completed"
    if "reflection" in break_session_1:
        assert break_session_1["reflection"] == "test reflection"

    assert focus_session_2["session_type"] == "focus"
    assert focus_session_2["task"] == "Test Task - Cycle 2"
    assert focus_session_2["planned_duration"] == 1
    assert focus_session_2["actual_duration"] == 0
    assert focus_session_2["status"] == "interrupted"
    if "reflection" in focus_session_2:
        assert focus_session_2["reflection"] == "test reflection"
