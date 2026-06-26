'''
cli.py 
Adds in functionality to run the timer and display logic together. Handles user input for starting timers and showing stats.
'''

from __future__ import annotations
from datetime import datetime
from focus.display import (
    show_history_table, 
    show_start_banner, 
    show_complete_banner, 
    show_interrupt_banner, 
    show_stats, 
    show_best_stats, 
    prompt_reflection, 
    long_break_notification, 
    show_config, 
    reset_cancelled, 
    should_reset, 
    reset_successful, 
    no_sessions_found, 
    make_progress_bar, 
    continue_to_next_session,
    exit_multi_session
)
from focus.timer import run_countdown, TimerResult
from focus.storage import (
    SessionRecord, 
    save_session, 
    get_sessions_last_n_days, 
    get_streak, 
    get_longest_streak, 
    get_max_sessions_per_day, 
    get_number_completed_focus_sessions_today, 
    get_all_sessions,
    get_number_completed_focus_sessions_today_since_last_long_break, 
    get_total_focus_mins, 
    get_most_focus_min
)
from focus.config import FocusConfig
from rich.console import Console
import click
from pathlib import Path
from typing import Callable, TypeAlias

OnTickFn: TypeAlias = Callable[[float, float], None]
CountdownFn: TypeAlias = Callable[[float, OnTickFn], tuple[float, str]]
ReflectionFn: TypeAlias = Callable[[Console], str]
ContinueFn: TypeAlias = Callable[[], bool]
SessionsSinceLastLongBreakFn: TypeAlias = Callable[[Path, int], int]
LongBreakNotificationFn: TypeAlias = Callable[[Console, int, int, int], bool]

@click.group()
def focus() -> None:
    pass


#helper function to trigger a session, used for testing and to keep start() cleaner
def trigger_session(console: Console, 
                    duration:int, 
                    task:str, 
                    data_path: Path, 
                    focus_or_break: str, 
                    _countdown_function: CountdownFn = run_countdown, #Injecting countdown function for testing purposes
                    _reflection_function: ReflectionFn = prompt_reflection #Injecting reflection function for testing purposes
                    ) -> str:
    '''Triggers a focus or break session. Returns the status of the session ("completed" or "interrupted").'''
    show_start_banner(console, duration, focus_or_break, task)

    start_time = datetime.now()
    total_seconds = duration * 60
    
    with make_progress_bar(console) as progress:
        task_progress = progress.add_task(f"{focus_or_break.capitalize()} Time Remaining:", total=total_seconds)
        def on_tick(elapsed: float, total: float) -> None:
            progress.update(task_progress, completed=elapsed)

        elapsed, status = _countdown_function(total_seconds, on_tick) 
        if status == "interrupted": 
            progress.update(task_progress, description=f"{focus_or_break.capitalize()} Time Interrupted: {round(elapsed / 60, 1)} minutes")
        else: 
            progress.update(task_progress, completed=elapsed, description=f"{focus_or_break.capitalize()} Time Finished: {round(elapsed / 60, 1)} minutes") 

    end_time = datetime.now()

    timer_result = TimerResult(
        planned_duration=total_seconds,
        actual_duration=round(elapsed),
        type=focus_or_break,
        start_time=start_time,
        end_time=end_time,
        status=status,
        task=task
    )

    reflection = _reflection_function(console)

    record = SessionRecord(
        id=str(start_time.timestamp()),  # simple unique ID based on timestamp
        task=task,
        planned_duration=timer_result.planned_duration,
        actual_duration=timer_result.actual_duration,
        started_at=timer_result.start_time.isoformat(),
        ended_at=timer_result.end_time.isoformat(),
        status=timer_result.status,
        session_type=timer_result.type,
        reflection=reflection
    )

    save_session(data_path, record)

    if status == "completed":
        show_complete_banner(console, focus_or_break, round(elapsed / 60))
    else:
        show_interrupt_banner(console, focus_or_break, round(elapsed / 60))

    return timer_result.status


def trigger_session_and_break(console: Console, 
                                duration: int,
                                task: str,
                                break_duration: int, 
                                cfg: FocusConfig, #Added as a paramter for testing purposes
                                _countdown_function: CountdownFn = run_countdown, #Injecting countdown function for testing purposes
                                _reflection_function: ReflectionFn = prompt_reflection, #Injecting reflection function for testing purposes, 
                                _sessions_since_break_function: SessionsSinceLastLongBreakFn = get_number_completed_focus_sessions_today_since_last_long_break, #Injecting function for testing purposes
                                _long_break_notification_function: LongBreakNotificationFn = long_break_notification  # Injecting function for testing purposes
                                ) -> str:
    '''Triggers a focus session followed by a break session. Returns the status of both sessions.'''
    if _sessions_since_break_function(cfg.data_path, cfg.long_break_minutes) >= cfg.cycles and _long_break_notification_function(console, cfg.cycles, break_duration, cfg.long_break_minutes):
        break_duration = cfg.long_break_minutes
    status = trigger_session(console, duration, task, cfg.data_path, "focus", _countdown_function=_countdown_function, _reflection_function=_reflection_function)
    if status != "completed":
        return status
    return trigger_session(console, break_duration, task + " - Break", cfg.data_path, "break", _countdown_function=_countdown_function, _reflection_function=_reflection_function)


def run_session_loop(
    console: Console,
    number_of_cycles: int,
    duration: int,
    task: str,
    break_duration: int,
    no_break: bool,
    cfg: FocusConfig, # Added for testing purposes 
    _countdown_function: CountdownFn = run_countdown, #Injecting countdown function for testing purposes
    _reflection_function: ReflectionFn = prompt_reflection, #Injecting reflection function for testing purposes
    _continue_function: ContinueFn = continue_to_next_session, #Injecting continue function for testing purposes
    _sessions_since_break_function: SessionsSinceLastLongBreakFn = get_number_completed_focus_sessions_today_since_last_long_break, #Injecting function for testing purposes
    _long_break_notification_function: LongBreakNotificationFn = long_break_notification, #Injecting function for testing purposes
) -> None:
    '''Helper function to run multiple focus/break cycles. Pulled out to make it easier to test.'''
    for i in range(number_of_cycles):
        if i > 0 and not _continue_function():
            exit_multi_session(console)
            break
        status = ""
        if no_break:
            status = trigger_session(console, duration if duration == 0 else duration or cfg.focus_minutes, task + f" - Cycle {i+1}", cfg.data_path, "focus", _countdown_function=_countdown_function, _reflection_function=_reflection_function)
        else: 
            status = trigger_session_and_break(console, duration if duration == 0 else duration or cfg.focus_minutes, task + f" - Cycle {i+1}",  break_duration if break_duration == 0 else break_duration or cfg.break_minutes,  cfg, _countdown_function=_countdown_function, _reflection_function=_reflection_function, _sessions_since_break_function=_sessions_since_break_function, _long_break_notification_function=_long_break_notification_function)
        if status != "completed":
            exit_multi_session(console)
            break


@focus.command()
@click.option("--duration", "-d", type=int, default=None, help="Duration of focus session in minutes(overrides config)")
@click.option("--task", "-t", default="General Focus", help="Description of the task you're working on")
@click.option("--break-duration", "-b", type=int, default=None, help="Duration of break session in minutes (overrides config)")
@click.option("--no-break", is_flag=True, default=False, help="Skip the break after this session")
@click.option("--number-of-cycles", "-c", type=int, default=2, help="Number of focus/break cycles to run (default: 2)")
def multi_start(number_of_cycles: int, duration: int, task: str, break_duration: int, no_break: bool) -> None:
    '''
    Start multiple focus sessions with optional breaks. Accepts duration in minutes, task description, break duration, and number of cycles.
    Prompts for reflection after each session and saves results to storage. If the user has completed enough focus sessions today since the last long break, prompts for a longer break.
    Saves session results and reflections to storage.\n
    Args: \n
        --number-of-cycles: Number of focus/break cycles to run (default: 2)
        --duration: Duration of focus session in minutes (overrides config). Allows for 0 duration for testing purposes.
        --task: Description of the task you're working on (default: "General Focus")
        --break-duration: Duration of break session in minutes (overrides config). Allows for 0 duration for testing purposes.
        --no-break: Skip the break after this session
    '''
    run_session_loop(Console(), number_of_cycles, duration, task, break_duration, no_break, FocusConfig.load())


@focus.command()
@click.option("--duration", "-d", type=int, default=None, help="Duration of focus session in minutes(overrides config)")
@click.option("--task", "-t", default="General Focus", help="Description of the task you're working on")
@click.option("--break-duration", "-b", type=int, default=None, help="Duration of break session in minutes (overrides config)")
@click.option("--no-break", is_flag=True, default=False, help="Skip the break after this session")
def start(duration: int, task: str, break_duration: int, no_break: bool) -> None:
    '''
    Start a focus session with an optional break. Accepts duration in minutes, task description, and break duration. 
    Prompts for reflection after each session and saves results to storage. If the user has completed enough focus sessions today since the last long break, prompts for a longer break.
    Saves session results and reflections to storage.\n
    Args: \n
        --duration: Duration of focus session in minutes (overrides config). Allows for 0 duration for testing purposes.
        --task: Description of the task you're working on (default: "General Focus")
        --break-duration: Duration of break session in minutes (overrides config). Allows for 0 duration for testing purposes.
        --no-break: Skip the break after this session
    '''
    console = Console()
    cfg = FocusConfig.load()
    if no_break:
        trigger_session(console, duration if duration == 0 else duration or cfg.focus_minutes, task, cfg.data_path, "focus")
    else: 
        trigger_session_and_break(console, duration if duration == 0 else duration or cfg.focus_minutes, task, break_duration if break_duration == 0 else break_duration or cfg.break_minutes, cfg)


@focus.command()
@click.option("--days", "-d", default=7, help="Number of days of history to show")
def history(days: int) -> None:
    '''
    Show a table of focus sessions from the last N days. Prints no sessions found if there are none.
    Table contains task, session type, planned vs actual duration, status (completed vs interrupted), and start/end timestamps.\n
    Args: \n
        --days: Number of days of history to show (default: 7)
    '''
    console = Console()
    focus_session_data = FocusConfig.load()
    sessions = get_sessions_last_n_days(focus_session_data.data_path, days=days)
    show_history_table(console, days, sessions)


@focus.command()
@click.option("--include-interrupted", is_flag=True, help="Whether to include interrupted sessions in the today's stats")
def personal_best(include_interrupted: bool) -> None:
    '''
    Show personal best stats like longest streak, most sessions in a day, longest focus time. Prints no sessions found if there are none.\n
    Args: \n
        --include-interrupted: Whether to include interrupted sessions in the today's stats (default: False)
    '''
    console = Console()
    focus_session_data = FocusConfig.load()
    best_streak = get_longest_streak(focus_session_data.data_path)
    best_focus_count = get_max_sessions_per_day(focus_session_data.data_path)
    most_focus_min = get_most_focus_min(focus_session_data.data_path, include_interrupted=include_interrupted)
    show_best_stats(console, best_streak, best_focus_count, most_focus_min)


@focus.command()
@click.option("--include-interrupted", is_flag=True, help="Whether to include interrupted sessions in the today's stats")
def stats(include_interrupted: bool) -> None:
    '''
    Show current streak, total sessions, sessions today, and total focus time. Prints no sessions found if there are none.\n
    Args: \n
        --include-interrupted: Whether to include interrupted sessions in the today's stats (default: False)
    '''
    console = Console()
    focus_session_data = FocusConfig.load()
    sessions = get_all_sessions(focus_session_data.data_path)
    current_streak = get_streak(focus_session_data.data_path)
    total_sessions = len(sessions)
    sessions_today = get_number_completed_focus_sessions_today(focus_session_data.data_path)
    total_focus_time = get_total_focus_mins(focus_session_data.data_path, include_interrupted=include_interrupted)

    show_stats(console, current_streak, total_sessions, sessions_today, total_focus_time)


@focus.command()
def config() -> None:
    '''
    Show current configuration settings.
    '''
    console = Console()
    cfg = FocusConfig.load()
    show_config(console, cfg.show())


@focus.command()
def reset() -> None:
    '''
    Reset all session data. Prints no sessions found if there are none. Prompts for confirmation before deleting data file.
    '''
    console = Console()
    focus_session_data = FocusConfig.load()
    if not focus_session_data.data_path.exists():
        no_sessions_found(console)
        return
    confirm = should_reset()
    if confirm:
        focus_session_data.data_path.unlink()  # Delete the file
        reset_successful(console)
    else:
        reset_cancelled(console)


if __name__ == "__main__":
    focus()

