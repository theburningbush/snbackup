import json
from pathlib import Path
from datetime import date

FOLDERS = {'note': 'Note', 'document': 'Document', 'export': 'EXPORT', 'mystyle': 'MyStyle', 'screenshot': 'SCREENSHOT', 'inbox': 'INBOX'}
EXTS = '.note', '.pdf', 'epub', '.docx', '.doc', '.txt', '.png', '.jpg', '.jpeg', '.bmp', '.webp', '.cbz', '.fb2', '.xps', '.mobi'


def today_pth(save_dir: str) -> Path:
    """Create today's Path object in YYYY-MM-DD format"""
    return Path(save_dir).joinpath(str(date.today()))


def check_version(name: str) -> str:
    from importlib.metadata import version
    return f"{name} v{version(name)}"


def load_config(config_pth: Path) -> dict:
    """Load in json config file"""
    try:
        with open(config_pth) as config_in:
            return json.load(config_in)
    except FileNotFoundError:
        raise SystemExit(f'Required json config file not found at {config_pth!s}.')
    except json.JSONDecodeError:
        raise SystemExit(f'The json config is malformed or invalid. Check your config at {config_pth!s}')