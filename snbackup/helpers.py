import os
import json
from pathlib import Path
from datetime import date
from argparse import ArgumentParser, Namespace

FOLDERS = {
    'note': 'Note', 
    'document': 'Document', 
    'export': 'EXPORT', 
    'mystyle': 'MyStyle', 
    'screenshot': 'SCREENSHOT', 
    'inbox': 'INBOX',
}

EXTS = {
    '.note', '.pdf', '.epub', '.docx', '.doc', 
    '.txt', '.png', '.jpg', '.jpeg', '.bmp', 
    '.webp', '.cbz', '.fb2', '.xps', '.mobi',
}

CONFIG_ENV = os.getenv('SNBACKUP_CONF', Path().cwd().joinpath('config.json'))


def user_input() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument('-c', '--config', type=Path, default=CONFIG_ENV, help='Path to config.json file')
    parser.add_argument('-f', '--full', action='store_true', help='Download all notes and files from device. Disregard any saved locally.')
    parser.add_argument('-i', '--inspect', action='store_true', help='Inspect device for new files to download and quit')
    parser.add_argument('-u', '--upload', nargs='+', help='Send one or more files to device. "snbackup -u file1 file2 file3"')
    parser.add_argument(
        '-d', '--destination', default='document', type=str.lower, choices=FOLDERS, help='Destination folder to send file upload'
    )
    parser.add_argument('-ls', '--list', action='store_true', help='List out information about backups found locally')
    parser.add_argument('-v', '--version', action='store_true', help='Print program version and quit.')
    parser.add_argument(
        '--notes',
        action='store_const',
        const=['Note'],
        default=list(FOLDERS.values()),
        help='Only download notes from within the Note folder on device',
    )
    parser.add_argument(
        '--cleanup',
        nargs='?',
        type=int,
        const=10,
        help='Remove locally stored previous backups. Keeps last 10 or any supplied number.',
    )
    return parser.parse_args()


def load_config(config_pth: Path) -> dict:
    """Load in json config file"""
    try:
        with open(config_pth) as config_in:
            return json.load(config_in)
    except FileNotFoundError:
        raise SystemExit(f'Required json config file not found at {config_pth!s}.')
    except json.JSONDecodeError:
        raise SystemExit(f'The json config is malformed or invalid. Check your config at {config_pth!s}')


def today_pth(save_dir: Path) -> Path:
    """Create today's Path object in YYYY-MM-DD format"""
    return save_dir.joinpath(str(date.today()))


def check_version(name: str) -> str:
    from importlib.metadata import version
    return f"{name} v{version(name)}"


def bytes_to_mb(byte_size: int) -> str:
    """Convert bytes to Megabytes"""
    return format(byte_size / 1000**2, '.2f')


def count_backups(directory: Path, pattern='202?-*') -> tuple:
    """Counts number of backup folders and returns oldest and 
    newest found on local disk"""

    previous = sorted(directory.glob(pattern))
    return len(previous), previous[0], previous[-1]


def recursive_scan(path: Path) -> int:
    """Scan a directory and return total size of files in bytes"""
    if path.is_file():
        return path.stat().st_size
    return sum(recursive_scan(item) for item in path.iterdir())
