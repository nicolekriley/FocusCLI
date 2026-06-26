'''
test functionality of FocusConfig class in config.py
'''

from focus.config import FocusConfig, DEFAULT_BREAK_MINUTES, DEFAULT_CYCLES, DEFAULT_FOCUS_MINUTES, DEFAULT_LONG_BREAK_MINUTES, DEFAULT_LONG_FOCUS_MINUTES
import focus.config as config_module
from pathlib import Path
import pytest
from typing import Generator

def test_load_defaults() -> None:
    cfg = FocusConfig.load()
    assert cfg.focus_minutes == DEFAULT_FOCUS_MINUTES
    assert cfg.break_minutes == DEFAULT_BREAK_MINUTES
    assert cfg.cycles == DEFAULT_CYCLES
    assert cfg.long_break_minutes == DEFAULT_LONG_BREAK_MINUTES
    assert cfg.long_focus_minutes == DEFAULT_LONG_FOCUS_MINUTES
    assert str(cfg.data_path) == str(Path.home() / ".focus_data.json")


def test_show() -> None:
    cfg = FocusConfig()
    display = cfg.show()
    assert display["Focus duration"] == str(DEFAULT_FOCUS_MINUTES) + " min"
    assert display["Break duration"] == str(DEFAULT_BREAK_MINUTES) + " min"
    assert display["Cycles before long break"] == DEFAULT_CYCLES
    assert display["Long break duration"] == str(DEFAULT_LONG_BREAK_MINUTES) + " min"
    assert display["Long focus duration"] == str(DEFAULT_LONG_FOCUS_MINUTES) + " min"


@pytest.fixture(autouse=False) 
def override_config_path(tmp_path: Path) -> Generator[Path, None, None]:
    '''
    Fixture to override CONFIG_FILE_PATH for testing load from file without affecting real config.
    '''
    original_path = config_module.CONFIG_FILE_PATH
    config_file = tmp_path / "focus.toml"
    config_module.CONFIG_FILE_PATH = config_file
    yield config_file
    config_module.CONFIG_FILE_PATH = original_path


def test_load_from_file(override_config_path: Path) -> None:
    config_content = """
    [focus]
    focus_minutes = 30
    break_minutes = 10
    cycles = 3
    long_break_minutes = 20
    long_focus_minutes = 60
    data_path = "/tmp/focus_data.json"
    """
    override_config_path.write_text(config_content)
    
    cfg = FocusConfig.load()
    assert cfg.focus_minutes == 30
    assert cfg.break_minutes == 10
    assert cfg.cycles == 3
    assert cfg.long_break_minutes == 20
    assert cfg.long_focus_minutes == 60
    assert str(cfg.data_path) == "/tmp/focus_data.json"