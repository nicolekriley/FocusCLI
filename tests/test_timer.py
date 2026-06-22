"""
test_timer.py 
Tests for countdown timer logic in timer.py
"""

from focus.timer import run_countdown

def test_countdown_completes() -> None:
    ticks: list[float] = []
    elapsed, status = run_countdown(3, lambda e, t: ticks.append(e), tick_interval=0)
    assert status == "completed"
    assert elapsed == 3

def test_countdown_calls_on_tick() -> None:
    ticks: list[float] = []
    run_countdown(5, lambda e, t: ticks.append(e), tick_interval=0)
    assert len(ticks) == 6  # 0..5 inclusive
    assert ticks == [0, 1, 2, 3, 4, 5]

def test_countdown_interrupts() -> None:
    ticks: list[float] = []
    # Simulate KeyboardInterrupt by raising it in the on_tick callback
    def on_tick(e: float, t: float) -> None:
        ticks.append(e)
        if e == 2:
            raise KeyboardInterrupt()

    elapsed, status = run_countdown(5, on_tick, tick_interval=0)
    assert status == "interrupted"
    assert elapsed == 2
    assert len(ticks) == 3  # 0, 1, 2
    assert ticks == [0, 1, 2]