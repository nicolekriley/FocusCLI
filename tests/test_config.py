'''
test functionality of FocusConfig class in config.py
'''

from focus.config import FocusConfig
import focus.config as config_module
from pathlib import Path

def test_load_defaults():
    cfg = FocusConfig.load()
    assert cfg.focus_minutes == 25
    assert cfg.break_minutes == 5
    assert cfg.cycles == 4
    assert cfg.long_break_minutes == 15
    assert cfg.long_focus_minutes == 45
    assert str(cfg.data_path) == str(Path.home() / "~/.focus_data.json")

def test_show():
    cfg = FocusConfig()
    display = cfg.show()
    assert display["Focus duration"] == "25 min"
    assert display["Break duration"] == "5 min"
    assert display["Cycles before long break"] == 4
    assert display["Long break duration"] == "15 min"
    assert display["Long focus duration"] == "45 min"

def test_load_from_file(tmp_path):
    config_content = """
    [focus]
    focus_minutes = 30
    break_minutes = 10
    cycles = 3
    long_break_minutes = 20
    long_focus_minutes = 60
    data_path = "/tmp/focus_data.json"
    """
    config_file = tmp_path / "focus.toml"
    config_file.write_text(config_content)

    # Override the CONFIG_FILE_PATH to point to our temp file
    config_module.CONFIG_FILE_PATH = config_file
    
    cfg = FocusConfig.load()
    assert cfg.focus_minutes == 30
    assert cfg.break_minutes == 10
    assert cfg.cycles == 3
    assert cfg.long_break_minutes == 20
    assert cfg.long_focus_minutes == 60
    assert str(cfg.data_path) == "/tmp/focus_data.json"