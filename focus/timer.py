#keeps the logic for the timers needed for the CLI application 
import time 
import datetime 
import typing 

#need dataclass 
from dataclasses import dataclass   


# way to store data after a timer has ended
@dataclass 
class TimerResult: 
    planned_duration: int #planned duration of timer in seconds 
    actual_duration: int #actual duration of timer in seconds
    type: str #work vs break timer; "work" or "break"
    start_time: datetime.datetime #time timer started 
    end_time: datetime.datetime # time timer ends 
    status: str #status of timer: "completed", "interrupted"
    task: str #describe what you are working on during the timer 

    @property
    def actual_minutes(self) -> float:
        return round(self.actual_duration / 60, 1)

    @property 
    def planned_minutes(self) -> float:
        return round(self.planned_duration / 60, 1)
    
# countdown function that takes in the total seconds for the timer, a callback function to 
# update the display each tick and an optional tick interval that defaults to 1 second. 
# It returns the total seconds elapsed and whether or not the timer was completed or interrupted. 
# in order to avoid crashing, we catch KeyboardInterrupt and return "interrupted" instead of raising the exception.
# tick interval can be set to 0 for testing purposes to avoid actual sleeping.
# expects tick interval must be positive. 
def run_countdown(
    total_seconds: int,
    on_tick: typing.Callable[[int, int], None],
    tick_interval: int = 1,
) -> typing.Tuple[int, str]:
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
                elapsed += tick_interval
            else: 
                elapsed += 1  # For testing, just increment without sleeping
        on_tick(elapsed, total_seconds)
        return elapsed, "completed"
    except KeyboardInterrupt:
        return elapsed, "interrupted"