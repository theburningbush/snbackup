import re
import json
import shutil
import itertools
from pathlib import Path
from datetime import date
from argparse import ArgumentParser, Namespace

import httpx

from .files import SnFiles
from .utilities import CustomLogger


FOLDERS = 'Note', 'Document', 'EXPORT', 'MyStyle', 'SCREENSHOT', 'INBOX',


def create_logger(log_file_name: str, *, running_tests=False) -> None:
    """Set up a global logger to be used throughout the program"""
    global logger
    custom = CustomLogger('INFO')
    if not running_tests:
        custom.to_file(log_file_name)
    custom.to_console()
    logger = custom.logger


def user_input() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument('-c', '--config', type=Path, default=Path().cwd().joinpath('config.json'), help='Full path to config')
    parser.add_argument('-f', '--full', action='store_true', help='Perform full backup of all notes and files')
    parser.add_argument('-i', '--inspect', action='store_true', help='Inspect device for new files to download and quit')
    parser.add_argument('-u', '--url', help='Override device URL found within config.json')
    parser.add_argument('-p', '--purge', nargs='?', type=int, const=10, help='Remove all but the last x backups.')
    parser.add_argument('-v', '--version', action='store_true', help='Print program version and quit.')
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


def get_from_device(base_url: str, uri: str) -> httpx.Response | None:
    """Retrieve html from device"""
    with httpx.Client(base_url=base_url, timeout=1) as client:
        try:
            response = client.get(uri)
            response.raise_for_status()
        except (httpx.ConnectTimeout, httpx.ConnectError) as e:
            logger.error(f'Unable to reach Supernote device: {e!r}')
            raise SystemExit()
        except httpx.HTTPError as e:
            logger.error(f'{e!r}')
            if response.status_code == 301:
                logger.info(f'{uri!r} not found')
                return None
        return response


def parse_html(html_text: str) -> list[dict] | list:
    """Search for a particular json string in html. Extract it 
    and deserialize to a dictionary. Returns list of dicts"""

    try:
        re_match = re.search(r"const json = '({.*?})'", html_text)
        parsed = re_match.group(1)
    except AttributeError as e:
        logger.error(f'Unable to extract necessary metadata from device response. Aborting: {e}')
        raise SystemExit()

    try:
        parsed_dict = json.loads(parsed)
    except json.JSONDecodeError as e:
        logger.error(e)
        parsed_dict = {}
    return parsed_dict.get('fileList', [])


def device_uri_gen(url, note_details: list[dict]):
    """Recursive generaotr to extract uri, modified date, and file size"""
    for note in note_details:
        if not note.get('isDirectory'):
            # Drop the anchor slash to call joinpath later and it work properly
            yield note.get('uri').lstrip('/'), note.get('date'), note.get('size')
        else:
            html = get_from_device(url, note.get('uri').lstrip('/'))
            new_note_details = parse_html(html.text)
            yield from device_uri_gen(url, new_note_details)


def today_pth(save_dir: str) -> Path:
    """Create today's Path object in YYYY-MM-DD format"""
    return Path(save_dir).joinpath(str(date.today()))


def save_note(local_pth: Path, note: bytes) -> None:
    """Make parent directory and write file bytes object to local disk"""
    local_pth.parent.mkdir(exist_ok=True, parents=True)

    logger.info(f'Saving {local_pth.stem!r} to {local_pth}')
    with open(local_pth, 'wb') as note_output:
        note_output.write(note)


def save_records(note_records: list[dict], json_md: Path) -> None:
    """Persist today's file metadata to json file"""
    logger.info('Saving file records to metadata json file')
    with open(json_md, 'wt') as json_out:
        print(json.dumps(note_records), file=json_out)


def previous_record_gen(json_md: Path, *, previous=None):
    """Retreive last backup metadata from json and
    yield back relevant info to instantiate file objects"""

    try:
        with open(json_md) as json_in:
            previous = json.loads(json_in.read())
    except FileNotFoundError:
        logger.warning('Unable to locate note metadata file')
        logger.info('Creating new file')
    except json.JSONDecodeError:
        logger.warning('Unable to decode json in metadata file')
    finally:
        previous = previous or []

    for record in previous:
        yield (record.get('current_loc'), record.get('uri'), 
               record.get('modified'), record.get('size'))


def check_for_deleted(current: set, previous: set) -> list[SnFiles]:
    """Look for files no longer on device from last backup"""
    symmetric = current.symmetric_difference(previous)
    return [note for note in symmetric if note not in current]


def purge_old_backups(base_dir: Path, *, num_backups=None, pattern='20??-*') -> None:
    """Delete old backups from the backup save directory on local disk"""
    if num_backups:
        logger.info(f'Purging old backups, keeping last {num_backups}')
        previous_folders = sorted(base_dir.glob(pattern), reverse=True)
        while len(previous_folders) > num_backups:
            old = previous_folders.pop()
            logger.info(f'Removing backup folder: {old}')
            shutil.rmtree(old)


def run_inspection(to_download: set) -> None:
    """Inspect current notes, determine what's new or changed, and log that out"""
    logger.info('Inspecting changes only...')
    if len(to_download) > 0:
        logger.info('New or updated files to be downloaded from device:')
    else:
        logger.info('No new or updated files found on device')
    for note in to_download:
        logger.info(f'{note.file_uri} ({int(note.file_size) / 1000**2:.2f} MB)')
    logger.info('Inspection complete')


def truncate_log(lines: int, minimum=100) -> None:
    """Truncate log to requested value or at least keep last 100 lines."""
    try:
        lines = int(lines)
    except (ValueError, TypeError):
        raise SystemExit('Warning: "truncate_log" config option should be an integer')
    else:
        lines = minimum if lines < minimum else lines

    print(f'Truncating log file to last {lines} lines')
    CustomLogger.truncate_logs(lines)


def backup() -> None:
    """Main workflow logic"""
    
    args = user_input()

    if args.version:
        from importlib.metadata import version
        raise SystemExit(f'snbackup v{version('snbackup')}')
    
    config = load_config(args.config)

    try:
        save_dir = config['save_dir']
        device_url = config['device_url']
    except KeyError:
        raise SystemExit('Unable to find "save_dir" or "device_url" in config.json file')

    num_backups = config.get('num_backups')
    truncate = config.get('truncate_log', 1000)

    if args.url:
        # TODO add validation for this url string
        device_url = args.url

    save_dir = Path(save_dir)
    json_md_file = Path(save_dir.joinpath('metadata.json'))

    create_logger(str(save_dir.joinpath('snbackup')))
    logger.info(f'Device at {device_url}')
    logger.info(f'Saving to {save_dir.absolute()}')

    all_files = []

    for folder in FOLDERS:
        httpx_response = get_from_device(device_url, folder)
        device_note_info = parse_html(httpx_response.text)
        all_files.extend(device_note_info)

    today = today_pth(save_dir)

    todays_files = {SnFiles(today, uri, mdate, size) 
                    for uri, mdate, size 
                    in device_uri_gen(device_url, all_files)}

    previous_files = {SnFiles(Path(loc), uri, mod, fsize)
                      for loc, uri, mod, fsize 
                      in previous_record_gen(json_md_file)}

    for deleted_note in check_for_deleted(todays_files, previous_files):
        previous_files.discard(deleted_note)

    if args.full:
        previous_files = set()

    to_download = todays_files.difference(previous_files)

    unchanged = todays_files.intersection(previous_files)

    if args.inspect:
        run_inspection(to_download)
        raise SystemExit()

    logger.info(f'Downloading {len(to_download)} files from device.')
    for new_note in to_download:
        download_response = get_from_device(device_url, new_note.file_uri)
        new_note.file_bytes = download_response.read()
        save_note(new_note.full_path, new_note.file_bytes)

    logger.info(f'Copying {len(unchanged)} unchanged files from local disk.')
    for current_note in unchanged:
        local_note = current_note.full_path.read_bytes()
        save_to_pth = today.joinpath(current_note.file_uri)
        save_note(save_to_pth, local_note)
        current_note.base_path = today

    if to_download or unchanged:
        records = [note.make_record() for note in itertools.chain(to_download, unchanged)]
        save_records(records, json_md_file)

    if args.purge:
        num_backups = abs(args.purge)

    purge_old_backups(save_dir, num_backups=num_backups)

    logger.info('Backup complete')

    truncate_log(truncate)