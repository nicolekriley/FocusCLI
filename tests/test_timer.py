# tests the countdown timer logic for timer.py 
from focus.timer import run_countdown

def test_countdown_completes() -> None:
    ticks: list[int] = []
    elapsed, status = run_countdown(3, lambda e, t: ticks.append(e), tick_interval=0)
    assert status == "completed"
    assert elapsed == 3

def test_countdown_calls_on_tick() -> None:
    ticks: list[int] = []
    run_countdown(5, lambda e, t: ticks.append(e), tick_interval=0)
    assert len(ticks) == 6  # 0..5 inclusive
    assert ticks == [0, 1, 2, 3, 4, 5]

def test_countdown_interrupts() -> None:
    ticks: list[int] = []
    # Simulate KeyboardInterrupt by raising it in the on_tick callback
    def on_tick(e: int, t: int) -> None:
        ticks.append(e)
        if e == 2:
            raise KeyboardInterrupt()

    elapsed, status = run_countdown(5, on_tick, tick_interval=0)
    assert status == "interrupted"
    assert elapsed == 2
    assert len(ticks) == 3  # 0, 1, 2
    assert ticks == [0, 1, 2]

def test_countdown_tick_interval() -> None:
    ticks: list[int] = []
    elapsed, status = run_countdown(3, lambda e, t: ticks.append(e), tick_interval=2.0)
    assert status == "completed"
    assert elapsed == 3
    assert len(ticks) == 2  # 0..2.5 inclusive
    assert ticks == [0, 2]

def test_countdown_fraction_tick_interval() -> None:
    ticks: list[float] = []
    elapsed, status = run_countdown(3, lambda e, t: ticks.append(e), tick_interval=0.5)
    assert status == "completed"
    assert elapsed == 3
    assert len(ticks) == 7  # 0..3 inclusive
    assert ticks == [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]