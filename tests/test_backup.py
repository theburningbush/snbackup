from snbackup import backup
from tempfile import NamedTemporaryFile
from pathlib import Path
import json

import pytest

# Create global logger inside backup namespace otherwise the functions will fail
backup.create_logger(__file__, running_tests=True)


@pytest.fixture
def metadata() -> list[dict]:
    return [
        {
            'saved': '2024-08-04',
            'current_loc': '/Users/devin/Documents/Supernote/2024-08-04',
            'uri': 'Note/Misc/Random.note',
            'modified': '2024-08-02 21:35:00',
            'size': 16398389,
        },
        {
            'saved': '2024-08-04',
            'current_loc': '/Users/devin/Documents/Supernote/2024-08-04',
            'uri': 'Note/Study/Python.note',
            'modified': '2024-08-02 22:05:00',
            'size': 15292689,
        },
        {
            'saved': '2024-08-04',
            'current_loc': '/Users/devin/Documents/Supernote/2024-08-04',
            'uri': 'Note/Journal.note',
            'modified': '2024-08-04 09:03:00',
            'size': 17979631,
        },
        {
            'saved': '2024-07-31',
            'current_loc': '/Users/devin/Documents/Supernote/2024-07-31',
            'uri': 'Note/Worknotes.note',
            'modified': '2024-07-30 11:42:00',
            'size': 5591332,
        },
        {
            'saved': '2024-07-31',
            'current_loc': '/Users/devin/Documents/Supernote/2024-07-31',
            'uri': 'Note/Misc/Back+And+Forth.note',
            'modified': '2024-05-05 22:23:00',
            'size': 971630,
        },
        {
            'saved': '2024-07-31',
            'current_loc': '/Users/devin/Documents/Supernote/2024-07-31',
            'uri': 'Note/Misc/Madeup.note',
            'modified': '2024-05-16 10:49:00',
            'size': 11931839,
        },
        {
            'saved': '2024-07-31',
            'current_loc': '/Users/devin/Documents/Supernote/2024-07-31',
            'uri': 'Note/Cool.note',
            'modified': '2024-06-27 16:32:00',
            'size': 27926564,
        },
    ]


def test_previous_record_gen(metadata: list[dict]):
    # TODO look at the builtin mktemp for pytest instead of rolling your own you heathen
    with NamedTemporaryFile(mode='w+t', encoding='utf-8', prefix='dtb') as temp:
        temp.write(json.dumps(metadata))
        temp.seek(0)  # Reset back to beginning of file after write
        pth = Path(temp.name)
        data_lst = [
            (data.get('current_loc'), data.get('uri'), data.get('modified'), data.get('size')) for data in metadata
        ]
        assert list(backup.previous_record_gen(pth)) == data_lst

        temp.write('*JUNK*/^Line[{{***')  # Write in bad text so json can't deserialize
        temp.flush()
        assert list(backup.previous_record_gen(pth)) == []

    # Moved out of context so this file is now gone. Hence file not found test
    not_found_error = backup.previous_record_gen(pth)
    assert list(not_found_error) == []
