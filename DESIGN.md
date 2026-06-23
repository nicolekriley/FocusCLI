## Important Design Decisions

## Case 1: Why `trigger_session` is separate from the Click commands that call it

**The Problem:**
Both `start` and `multi_start` commands need to run a session, so the session logic needs to be accessible from two different entry points.

**Options Considered:**
- Duplicate the logic inside each Click command
- Extract the logic into a shared helper that both commands call

**What I Chose and Why:**
I extracted the logic into `trigger_session`, a plain function both commands call. This avoids duplication, makes the function straightforward to unit test in isolation, and keeps Click commands thin so they handle CLI wiring only, not business logic.


## Case 2: Why `run_session_loop` is a plain function versus repeated Click invocations

**The Problem:**
`multi_start` needs to run multiple sessions in sequence without re-entering Click's command machinery each time.

**Options Considered:**
- Call the `start` Click command multiple times inside `multi_start`
- Use a for loop over plain helper functions, keeping Click out of the inner loop

**What I Chose and Why:**
I used a for loop over plain helper functions. Click is designed to handle terminal I/O wiring at the entry point so re-invoking a Click command repeatedly would recreate the Click context unnecessarily on each iteration and blurs the boundary between CLI wiring and core logic. By keeping the loop in plain Python, the Click context is created exactly once and the session logic stays easily testable.


## Case 3: Why `tick_interval=0` for testing instead of mocking `time.sleep`

**The Problem:**
Tests that exercise `countdown` would be unacceptably slow if they waited on real sleep intervals. There needs to be a way to run the timer at zero delay.

**Options Considered:**
- Pass `tick_interval=0` as a parameter to `countdown`
- Mock `time.sleep` in tests to eliminate the wait

**What I Chose and Why:**
I added `tick_interval` as a parameter to `countdown` and default it to `0` in tests. This required no mocking infrastructure and has the bonus of being usable during manual command-line testing as you can pass `--tick-interval 0` to run through sessions instantly. Mocking `time.sleep` would speed up automated tests but wouldn't help during manual testing and would couple the tests more tightly to the implementation detail of which sleep function is called.

**What I'd Do Differently:**
In hindsight, both approaches are reasonable. If `countdown` grew more complex and `tick_interval` started feeling like test-only contamination of the production API, I'd switch to mocking. For now, the parameter approach keeps things simple and flexible.
