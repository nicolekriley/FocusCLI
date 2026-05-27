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
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.align import Align

def show_start_banner(console: Console, minutes: int, timer_type: str, task: str) -> None:
    emoji = Emoji("pushpin") if timer_type == "focus" else Emoji("coffee")
    focus_color = "bold green" if timer_type == "focus" else "bold cyan"
    panel_text = f"Starting [{focus_color}]{timer_type}[/] session for {minutes} minutes for task: [italic]{task}[/italic]"
    panel_text_aligned = Align.center(panel_text)
    console.print(Panel(title=f"{emoji} Starting Session Timer {emoji}", 
                        renderable=panel_text_aligned, border_style=focus_color.replace("bold ", "")))


def show_complete_banner(console: Console, timer_type: str, minutes: int) -> None:
    panel_text = """
        :party_popper: {timer_type} session complete!
        :brain: [bold]Great work![/bold]
        :stopwatch:  {mins} minutes of {timer_type_lower}
        :star: Keep the momentum going
    """.format(mins=minutes, timer_type=timer_type.capitalize(), timer_type_lower=timer_type.lower())
    aligned_text = Align.center(panel_text)
    console.print(Panel(title=":sparkles: [bold yellow]Session Complete[/bold yellow] :sparkles:", 
                        renderable=aligned_text, border_style="yellow"))


def show_interrupt_banner(console: Console, timer_type: str, actual_minutes: int) -> None:
    emoji = Emoji("x")
    panel_text = f"[bold red]{timer_type.capitalize()} session interrupted after {actual_minutes} minutes![/bold red] \n[italic]That's okay — it still counts.[/italic] 💛"
    panel_text_aligned = Align.center(panel_text)
    console.print(Panel(title=f"{emoji} Session Interrupted {emoji}", renderable=panel_text_aligned, border_style="dim"))


def show_stats(console: Console, current_streak: int, total_sessions: int, sessions_today: int, total_focus: int) -> None:
    # show stats of current streak, total sessions, sessions today, total focus time
    if total_sessions == 0: 
        no_sessions_found(console)
        return
    
    emoji = Emoji("chart_with_upwards_trend")
    panel_text = f"Current Streak: [bold]{current_streak}[/bold]\nTotal Sessions: [bold]{total_sessions}[/bold]\nCompleted Sessions Today: [bold]{sessions_today}[/bold]\nTotal Focus Time: [bold]{total_focus} minutes[/bold]"
    aligned_text = Align.center(panel_text)
    console.print(Panel(renderable=aligned_text, title=f"{emoji} Session Stats {emoji}", border_style="blue"))


def show_best_stats(console: Console, best_streak: int, best_focus_count: int, most_focus_min: int) -> None:
    if best_streak == 0 and best_focus_count == 0 and most_focus_min == 0:
        no_sessions_found(console)
        return
    
    emoji = Emoji("trophy")
    panel_text = f"Best Streak: [bold]{best_streak}[/bold]\nMost Focus Sessions in a Day: [bold]{best_focus_count}[/bold]\nLongest Focus Time: [bold]{most_focus_min} minutes[/bold]"
    aligned_text = Align.center(panel_text)
    console.print(Panel(renderable=aligned_text, title=f"{emoji} Personal Bests {emoji}", border_style="magenta"))


def show_history_table(console: Console, length: int, sessions: list[SessionRecord]) -> None:
    if not sessions:
        no_sessions_found(console)
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
        emoji = Emoji("heavy_check_mark") if s["status"] == "completed" else Emoji("zap")
        status_fmt = f"[{status_color}]{emoji}  completed[/{status_color}]" if s["status"] == "completed" else f"[{status_color}]{emoji} interrupted[/{status_color}]"
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
    console.print("\n:thought_balloon: [bold]Quick reflection:[/bold] :thought_balloon:")
    return Prompt.ask("How did it go? Any reflections on the session?", default="")


def make_progress_bar(console: Console) -> Progress:
    return Progress(
        TextColumn(":stopwatch: [bold green]{task.description} :stopwatch:"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        console=console,
    )


def continue_to_next_session() -> bool:
    return Confirm.ask("\n:repeat: [bold]Ready for the next session?[/bold] :repeat:", default=True)


def long_break_notification(console: Console, cycles: int, given_break_duration: int, recommended_break_duration: int) -> bool:
    console.print(f"\n:coffee: [bold yellow]You've completed {cycles} focus sessions! Time for a longer break![/bold yellow] :coffee:")
    if given_break_duration: 
        console.print(f"[dim]You specified a break duration of {given_break_duration} minutes.[/dim]")
    console.print(f"[dim]The recommended break duration is {recommended_break_duration} minutes.[/dim]")
    return Confirm.ask(f"Would you like to take the recommended {recommended_break_duration}-minute break instead?", default=True)


def show_config(console: Console, config_dict: dict[str, object]) -> None:
    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    for key, value in config_dict.items():
        table.add_row(key, str(value))
    console.print(table)


def should_reset() -> bool: 
    return Confirm.ask("\n:warning: [bold red]Are you sure you want to reset your data? This action cannot be undone. [/bold red] :warning:", default=False)


def reset_successful(console: Console) -> None: 
    console.print("\n:data: [bold green]Data reset successful![/bold green] :data:")


def reset_cancelled(console: Console) -> None:
    console.print("\n:x: [bold yellow]Data reset cancelled. Your data is safe.[/bold yellow] :x:")


def no_sessions_found(console: Console) -> None:
    console.print("[dim]No sessions found.[/dim]")
