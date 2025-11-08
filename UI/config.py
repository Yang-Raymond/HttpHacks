# focusdock/storage/config.py
import yaml
from pathlib import Path

# Define where config.yaml lives (using current folder for simplicity)
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

# Default config
DEFAULT_CONFIG = {
    "durations": {"short": 25, "medium": 50, "long": 90},
    "blocked_apps": ["chrome.exe", "spotify.exe"],
    "blocked_sites": ["facebook.com", "youtube.com"],
    "app_block_mode": "polite"
}

def read_config():
    """Read config.yaml or return defaults if not found."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            try:
                data = yaml.safe_load(f)
                if data is None:
                    return DEFAULT_CONFIG.copy()
                return data
            except Exception:
                return DEFAULT_CONFIG.copy()
    else:
        return DEFAULT_CONFIG.copy()

def write_config(config):
    """Save config dict to config.yaml"""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.safe_dump(config, f)
