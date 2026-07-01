# FocusCLI

A Pomodoro-style focus timer for your terminal. Run timed focus sessions and breaks, track your history, and view personal bests — all from the command line.

## Demo

[![asciicast](https://asciinema.org/a/MP2QcmBxMPgn04bZ.svg)](https://asciinema.org/a/MP2QcmBxMPgn04bZ)

## Features

- Timed focus and break sessions with a live progress bar
- Automatic long-break prompts after a configurable number of cycles
- Post-session reflection prompts
- Multi-cycle mode to chain focus/break sessions back-to-back
- Session history, streaks, and personal best stats
- Configurable via `~/.focus.toml`

## Requirements

- Python 3.10+

## Installation

```bash
pip install -e .
```

## Usage

### Start a single focus session

```bash
focus start
```

Runs a focus session followed by a break. After enough focus sessions in a day, you'll be prompted to take a longer break assuming no break is not on. 

**Options:**

| Flag | Short | Description |
|------|-------|-------------|
| `--duration` | `-d` | Focus duration in minutes (overrides config) |
| `--task` | `-t` | Task description (default: `General Focus`) |
| `--break-duration` | `-b` | Break duration in minutes (overrides config) |
| `--no-break` | | Skip the break after the session |

```bash
focus start --duration 30 --task "Write report" --break-duration 10
focus start --no-break
```

### Run multiple focus/break cycles

```bash
focus multi-start
```

Chains multiple focus/break cycles. You'll be asked between cycles if you're ready to continue. Exits early if a session is interrupted.

**Options:**

| Flag | Short | Description |
|------|-------|-------------|
| `--number-of-cycles` | `-c` | Number of cycles to run (default: 2) |
| `--duration` | `-d` | Focus duration in minutes (overrides config) |
| `--task` | `-t` | Task description (default: `General Focus`) |
| `--break-duration` | `-b` | Break duration in minutes (overrides config) |
| `--no-break` | | Skip breaks between cycles |

```bash
focus multi-start --number-of-cycles 4 --task "Deep work"
```

### View session history

```bash
focus history
focus history --days 14
```

Shows a table of focus sessions from the last N days (default: 7). Columns include task, session type, planned vs actual duration, status, and timestamps.

### View stats

```bash
focus stats
focus stats --include-interrupted
```

Shows current streak, total sessions, sessions completed today, and total focus time. Includes a flag to also use interrupted sessions in the analysis of total break sessions, total focus sessions, and total time focusing stats.

### View personal bests

```bash
focus personal-best
focus personal-best --include-interrupted
```

Shows longest streak, most focus sessions in a single day, and longest focus session.
Includes a flag to also use interrupted sessions in analysis for most focus minutes in a session



### View configuration

```bash
focus config
```

### Reset all session data

```bash
focus reset
```

Prompts for confirmation before deleting all saved session data. Confirms delete before continuing. 

## Configuration

Create `~/.focus.toml` to override defaults:

```toml
[focus]
focus_minutes = 25
break_minutes = 5
cycles = 4
long_break_minutes = 15
```

| Setting | Default | Description |
|---------|---------|-------------|
| `focus_minutes` | 25 | Default focus session length |
| `break_minutes` | 5 | Default break length |
| `cycles` | 4 | Focus sessions before a long break is suggested |
| `long_break_minutes` | 15 | Length of the suggested long break |

Session data is saved to `~/.focus_data.json`.

## Development

Install with dev dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest --cov=focus --cov-report=term-missing
```

CLI commands are tested via their underlying helper functions rather than Click's test runner.

Lint and type check:

```bash
ruff check focus/ tests/
mypy focus/
```

CI runs on Python 3.10, 3.11, and 3.12 via GitHub Actions.

## Future work 
[ ] Add in notifications and sound 
[ ] Add a TUI 
[ ] Syncing to an external or backend service


Interested in the technical decisions behind this project? See DESIGN.md.
