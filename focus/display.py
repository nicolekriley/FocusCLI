"""
display.py 
Console display logic for timer. Separated from timer logic so it's easy to unit-test and swap out display backends.
Uses Rich library to display a progress bar and timer countdown in the console.
"""

from __future__ import annotations
from datetime import datetime
from rich.emoji import Emoji
from rich.console import Console
from rich.progress import Progress, BarColumn, TimeRemainingColumn, TextColumn
from rich.table import Table
from storage import SessionRecord
from rich.prompt import Prompt 
from rich.panel import Panel
from rich.align import Align

def show_start_banner(console: Console, minutes: int, timer_type: str, task: str) -> None:
    emoji = Emoji("pushpin") if timer_type == "focus" else  Emoji("coffee")
    focus_color = "bold green" if timer_type == "focus" else "bold cyan"
    console.print(Panel(title=f"{emoji} Starting Session Timer {emoji}", renderable=f"Starting [{focus_color}]{timer_type}[/] session for {minutes} minutes for task: [italic]{task}[/italic]", border_style=focus_color.replace("bold ", "")))

def show_complete_banner(console: Console, timer_type: str, minutes: int) -> None:
    panelText = """
        Emoji("brain")  [bold]Great work![/bold]
        Emoji("stopwatch")  {mins} minutes of focus
        Emoji("star")  Keep the momentum going
    """.format(mins=minutes)
    console.print(Panel(title=":sparkles: [bold yellow]Session Complete[/bold yellow] :sparkles:", renderable=panelText, border_style="yellow"))

def show_interrupt_banner(console: Console, timer_type: str, actual_minutes: int) -> None:
    emoji = Emoji("x")
    panelText = f"[bold red]{timer_type} session interrupted after {actual_minutes} minutes![/bold red] \n[italic]That's okay — it still counts.[/italic] 💛"
    console.print(Panel(title=f"{emoji} Session Interrupted {emoji}", renderable=panelText, border_style="dim"))

def show_stats(console: Console, current_streak: int, total_sessions: int, sessions_today: int, total_focus: int) -> None:
    # show stats of current streak, session history over past 7 days, sessions today, total focus time
    emoji = Emoji("chart_with_upwards_trend")
    panelText = f"Current Streak: [bold]{current_streak}[/bold]\nTotal Sessions: [bold]{total_sessions}[/bold]\nSessions Today: [bold]{sessions_today}[/bold]\nTotal Focus Time: [bold]{total_focus} minutes[/bold]"
    console.print(Panel(panelText, title=f"{emoji} Session Stats {emoji}", subtitle="Here's how your focus journey is going:"))

def show_best_stats(console: Console, best_streak: int, best_focus: int) -> None:
    emoji = Emoji("trophy")
    panelText = f"Best Streak: [bold]{best_streak}[/bold]\nMost Focus Sessions in a Day: [bold]{best_focus} minutes[/bold]"
    console.print(Panel(panelText, title=f"{emoji} Personal Bests {emoji}", subtitle="Your all-time best focus achievements:"))

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
        emoji = Emoji("check") if s["status"] == "completed" else Emoji("zap")
        status_fmt = f"[{status_color}]{emoji} {s['status']}[/{status_color}]" if s["status"] == "completed" else f"[{status_color}]{emoji} interrupted[/{status_color}]"
        type_color = "blue" if s["session_type"] == "focus" else "yellow"
        start_date_time = datetime.fromisoformat(s["started_at"]).strftime("%Y-%m-%d %H:%M:%S")
        end_date_time = datetime.fromisoformat(s["ended_at"]).strftime("%Y-%m-%d %H:%M:%S")
        table.add_row(
            s.get("task", ""),
            f"[{type_color}]{s['session_type']}[/{type_color}]",
            f"{s['planned_duration'] // 60:.1f}",
            f"{s['actual_duration'] // 60:.1f}",
            status_fmt,
            start_date_time,
            end_date_time,
        )
    console.print(table)

def prompt_reflection(console: Console) -> str:
    console.print("\n Emoji('thought_balloon') [bold]Quick reflection:[/bold] Emoji('thought_balloon')")
    return Prompt.ask("How did it go? Any reflections on the session?", default="")

def make_progress_bar(console: Console) -> Progress:
    return Progress(
        TextColumn("Emoji('stopwatch') [bold green]{task.description} Emoji('stopwatch')"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    )

#for testing purposes, we can just call the display functions here with some dummy data to see how they look in the console. In production, these would be called from the main timer logic in focus.py.
def main(): 
    console = Console()
    show_start_banner(console, 25, "focus", "Write blog post")
    show_interrupt_banner(console, "focus", 10)
    show_complete_banner(console, "focus", 25)
    show_stats(console, current_streak=3, total_sessions=15, sessions_today=2, total_focus=375)
    show_best_stats(console, best_streak=5, best_focus=150)

if __name__ == "__main__": 
    main()
