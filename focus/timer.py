"""
timer.py 
Core countdown logic. Separated from display so it's easy to unit-test.
"""

from __future__ import annotations

import time 
from datetime import datetime 
from typing import Tuple, Callable
from dataclasses import dataclass   


# way to store data after a timer has ended
@dataclass 
class TimerResult: 
    planned_duration: int #planned duration of timer in seconds 
    actual_duration: int #actual duration of timer in seconds
    type: str #work vs break timer; "work" or "break"
    start_time: datetime #time timer started 
    end_time: datetime # time timer ends 
    status: str #status of timer: "completed", "interrupted"
    task: str #describe what you are working on during the timer 

    @property
    def actual_minutes(self) -> float:
        return round(self.actual_duration / 60, 1)

    @property 
    def planned_minutes(self) -> float:
        return round(self.planned_duration / 60, 1)
    

def run_countdown(
    total_seconds: float,
    on_tick: Callable[[float, float], None],
    tick_interval: float = 1.0,
) -> tuple[float, str]:
    """
    Count down total_seconds, calling on_tick(elapsed, total) each tick.
    Returns (seconds_elapsed, status) where status is 'completed' or 'interrupted'.
    Raises KeyboardInterrupt internally and returns 'interrupted' — caller never crashes.
    """
    elapsed = 0
    try:
        while elapsed < total_seconds:
            on_tick(elapsed, total_seconds)
            if tick_interval > 0:
                time.sleep(tick_interval)
            elapsed += tick_interval if tick_interval > 0 else 1  # For testing, just increment without sleeping
        on_tick(elapsed, total_seconds)
        return elapsed, "completed"
    except KeyboardInterrupt:
        return elapsed, "interrupted"