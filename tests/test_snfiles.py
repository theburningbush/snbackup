from pathlib import Path
from datetime import datetime

import pytest

from snbackup.files import SnFiles, BadDateError


@pytest.fixture
def some_note() -> SnFiles:
    return SnFiles(Path('/test/path/2024-08-01'), 'uri/fake.note', '2024-07-04 13:45:01', 404040)


def test_save_date(some_note):
    assert some_note.save_date == '2024-08-01'


def test_full_path(some_note):
    assert some_note.full_path == Path('/test/path/2024-08-01/uri/fake.note')


def test_file_bytes(some_note):
    assert some_note.file_bytes == b''


def test_file_bytes_raises_type_error(some_note):
    with pytest.raises(TypeError) as exc_info:
        some_note.file_bytes = 'not_bytes_object'
        assert 'File must be bytes object' in str(exc_info)


def test_file_bytes_sets_properly(some_note):
    some_note.file_bytes = b'actual_bytes_object'
    assert some_note.file_bytes == b'actual_bytes_object'


def test_last_modified(some_note):
    assert some_note.last_modified == datetime.fromisoformat('2024-07-04 13:45:01')


def test_last_modified_raises_baddateerror(some_note):
    with pytest.raises(BadDateError):
        some_note.last_modified = 999

    with pytest.raises(BadDateError):
        some_note.last_modified = 'bad_value'

    assert some_note.last_modified == datetime(2000, 1, 1)


def test_make_record(some_note):
    record = {
        'saved': '2024-08-01',
        'current_loc': '/test/path/2024-08-01',
        'uri': 'uri/fake.note',
        'modified': '2024-07-04 13:45:01',
        'size': 404040,
    }
    assert some_note.make_record() == record
