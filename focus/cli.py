'''
cli.py 
Adds in functionality to run the timer and display logic together. Handles user input for starting timers and showing stats.
'''

from __future__ import annotations
from datetime import datetime
from display import (
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
    no_sessions_found
)
from timer import run_countdown, TimerResult
from storage import (
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
from rich.console import Console
import click
from pathlib import Path
from config import FocusConfig

@click.group()
def focus():
    pass


#helper function to trigger a session, used for testing and to keep start() cleaner
def trigger_session(console: Console, duration:int, task:str, data_path: Path,  focus_or_break: str) -> str:
    '''Triggers a focus or break session. Returns the status of the session ("completed" or "interrupted").'''
    show_start_banner(console, duration, focus_or_break, task)

    start_time = datetime.now()
    total_seconds = duration * 60
    elapsed, status = run_countdown(total_seconds, lambda e, t: None)  # No-op on_tick for now

    end_time = datetime.now()

    timer_result = TimerResult(
        planned_duration=total_seconds,
        actual_duration=elapsed,
        type=focus_or_break,
        start_time=start_time,
        end_time=end_time,
        status=status,
        task=task
    )

    reflection = prompt_reflection(console)

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


@focus.command()
@click.option("--duration", "-d", type=int, default=None, help="Duration of focus session in minutes(overrides config)")
@click.option("--task", "-t", default="General Focus", help="Description of the task you're working on")
@click.option("--break-duration", "-b", type=int, default=None, help="Duration of break session in minutes (overrides config)")
@click.option("--no-break", is_flag=True, default=False, help="Skip the break after this session")
def start(duration: int, task: str, break_duration: int, no_break: bool):
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

    config_focus_duration = cfg.focus_minutes
    config_break_duration = cfg.break_minutes
    if duration is None:
        duration = config_focus_duration
    if break_duration is None:
        break_duration = config_break_duration
    if not(no_break) and get_number_completed_focus_sessions_today_since_last_long_break(cfg.data_path, cfg.long_break_minutes) >= cfg.cycles:
        longer_break = long_break_notification(console, cfg.cycles, cfg.break_minutes,cfg.long_break_minutes)
        if longer_break: 
            break_duration = cfg.long_break_minutes
    status = trigger_session(console, duration, task, cfg.data_path, "focus")
     
    if not no_break and status == "completed":
        trigger_session(console, break_duration, task + " - Break", cfg.data_path, "break")


@focus.command()
@click.option("--days", "-d", default=7, help="Number of days of history to show")
def history(days):
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
def personal_best(include_interrupted):
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
def stats(include_interrupted):
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
def config():
    '''
    Show current configuration settings.
    '''
    console = Console()
    cfg = FocusConfig.load()
    show_config(console, cfg.show())


@focus.command()
def reset():
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
        focus_session_data.data_path.unlink()
        reset_successful(console)
    else:
        reset_cancelled(console)

if __name__ == "__main__":
    focus()

