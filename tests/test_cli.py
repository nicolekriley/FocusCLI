'''
Test functionality for helper functions in cli.py
'''
from focus.cli import OnTickFn, run_session_loop, trigger_session_and_break, trigger_session
from focus.storage import get_all_sessions


from rich.console import Console

def test_trigger_session_complete(tmp_path) -> None:
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        return duration, "completed"
    
    def fake_reflection(console: Console) -> str:
        return "test reflection"
    
    status = trigger_session(Console(), 1, "Test Task", tmp_path / ".focus_data.json", "focus", _countdown_function=fake_countdown, _reflection_function=fake_reflection)
    assert status == "completed"

    # Check that the session record was saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 1

    session = records[0]
    assert session["session_type"] == "focus"
    assert session["task"] == "Test Task"
    assert session["status"] == "completed"


def test_trigger_session_interrupted(tmp_path) -> None:
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        return duration, "interrupted"

    def fake_reflection(console: Console) -> str:
        return "test reflection"
    
    status = trigger_session(Console(), 1, "Test Task", tmp_path / ".focus_data.json", "focus", _countdown_function=fake_countdown, _reflection_function=fake_reflection)
    assert status == "interrupted"

    # Check that the session record was saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 1

    session = records[0]
    assert session["session_type"] == "focus"
    assert session["task"] == "Test Task"
    assert session["status"] == "interrupted"


def test_trigger_session_and_break_complete(tmp_path) -> None: 
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        return duration, "completed"

    def fake_reflection(console: Console) -> str:
        return "test reflection"

    status = trigger_session_and_break(Console(), 1, "Test Task", 1, _countdown_function=fake_countdown, _reflection_function=fake_reflection)
    assert status == "completed"

    # Check that the session records were saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 2 

    session = records[0]
    assert session["session_type"] == "focus"
    assert session["task"] == "Test Task"
    assert session["status"] == "completed"

    session_break = records[1]
    assert session_break["session_type"] == "break"
    assert session_break["task"] == "Test Task  - Break"
    assert session_break["status"] == "completed"


def test_trigger_session_and_break_focus_interrupted(tmp_path) -> None: 
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        return duration, "interrupted"

    def fake_reflection(console: Console) -> str:
        return "test reflection"

    status = trigger_session_and_break(1, "Test Task", 1, _countdown_function=fake_countdown, _reflection_function=fake_reflection)
    assert status == "interrupted"

    # Check that the session records were saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 1 # should only save the focus session, not the break session

    session = records[0]
    assert session["session_type"] == "focus"
    assert session["task"] == "Test Task"
    assert session["status"] == "interrupted"


def test_trigger_session_and_break_break_interrupted(tmp_path) -> None: 
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        if duration == 1:
            return duration, "completed"  # Focus session completes
        else:
            return duration, "interrupted"  # Break session is interrupted

    def fake_reflection(console: Console) -> str:
        return "test reflection"

    status = trigger_session_and_break(1, "Test Task", 1, _countdown_function=fake_countdown, _reflection_function=fake_reflection)
    assert status == "interrupted"

    # Check that the session records were saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 2  # Both focus and break sessions should be saved

    focus_session = records[0]
    assert focus_session["session_type"] == "focus"
    assert focus_session["task"] == "Test Task"
    assert focus_session["status"] == "completed"

    break_session = records[1]
    assert break_session["session_type"] == "break"
    assert break_session["task"] == "Test Task  - Break"
    assert break_session["status"] == "interrupted"


def test_run_session_loop_complete(tmp_path) -> None:
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        return duration, "completed"

    def fake_reflection(console: Console) -> str:
        return "test reflection"
    
    def fake_continue_to_next_session() -> bool:
        return True  # Always continue for testing
    
    def fake_exit_multi_session(console: Console) -> None:
        pass  # Do nothing for testing

    run_session_loop(2, 1, "Test Task", 1, False, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _continue_function=fake_continue_to_next_session, _exit_multi_function=fake_exit_multi_session)

    # Check that the session records were saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 4  # 2 focus sessions and 2 break sessions

    for i in range(2):
        focus_session = records[i * 2]
        break_session = records[i * 2 + 1]

        assert focus_session["session_type"] == "focus"
        assert focus_session["task"] == "Test Task"
        assert focus_session["status"] == "completed"

        assert break_session["session_type"] == "break"
        assert break_session["task"] == "Test Task  - Break"
        assert break_session["status"] == "completed"


def run_session_loop_completed_no_break(tmp_path) -> None:
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        return duration, "completed"

    def fake_reflection(console: Console) -> str:
        return "test reflection"
    
    def fake_continue_to_next_session() -> bool:
        return True  # Always continue for testing
    
    def fake_exit_multi_session(console: Console) -> None:
        pass  # Do nothing for testing

    run_session_loop(2, 1, "Test Task", 1, True, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _continue_function=fake_continue_to_next_session, _exit_multi_function=fake_exit_multi_session)

    # Check that the session records were saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 2  # Only 2 focus sessions, no break sessions

    for i in range(2):
        focus_session = records[i]

        assert focus_session["session_type"] == "focus"
        assert focus_session["task"] == "Test Task"
        assert focus_session["status"] == "completed"


def test_run_session_loop_not_continue(tmp_path) -> None:
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        return duration, "completed"

    def fake_reflection(console: Console) -> str:
        return "test reflection"
    
    def fake_continue_to_next_session() -> bool:
        return False  # Stop after the first cycle for testing
    
    def fake_exit_multi_session(console: Console) -> None:
        pass  # Do nothing for testing

    run_session_loop(2, 1, "Test Task", 1, False, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _continue_function=fake_continue_to_next_session, _exit_multi_function=fake_exit_multi_session)

    # Check that the session records were saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 2  # Only the first focus and break sessions should be saved

    focus_session = records[0]
    break_session = records[1]

    assert focus_session["session_type"] == "focus"
    assert focus_session["task"] == "Test Task"
    assert focus_session["status"] == "completed"

    assert break_session["session_type"] == "break"
    assert break_session["task"] == "Test Task  - Break"
    assert break_session["status"] == "completed"


def test_run_session_loop_focus_interrupted(tmp_path) -> None:
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        return duration, "interrupted"

    def fake_reflection(console: Console) -> str:
        return "test reflection"
    
    def fake_exit_multi(console: Console) -> None:
        pass  # Do nothing for testing

    def fake_continue() -> bool:
        return True  # Always continue for testing

    run_session_loop(2, 1, "Test Task", 1, False, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _exit_multi_function=fake_exit_multi, _continue_function=fake_continue)

    # Check that the session records were saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 1  # Only the first focus session should be saved

    focus_session = records[0]
    assert focus_session["session_type"] == "focus"
    assert focus_session["task"] == "Test Task"
    assert focus_session["status"] == "interrupted"


def test_run_session_loop_break_interrupted(tmp_path) -> None:
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        if duration == 1:
            return duration, "completed"  # Focus session completes
        else:
            return duration, "interrupted"  # Break session is interrupted

    def fake_reflection(console: Console) -> str:
        return "test reflection"
    
    def fake_exit_multi(console: Console) -> None:
        pass  # Do nothing for testing

    def fake_continue() -> bool:
        return True  # Always continue for testing

    run_session_loop(2, 1, "Test Task", 1, False, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _exit_multi_function=fake_exit_multi, _continue_function=fake_continue)

    # Check that the session records were saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 2  # One focus session and one break session

    focus_session_1 = records[0]
    break_session_1 = records[1]

    assert focus_session_1["session_type"] == "focus"
    assert focus_session_1["task"] == "Test Task - Cycle 1"
    assert focus_session_1["status"] == "completed"

    assert break_session_1["session_type"] == "break"
    assert break_session_1["task"] == "Test Task - Cycle 1 - Break" 
    assert break_session_1["status"] == "interrupted"


def test_run_session_loop_no_break(tmp_path) -> None:
    def fake_countdown(duration: float, on_tick: OnTickFn, tick_interval: float=1.0) -> tuple[float, str]:
        return duration, "completed"

    def fake_reflection(console: Console) -> str:
        return "test reflection"
    
    def fake_continue_to_next_session() -> bool:
        return True  # Always continue for testing
    
    def fake_exit_multi_session(console: Console) -> None:
        pass  # Do nothing for testing

    run_session_loop(2, 1, "Test Task", 1, True, _countdown_function=fake_countdown, _reflection_function=fake_reflection, _continue_function=fake_continue_to_next_session, _exit_multi_function=fake_exit_multi_session)

    # Check that the session records were saved correctly
    records = get_all_sessions(tmp_path / ".focus_data.json")
    assert len(records) == 2  # Only 2 focus sessions, no break sessions

    for i in range(2):
        focus_session = records[i]

        assert focus_session["session_type"] == "focus"
        assert focus_session["task"] == "Test Task" + f" - Cycle {i+1}"
        assert focus_session["status"] == "completed"