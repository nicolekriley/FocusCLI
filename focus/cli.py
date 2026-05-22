'''
cli.py 
Adds in functionality to run the timer and display logic together. Handles user input for starting timers and showing stats.
'''

from __future__ import annotations
from datetime import datetime
from display import show_history_table, show_start_banner, show_complete_banner, show_interrupt_banner, show_stats, show_best_stats, prompt_reflection
from timer import run_countdown, TimerResult
from config import FocusConfig
from storage import SessionRecord, save_session, get_sessions_last_n_days, get_streak, get_longest_streak, get_max_sessions_per_day, get_sessions_today, get_all_sessions
from rich.console import Console
import click
from pathlib import Path
from config import FocusConfig

@click.group()
def focus():
    pass

@focus.command()
@click.option("--duration", "-d", default=25, help="Duration of focus session in minutes(overrides config)")
@click.option("--task", "-t", default="General Focus", help="Description of the task you're working on")
@click.option("--break-duration", "-b", default=5, help="Duration of break session in minutes (overrides config)")
@click.option("--no-break", is_flag=True, help="Skip the break after this session")
def start(duration: int, task: str, break_duration: int, no_break: bool):
    console = Console()
    show_start_banner(console, duration, "focus", task)
    start_time = datetime.now()
    total_seconds = duration * 60
    elapsed, status = run_countdown(total_seconds, lambda e, t: None)  # No-op on_tick for now
    end_time = datetime.now()
    
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
    save_session(Path("data/sessions.json"), record)

    if status == "completed":
        show_complete_banner(console, "focus", round(elapsed / 60))
    else:
        show_interrupt_banner(console, "focus", round(elapsed / 60))

@focus.command()
@click.option("--days", "-d", default=7, help="Number of days of history to show")
def history(days):
    console = Console()
    focus_session_data = FocusConfig.load()
    sessions = get_sessions_last_n_days(focus_session_data.data_path, days=days)
    show_history_table(console, days, sessions)

@focus.command()
def personal_best_stats():
    console = Console()
    focus_session_data = FocusConfig.load()
    sessions = get_sessions_last_n_days(focus_session_data.data_path, days=30)
    best_streak = get_longest_streak(focus_session_data.data_path)
    best_focus_count = get_max_sessions_per_day(focus_session_data.data_path)
    most_focus_min = max((s["actual_duration"] for s in sessions if s["status"] == "completed" and s["session_type"] == "focus"), default=0) // 60
    show_best_stats(console, best_streak, best_focus_count, most_focus_min)

@focus.command()
def stats():
    console = Console()
    focus_session_data = FocusConfig.load()
    sessions = get_all_sessions(focus_session_data.data_path)
    current_streak = get_streak(focus_session_data.data_path)
    total_sessions = len(sessions)
    sessions_today = get_sessions_today(focus_session_data.data_path)
    total_focus = sum(s["actual_duration"] for s in sessions if s["session_type"] == "focus")

    show_stats(console, current_streak, total_sessions, sessions_today, total_focus // 60)

@focus.command()
def config():
    console = Console()
    cfg = FocusConfig.load()
    console.print("[bold underline]Current Configuration:[/bold underline]")
    for key, value in cfg.show().items():
        console.print(f"[cyan]{key}:[/cyan] {value}")


