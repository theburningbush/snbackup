import os
import json
import httpx
import itertools
import shutil
from pathlib import Path
from datetime import date
from argparse import ArgumentParser

from .notes import Note
from .utilities import CustomLogger


def create_logger(log_file_name: str, *, running_tests=False) -> None:
    """Sets up a global logger to be used throughout the program"""
    global logger
    my_logger = CustomLogger('INFO')
    if not running_tests:
        my_logger.to_file(log_file_name)
    my_logger.to_console()
    logger = my_logger.get_logger()


def user_input() -> tuple[Path, bool, bool, str, int]:
    parser = ArgumentParser()
    parser.add_argument('-c', '--config', type=Path, default=Path(f'{os.getcwd()}/config.json'), help='Full path to config')
    parser.add_argument('-f', '--full', action='store_true', help='Perform full backup of all notes')
    parser.add_argument('-i', '--inspect', action='store_true', help='Inspect device for new downloads and quit')
    parser.add_argument('-u', '--url', help='Override device URL found within config.json')
    parser.add_argument('-p', '--purge', nargs='?', type=int, const=10, help='Remove all but the last x backups.')
    args = parser.parse_args()
    return args.config, args.full, args.inspect, args.url, args.purge


def load_config(config_pth: Path) -> dict:
    """Load in json config file"""
    try:
        with open(config_pth) as config_in:
            return json.load(config_in)
    except FileNotFoundError:
        raise SystemExit(f'JSON config file not found at {config_pth!s}.')
    except json.JSONDecodeError:
        raise SystemExit(f'JSON file malformed or invalid. Check your config at {config_pth!s}')


def get_from_device(base_url: str, uri: str) -> httpx.Response | None:
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


def parse_html(html_text: str) -> list[dict] | None:
    if 'const json =' in html_text:
        # TODO: use regex
        parsed_json = html_text.split('const json = ')[1].split("console.log('json=' + json")[0].strip().strip("'")
        try:
            parsed_dict = json.loads(parsed_json)
        except json.JSONDecodeError as e:
            logger.error(e)
            parsed_dict = {}
        return parsed_dict.get('fileList')


def device_uri_gen(url, note_details: list[dict]):
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
    """Makes parent directory then writes
    note bytes to local disk"""

    local_pth.parent.mkdir(exist_ok=True, parents=True)

    logger.info(f'Saving {local_pth.stem!r} to {local_pth}')
    with open(local_pth, 'wb') as note_output:
        note_output.write(note)


def save_records(note_records: list[dict], json_md: Path) -> None:
    """Persists today's note metadata to json file"""
    logger.info('Saving note records to metadata json file')
    with open(json_md, 'wt') as json_out:
        print(json.dumps(note_records), file=json_out)


def previous_record_gen(json_md: Path, *, previous=None):
    """Retreives last backup metadata from json and
    yields back relevant info to serialize Note objects"""

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


def check_for_deleted(current: set, previous: set) -> list[Note]:
    """Looks for notes no longer on device from last backup"""
    symmetric = current.symmetric_difference(previous)
    return [note for note in symmetric if note not in current]


def purge_old_backups(base_dir: Path, *, num_backups=None, pattern='20??-*') -> None:
    """Deletes old backups from the backup save directory"""
    if num_backups:
        logger.info(f'Purging old backups, keeping last {num_backups}')
        previous_folders = sorted(base_dir.glob(pattern), reverse=True)
        while len(previous_folders) > num_backups:
            old = previous_folders.pop()
            logger.info(f'Removing backup folder: {old}')
            shutil.rmtree(old)


def backup() -> None:
    """Main workflow logic"""
    config_file, full_backup, inspect, url_override, purge_old = user_input()
    config = load_config(config_file)

    try:
        save_dir = config['save_dir']
        device_url = config['device_url']
    except KeyError:
        raise SystemExit('Unable to find "save_dir" or "device_url" in config file')

    num_backups = config.get('num_backups')

    if url_override:
        # TODO add validation on this so it looks like valid URL
        device_url = url_override

    save_dir = Path(save_dir)
    json_md_file = Path(save_dir.joinpath('metadata.json'))

    create_logger(str(save_dir.joinpath('snbackup')))
    logger.info(f'Device at {device_url}')
    logger.info(f'Saving to {save_dir.absolute()}')

    httpx_response = get_from_device(device_url, 'Note')
    device_note_info = parse_html(httpx_response.text)

    today = today_pth(save_dir)

    todays_notes = {Note(today, uri, mdate, size) 
                    for uri, mdate, size 
                    in device_uri_gen(device_url, device_note_info)}

    previous_notes = {Note(Path(loc), uri, mod, fsize) 
                      for loc, uri, mod, fsize 
                      in previous_record_gen(json_md_file)}

    for deleted_note in check_for_deleted(todays_notes, previous_notes):
        previous_notes.discard(deleted_note)

    if full_backup:
        previous_notes = set()

    to_download = todays_notes.difference(previous_notes)

    unchanged = todays_notes.intersection(previous_notes)

    if inspect:
        logger.info('Inspecting changes only...')
        logger.info('New/updated notes to be downloaded from device:')
        for note in to_download:
            logger.info(f'Note: {note.note_uri}, Size: {int(note.file_size) / 1000**2:.2f} MB')
        logger.info('Inspection complete')
        raise SystemExit()

    logger.info(f'Downloading {len(to_download)} new notes from device.')
    for new_note in to_download:
        download_response = get_from_device(device_url, new_note.note_uri)
        new_note.file_bytes = download_response.read()
        save_note(new_note.full_path, new_note.file_bytes)

    logger.info(f'Merging {len(unchanged)} unchanged notes from local disk')
    for current_note in unchanged:
        local_note = current_note.full_path.read_bytes()
        save_to_pth = today.joinpath(current_note.note_uri)
        save_note(save_to_pth, local_note)
        current_note.base_path = today

    records = [note.make_record() for note in itertools.chain(to_download, unchanged)]
    save_records(records, json_md_file)

    if purge_old:
        num_backups = abs(purge_old)

    purge_old_backups(save_dir, num_backups=num_backups)

    logger.info('Backup complete')
