import os
import re
import json
import shutil
import itertools as it
from pathlib import Path

import httpx

from .files import SnFiles
from .device import Device
from .setup import SetupConf
from .utilities import CustomLogger, truncate_log
from .helpers import (
    EXTS,
    FOLDERS,
    user_input,
    check_version,
    today_pth,
    load_config,
    bytes_to_mb,
    count_backups,
    recursive_scan,
    locate_config,
)


def create_logger(log_file_name: str, level='INFO', *, running_tests=False) -> None:
    """Set up a global logger to be used throughout the program."""
    global logger
    custom = CustomLogger(level)
    if not running_tests:
        custom.to_file(log_file_name)
    custom.to_console()
    logger = custom.logger


def talk_to_device(device: Device, uri: str, document=None) -> httpx.Response:
    """Wrapper to handle calling device, logging, and managing exceptions"""
    try:
        response = device.http_request(uri, document)
    except (httpx.ConnectTimeout, httpx.ConnectError) as e:
        logger.error(f'Unable to reach Supernote device: {e!r}')
        raise SystemExit(1)
    except httpx.HTTPError as e:
        logger.error(f'Unhandled error: {e!r}')
        raise SystemExit(1)
    return response


def parse_html(html_text: str, regex_str=r"const json = '(?P<json_str>{.*?})'") -> str:
    """Search for and extract a particular json string in html."""
    try:
        re_match = re.search(regex_str, html_text)
        parsed = re_match.group('json_str')
    except AttributeError as e:
        logger.error(f'Unable to extract necessary data from device: {e!r}')
        raise SystemExit(1)
    return parsed


def load_parsed(parsed: str) -> list[dict] | list:
    """Deserialize json extracted from device for creating file objects."""
    try:
        parsed_dict = json.loads(parsed)
    except json.JSONDecodeError as e:
        logger.error(e)
        parsed_dict = {}
    return parsed_dict.get('fileList', [])


def device_uri_gen(device: Device, file_details: list[dict]):
    """Recursive generator to extract uri, modified date, and file size."""
    for file in file_details:
        file_uri = file.get('uri').lstrip('/')  # Drop anchor slash to call joinpath later and it work
        if not file.get('isDirectory'):
            yield file_uri, file.get('date'), file.get('size')
        else:
            html = talk_to_device(device, file_uri)
            re_parse = parse_html(html.text)
            new_file_details = load_parsed(re_parse)
            yield from device_uri_gen(device, new_file_details)


def save_file(local_pth: Path, file: bytes) -> None:
    """Make parent directory and write file bytes object to local disk."""
    local_pth.parent.mkdir(exist_ok=True, parents=True)

    logger.info(f'Saving {local_pth.stem!r} to {local_pth}')
    with open(local_pth, 'wb') as file_output:
        file_output.write(file)
        file_output.flush()
        os.fsync(file_output.fileno())


def save_records(file_records: list[dict], json_md: Path) -> None:
    """Persist today's file metadata to json file."""
    logger.info('Saving file records to metadata json file')
    with open(json_md, 'wt') as json_out:
        print(json.dumps(file_records), file=json_out)


def previous_record_gen(json_md: Path, *, previous=None):
    """Retreive last backup metadata found locally and yield
    back relevant info to instantiate file objects.
    """
    try:
        with open(json_md) as json_in:
            previous = json.loads(json_in.read())
    except FileNotFoundError:
        logger.warning('Unable to locate metadata file. Creating new file')
    except json.JSONDecodeError:
        logger.warning('Unable to decode json in metadata file')
    finally:
        previous = previous or []

    for record in previous:
        yield (record.get('current_loc'), record.get('uri'), record.get('modified'), record.get('size'))


def check_for_deleted(current: set, previous: set) -> list[SnFiles]:
    """Look for files no longer on device from last backup."""
    symmetric = current.symmetric_difference(previous)
    return [file for file in symmetric if file not in current]


def prepare_upload(ufile: list):
    """Prepare file upload to send to device."""
    for file in (Path(file) for file in ufile):
        if file.is_file() and file.suffix.casefold() in EXTS:
            yield {f'{file.name}': open(file, 'rb')}


def upload_files(device: Device, to_upload: list, destination: str) -> str | None:
    """Uploads chosen files to remote device."""
    response = None
    for file in prepare_upload(to_upload):
        response = talk_to_device(device, destination, file)
        for resp in response.json():
            file, size = resp.get('name'), resp.get('size', 0)
            logger.info(f'Uploaded {file} to {destination} folder ({bytes_to_mb(size)} MB)')
    return 'Upload complete' if response else None


def cleanup_backups(base_dir: Path, *, num_backups=0, cleanup=False, pattern='202?-*') -> None:
    """Delete old backups from the backup save directory on local disk."""
    if num_backups > 0 and cleanup:
        logger.info(f'Removing old backups, keeping last {num_backups}')
        previous_folders = sorted(base_dir.glob(pattern), reverse=True)
        while len(previous_folders) > num_backups:
            old = previous_folders.pop()
            logger.info(f'Removing backup folder: {old}')
            shutil.rmtree(old)


def run_inspection(to_download: set) -> None:
    """Inspect current files, determine what's new or changed, and log that out."""
    logger.info('Inspecting changes only')
    if len(to_download) > 0:
        logger.info('Listing new or updated files to download:')
    else:
        logger.info('No new or updated files to download.')
    for c, file in enumerate(to_download, start=1):
        logger.info(f'{c}.{file.file_uri} ({bytes_to_mb(file.file_size)} MB)')
    logger.info('Inspection complete')


def backup() -> None:
    """Main workflow logic."""
    args = user_input()

    if args.version:
        print(check_version('snbackup'))
        raise SystemExit()

    if args.setup:
        setup = SetupConf()
        setup.prompt()
        setup.write_config()
        print(f'Config file created at {setup.home_conf}')
        print('Setup complete.')
        print('Run "snbackup -i" to inspect downloads or "snbackup" to start backup process.')
        raise SystemExit()

    if not args.config:
        args.config = locate_config()

    config = load_config(args.config)

    try:
        save_dir = config['save_dir']
        device_url = config['device_url']
    except KeyError:
        raise SystemExit('Unable to find "save_dir" or "device_url" in config.json file')

    num_backups = config.get('num_backups', 0)
    cleanup = config.get('cleanup', False)
    truncate = config.get('truncate_log', 1000)

    save_dir = Path(save_dir)
    if not save_dir.is_dir():
        raise SystemExit(f'Unable to locate or write to {save_dir}')

    metadata_file = Path(save_dir.joinpath('metadata.json'))

    create_logger(str(save_dir.joinpath('snbackup')))

    logger.info(f'Loaded config {args.config}')

    if args.list:
        num, oldest, latest = count_backups(save_dir)
        logger.info(f'{num} backups found in {save_dir} ({bytes_to_mb(recursive_scan(save_dir))} MB)')
        logger.info(f'Oldest backup: {oldest.name} ({bytes_to_mb(recursive_scan(oldest))} MB)')
        logger.info(f'Latest backup: {latest.name} ({bytes_to_mb(recursive_scan(latest))} MB)')
        raise SystemExit()

    device = Device(device_url)
    logger.info(f'Device at {device.base_url}')

    try:
        if args.upload:
            resp = upload_files(device, args.upload, FOLDERS.get(args.destination))
            msg = resp if resp else 'No files to upload.'
            logger.info(msg)
            raise SystemExit()

        logger.info(f'Saving files to {save_dir.absolute()}')

        all_files = []

        for folder in args.notes:
            httpx_response = talk_to_device(device, folder)
            re_parse = parse_html(httpx_response.text)
            device_data = load_parsed(re_parse)
            all_files.extend(device_data)

        today = today_pth(save_dir)

        todays_files = {
            SnFiles(today, uri, mdate, size)
            for uri, mdate, size in device_uri_gen(device, all_files)
        }

        previous_files = {
            SnFiles(Path(loc), uri, mod, fsize)
            for loc, uri, mod, fsize in previous_record_gen(metadata_file)
        }

        for deleted_file in check_for_deleted(todays_files, previous_files):
            previous_files.discard(deleted_file)

        if args.full:
            previous_files = set()

        to_download = todays_files.difference(previous_files)

        unchanged = todays_files.intersection(previous_files)

        if args.inspect:
            run_inspection(to_download)
            raise SystemExit()

        logger.info(f'Downloading {len(to_download)} files from device.')
        for new_file in to_download:
            download_response = talk_to_device(device, new_file.file_uri)
            new_file.file_bytes = download_response.read()
            save_file(new_file.full_path, new_file.file_bytes)

        logger.info(f'Copying {len(unchanged)} unchanged files from local disk.')
        for previous_file in unchanged:
            local_file = previous_file.full_path.read_bytes()
            save_to_pth = today.joinpath(previous_file.file_uri)
            save_file(save_to_pth, local_file)
            previous_file.base_path = today
    finally:
        device.close()

    if to_download or unchanged:
        records = [snfile.make_record() for snfile in it.chain(to_download, unchanged)]
        save_records(records, metadata_file)

    if args.cleanup:
        num_backups = abs(args.cleanup)
        cleanup = True

    cleanup_backups(save_dir, num_backups=num_backups, cleanup=cleanup)

    logger.info('Backup complete')

    truncate_log(truncate)
