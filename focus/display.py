'''
display.py 
Console display logic for timer. Separated from timer logic so it's easy to unit-test and swap out display backends.
Uses Rich library to display a progress bar and timer countdown in the console.
'''

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Callable
from rich.console import Console
from rich.progress import Progress, BarColumn, TimeRemainingColumn, TextColumn
from rich.live import Live, console
from rich.table import Table
from focus.storage import SessionRecord
from rich.prompt import Prompt 
from rich.panel import Panel

def show_start_banner(console: Console, minutes: int, timer_type: str, task: str) -> None:
    emoji = "🎯" if timer_type == "focus" else "☕"
    focus_color = "bold green" if timer_type == "focus" else "bold cyan"
    console.print(Panel(title="Starting Session Timer", renderable=f"{emoji} Starting [{focus_color}]{timer_type}[/] session for {minutes} minutes for task: [italic]{task}[/italic]", border_style=focus_color.replace("bold ", "")))

def show_complete_banner(console: Console, timer_type: str, minutes: int) -> None:
    panelText = """
        🧠  [bold]Great work![/bold]
        ⏱   {mins} minutes of focus
        🌟  Keep the momentum going
    """.format(mins=minutes)
    console.print(Panel(title="✨ [bold yellow]Session Complete[/bold yellow] ✨", renderable=panelText, border_style="yellow"))

def show_interrupt_banner(console: Console, timer_type: str, actual_minutes: int) -> None:
    panelText = f"[bold red]{timer_type} session interrupted after {actual_minutes} minutes![/bold red] \n[italic]That's okay — it still counts.[/italic] 💛"
    console.print(Panel(title="❌ Session Interrupted ❌", renderable=panelText, border_style="dim"))

def show_stats(console: Console, current_streak: int, total_sessions: int, sessions_today: int, total_focus: int) -> None:
    # show stats of current streak, session history over past 7 days, sessions today, total focus time
    panelText = f"Current Streak: [bold]{current_streak}[/bold]\nTotal Sessions: [bold]{total_sessions}[/bold]\nSessions Today: [bold]{sessions_today}[/bold]\nTotal Focus Time: [bold]{total_focus} minutes[/bold]"
    console.print(Panel(panelText, title="📈 Session Stats 📈", subtitle="Here's how your focus journey is going:"))

def show_history_table(console: Console, length: int, sessions: list[SessionRecord]) -> None:
    if not sessions:
        console.print("[dim]No sessions found.[/dim]")
        return
    
    table = Table(title=f"Focus Session History (Last {length} Days)")
    table.add_column("Task", style="cyan")
    table.add_column("Session Type", style="yellow")
    table.add_column("Planned (min)", justify="right", style="magenta")
    table.add_column("Actual (min)", justify="right", style="green")
    table.add_column("Status", style="bold")
    table.add_column("Started At", style="dim")
    table.add_column("Ended At", style="dim")
  

    for s in sessions:
        status_color = "green" if s["status"] == "completed" else "red"
        type_color = "blue" if s["session_type"] == "focus" else "yellow"
        start_date_time = datetime.fromisoformat(s["started_at"]).strftime("%Y-%m-%d %H:%M:%S")
        end_date_time = datetime.fromisoformat(s["ended_at"]).strftime("%Y-%m-%d %H:%M:%S")
        table.add_row(
            s.get("task", ""),
            f"[{type_color}]{s['session_type']}[/{type_color}]",
            f"{s['planned_duration'] // 60:.1f}",
            f"{s['actual_duration'] // 60:.1f}",
            f"[{status_color}]{s['status']}[/{status_color}]",
            start_date_time,
            end_date_time,
        )
    console.print(table)

def prompt_reflection(console: Console) -> str:
    console.print("\n[bold]Quick reflection:[/bold]")
    return Prompt.ask("How did it go? Any reflections on the session?", default="")

def make_progress_bar() -> Progress:
    return Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeRemainingColumn(),
    )
