from snbackup.notes import Note
from pathlib import Path

import pytest

@pytest.fixture
def some_note() -> Note:
    return Note(Path('/test/path/2024-08-01'),'uri/fake.note', '2024-07-04 13:45:01', 404040)


def test_save_date(some_note):
    assert some_note.save_date == '2024-08-01'


def test_full_path(some_note):
    assert some_note.full_path == Path('/test/path/2024-08-01/uri/fake.note')


def test_file_bytes(some_note):
    assert some_note.file_bytes == b''


def test_file_bytes_raises_typerror(some_note):
    with pytest.raises(TypeError):
        some_note.file_bytes = 'not_bytes_object'


def test_file_bytes_sets_properly(some_note):
    some_note.file_bytes = b'actual_bytes_object'
    some_note.file_bytes == b'actual_bytes_object'