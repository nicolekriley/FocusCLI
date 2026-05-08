'''
test functionality of FocusConfig class in config.py
'''

from focus.config import FocusConfig
import focus.config as config_module
from pathlib import Path
import pytest

def test_load_defaults():
    cfg = FocusConfig.load()
    assert cfg.focus_minutes == 25
    assert cfg.break_minutes == 5
    assert cfg.cycles == 4
    assert cfg.long_break_minutes == 15
    assert cfg.long_focus_minutes == 45
    assert str(cfg.data_path) == str(Path.home() / ".focus_data.json")

def test_show():
    cfg = FocusConfig()
    display = cfg.show()
    assert display["Focus duration"] == "25 min"
    assert display["Break duration"] == "5 min"
    assert display["Cycles before long break"] == 4
    assert display["Long break duration"] == "15 min"
    assert display["Long focus duration"] == "45 min"

@pytest.fixture(autouse=False)
def override_config_path(tmp_path):
    '''
    Fixture to override CONFIG_FILE_PATH for testing load from file without affecting real config.
    '''
    original_path = config_module.CONFIG_FILE_PATH
    config_file = tmp_path / "focus.toml"
    config_module.CONFIG_FILE_PATH = config_file
    yield config_file
    config_module.CONFIG_FILE_PATH = original_path

def test_load_from_file(override_config_path):
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