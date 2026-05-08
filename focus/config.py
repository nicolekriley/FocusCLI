'''
config.py 
Contains configuration information for the focus package CLI 
'''
from __future__ import annotations

import sys

from dataclasses import dataclass, field 
from pathlib import Path

try: 
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]


DEFAULT_FOCUS_MINUTES = 25
DEFAULT_BREAK_MINUTES = 5
DEFAULT_CYCLES = 4
DEFAULT_LONG_BREAK_MINUTES = 15
DEFAULT_LONG_FOCUS_MINUTES = 45 

CONFIG_FILE_PATH = Path.home() / "~/.focus.toml"
DATA_FILE_PATH = Path.home() / "~/.focus_data.json"

@dataclass 
class FocusConfig:
    focus_minutes: int = DEFAULT_FOCUS_MINUTES
    break_minutes: int = DEFAULT_BREAK_MINUTES
    cycles: int = DEFAULT_CYCLES
    long_break_minutes: int = DEFAULT_LONG_BREAK_MINUTES
    long_focus_minutes: int = DEFAULT_LONG_FOCUS_MINUTES
    data_path: Path = field(default_factory=lambda: DATA_FILE_PATH)

    @classmethod
    def load(cls) -> FocusConfig:
        '''Load config from ~/.focus.toml, falling back to default values.'''
        if not CONFIG_FILE_PATH.exists():
            return cls()
        with open(CONFIG_FILE_PATH, "rb") as f:
            raw = tomllib.load(f)
        cfg = raw.get("focus", {})
        return cls(
            focus_minutes=cfg.get("focus_minutes", DEFAULT_FOCUS_MINUTES),
            break_minutes=cfg.get("break_minutes", DEFAULT_BREAK_MINUTES),
            cycles=cfg.get("cycles", DEFAULT_CYCLES),
            long_break_minutes=cfg.get("long_break_minutes", DEFAULT_LONG_BREAK_MINUTES),
            long_focus_minutes=cfg.get("long_focus_minutes", DEFAULT_LONG_FOCUS_MINUTES),
            data_path=Path(cfg.get("data_path", str(Path.home() / "~/.focus_data.json"))),
        )

        
    
    def show(self):
        return {
            "Focus duration": f"{self.focus_minutes} min",
            "Break duration": f"{self.break_minutes} min",
            "Cycles before long break": self.cycles,
            "Long break duration": f"{self.long_break_minutes} min",
            "Long focus duration": f"{self.long_focus_minutes} min",
        }
