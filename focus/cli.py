'''
cli.py 
Adds in functionality to run the timer and display logic together. Handles user input for starting timers and showing stats.
'''

from __future__ import annotations
from datetime import datetime
from display import (
    continue_to_next_session,
    show_history_table, 
    show_start_banner, 
    show_complete_banner, 
    show_interrupt_banner, 
    show_stats, 
    show_best_stats, 
    prompt_reflection, 
    continue_to_next_session, 
    long_break_notification
)
from timer import run_countdown, TimerResult
from config import FocusConfig
from storage import (
    SessionRecord, 
    save_session, 
    get_sessions_last_n_days, 
    get_streak, 
    get_longest_streak, 
    get_max_sessions_per_day, 
    get_number_completed_focus_sessions_today, 
    get_all_sessions,
    get_number_completed_focus_sessions_today_before_last_long_break, 
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


@focus.command()
@click.option("--duration", "-d", type=int, default=25, help="Duration of focus session in minutes(overrides config)")
@click.option("--task", "-t", default="General Focus", help="Description of the task you're working on")
@click.option("--break-duration", "-b", type=int, default=5, help="Duration of break session in minutes (overrides config)")
@click.option("--no-break", is_flag=True, help="Skip the break after this session")
def start(duration: int, task: str, break_duration: int, no_break: bool):
    '''
    Start a focus session with an optional break. Accepts duration in minutes, task description, and break duration. 
    Prompts for reflection after each session and saves results to storage. If the user has completed enough focus sessions today, prompts for a longer break.
    Saves session results and reflections to storage.\n
    Args: \n
        --duration: Duration of focus session in minutes (overrides config)
        --task: Description of the task you're working on (default: "General Focus")
        --break-duration: Duration of break session in minutes (overrides config)
        --no-break: Skip the break after this session
    '''
    console = Console()
    cfg = FocusConfig.load()

    config_focus_duration = cfg.focus_minutes
    config_break_duration = cfg.break_minutes
    if duration != 0 or break_duration != 0: 
        duration = duration or config_focus_duration
        break_duration = break_duration or config_break_duration
    if get_number_completed_focus_sessions_today_before_last_long_break(Path(cfg.data_path)) >= cfg.cycles:
        longer_break = long_break_notification(console, cfg.cycles, cfg.break_minutes,cfg.long_break_minutes)
        if longer_break: 
            duration = cfg.long_break_minutes
            break_duration = cfg.long_focus_minutes
    
    show_start_banner(console, duration, "focus", task)
    start_time = datetime.now()
    total_seconds = duration * 60
    elapsed, status = run_countdown(total_seconds, lambda e, t: None)  # No-op on_tick for now
    end_time = datetime.now()
    
    print(duration, elapsed, status)

    timer_result = TimerResult(
        planned_duration=total_seconds,
        actual_duration=elapsed,
        type="focus",
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

    save_session(Path(cfg.data_path), record)

    if status == "completed":
        show_complete_banner(console, "focus", round(elapsed / 60))
    else:
        show_interrupt_banner(console, "focus", round(elapsed / 60))
    
    prompted = False 
    if not no_break and status == "completed":
        show_start_banner(console, break_duration, "break", "Break Time!")
        break_start_time = datetime.now()
        break_seconds = break_duration * 60
        break_elapsed, break_status = run_countdown(break_seconds, lambda e, t: None)
        break_end_time = datetime.now()

        break_timer_result = TimerResult(
            planned_duration=break_seconds,
            actual_duration=break_elapsed,
            type="break",
            start_time=break_start_time,
            end_time=break_end_time,
            status=break_status,
            task="Break"
        )

        reflection = prompt_reflection(console)

        print(break_timer_result.planned_duration)
        print(break_timer_result.actual_duration)
        break_record = SessionRecord(
            id=str(break_start_time.timestamp()),
            task="Break",
            planned_duration=break_timer_result.planned_duration,
            actual_duration=break_timer_result.actual_duration,
            started_at=break_timer_result.start_time.isoformat(),
            ended_at=break_timer_result.end_time.isoformat(),
            status=break_timer_result.status,
            session_type=break_timer_result.type,
            reflection=reflection
        )

        save_session(Path(cfg.data_path), break_record)

        if break_status == "completed":
            show_complete_banner(console, "break", round(break_elapsed / 60))
        else:
            show_interrupt_banner(console, "break", round(break_elapsed / 60))

        continued = break_status == "completed" and continue_to_next_session()
        prompted = True 
        if continued:
            start(duration=duration, task=task, break_duration=break_duration, no_break=no_break) 
    if not prompted and status == "completed" and continue_to_next_session():
        start(duration=duration, task=task, break_duration=break_duration, no_break=no_break)


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
    Show personal best stats like longest streak, most sessions in a day, longest focus time. \n
    Args: \n
        --include-interrupted: Whether to include interrupted sessions in the today's stats (default: False)
    '''
    console = Console()
    focus_session_data = FocusConfig.load()
    sessions = get_all_sessions(focus_session_data.data_path)
    best_streak = get_longest_streak(focus_session_data.data_path)
    best_focus_count = get_max_sessions_per_day(focus_session_data.data_path)
    most_focus_min = get_most_focus_min(focus_session_data.data_path, include_interrupted=include_interrupted)
    show_best_stats(console, best_streak, best_focus_count, most_focus_min)


@focus.command()
@click.option("--include-interrupted", is_flag=True, help="Whether to include interrupted sessions in the today's stats")
def stats(include_interrupted):
    '''
    Show current streak, total sessions, sessions today, and total focus time. \n
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
    console.print("[bold underline]Current Configuration:[/bold underline]")
    for key, value in cfg.show().items():
        console.print(f"[cyan]{key}:[/cyan] {value}")


@focus.command()
def reset():
    '''
    Reset all session data. Prompts for confirmation before deleting data file.
    '''
    console = Console()
    focus_session_data = FocusConfig.load()
    if not focus_session_data.data_path.exists():
        console.print("[dim]No session data found to reset.[/dim]")
        return
    
    confirm = click.confirm("Are you sure you want to reset all session data? This cannot be undone.", default=False)
    if confirm:
        focus_session_data.data_path.unlink()
        console.print("[green]All session data has been reset.[/green]")
    else:
        console.print("[yellow]Reset cancelled. Your session data is safe.[/yellow]")


if __name__ == '__main__':
    focus()
