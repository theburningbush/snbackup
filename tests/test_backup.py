from snbackup import backup
from tempfile import NamedTemporaryFile
from pathlib import Path
import textwrap
import json
import sys

from snbackup.notes import Note

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


@pytest.fixture
def html_text() -> str:
    return textwrap.dedent("""            
                <div id="table-item" class="table-item" style="width:100%;height: 100%;overflow: auto">
                    <table class="table item">
                        <colgroup>
                            <col style="width: 60%">
                            <col style="width: 20%">
                            <col style="width: 20%">
                        </colgroup>
                        <!--                <tbody> 标签用于组合 HTML 表格的主体内容。-->
                        <tbody id="item-container" style="width:100%;height: 100%;">

                        </tbody>
                    </table>
                </div>

            </div>
        </div>
    </div>

    </body>


    <script>

        const json = '{"availableMemory":23330586624,"deviceName":"Supernote","fileList":[{"date":"2024-07-17 21:19","extension":"","isDirectory":true,"name":"Work","size":0,"uri":"/Note/Work"},{"date":"2024-07-13 22:17","extension":"","isDirectory":true,"name":"Study","size":0,"uri":"/Note/Study"},{"date":"2024-07-12 08:19","extension":"","isDirectory":true,"name":"Misc","size":0,"uri":"/Note/Misc"},{"date":"2024-07-11 10:31","extension":"note","isDirectory":false,"name":"Today.note","size":8675309,"uri":"/Note/Today.note"},{"date":"2024-06-27 16:32","extension":"note","isDirectory":false,"name":"Tomorrow.note","size":27926564,"uri":"/Note/Tomorrow.note"},{"date":"2024-07-19 08:25","extension":"note","isDirectory":false,"name":"Yesterday.note","size":12221169,"uri":"/Note/Yesterday.note"},{"date":"2024-05-23 08:21","extension":"note","isDirectory":false,"name":"Stuff.note","size":4726881,"uri":"/Note/Stuff.note"},{"date":"2024-06-09 05:53","extension":"note","isDirectory":false,"name":"ABC123.note","size":786656,"uri":"/Note/ABC123.note"}],"routeList":[{"name":"Supernote","path":"/"},{"name":"Note","path":"/Note"}],"totalMemory":32.0}'
        console.log('json=' + json)
        const webInfo = JSON.parse(json)

        document.title = webInfo.deviceName
        document.getElementById('title').innerText = webInfo.deviceName
        setAvailableMemory(webInfo.availableMemory)

        const itemContainerDocument = document.getElementById('item-container')
        const mainElement = document.getElementById('main');
                           
    """)


def test_previous_record_gen(metadata):
    # TODO look at the builtin mktemp for pytest instead of rolling your own you heathen
    with NamedTemporaryFile(mode='w+t', encoding='utf-8', prefix='dtb', delete_on_close=False) as temp:
        temp.write(json.dumps(metadata))
        temp.seek(0)  # Reset back to beginning of file after write
        pth = Path(temp.name)
        data_lst = [
            (data.get('current_loc'), data.get('uri'), data.get('modified'), data.get('size')) for data in metadata
        ]
        assert list(backup.previous_record_gen(pth)) == data_lst

        temp.write('*JUNK*/^Line[{{***')  # Write in bad text overtop json so it can't deserialize properly
        temp.flush()  # Force the write
        assert list(backup.previous_record_gen(pth)) == []

    # Moved out of context so this file is now gone. Hence file not found test
    not_found_error = backup.previous_record_gen(pth)
    assert list(not_found_error) == []


def test_parse_html(html_text):
    response = [
        {
            'date': '2024-07-17 21:19',
            'extension': '',
            'isDirectory': True,
            'name': 'Work',
            'size': 0,
            'uri': '/Note/Work',
        },
        {
            'date': '2024-07-13 22:17',
            'extension': '',
            'isDirectory': True,
            'name': 'Study',
            'size': 0,
            'uri': '/Note/Study',
        },
        {
            'date': '2024-07-12 08:19',
            'extension': '',
            'isDirectory': True,
            'name': 'Misc',
            'size': 0,
            'uri': '/Note/Misc',
        },
        {
            'date': '2024-07-11 10:31',
            'extension': 'note',
            'isDirectory': False,
            'name': 'Today.note',
            'size': 8675309,
            'uri': '/Note/Today.note',
        },
        {
            'date': '2024-06-27 16:32',
            'extension': 'note',
            'isDirectory': False,
            'name': 'Tomorrow.note',
            'size': 27926564,
            'uri': '/Note/Tomorrow.note',
        },
        {
            'date': '2024-07-19 08:25',
            'extension': 'note',
            'isDirectory': False,
            'name': 'Yesterday.note',
            'size': 12221169,
            'uri': '/Note/Yesterday.note',
        },
        {
            'date': '2024-05-23 08:21',
            'extension': 'note',
            'isDirectory': False,
            'name': 'Stuff.note',
            'size': 4726881,
            'uri': '/Note/Stuff.note',
        },
        {
            'date': '2024-06-09 05:53',
            'extension': 'note',
            'isDirectory': False,
            'name': 'ABC123.note',
            'size': 786656,
            'uri': '/Note/ABC123.note',
        },
    ]
    assert backup.parse_html(html_text) == response


def test_check_for_deleted():
    set_1 = {Note(Path('/test/path/2024-08-01'), f'uri/fake_{n}.note', '2024-07-04 13:45:01', 404040) for n in range(5)}
    set_2 = {Note(Path('/test/path/2024-08-01'), f'uri/fake_{n}.note', '2024-07-04 13:45:01', 404040) for n in range(5)}

    set_1.add(Note(Path('/test/path/2024-08-01'), 'uri/only_set_1.note', '2024-07-04 13:45:01', 404040))

    one = Note(Path('/test/path/2024-08-01'), 'uri/only_set_2_one.note', '2024-07-04 13:45:01', 404040)
    two = Note(Path('/test/path/2024-08-01'), 'uri/only_set_2_two.note', '2024-07-04 13:45:01', 404040)
    set_2.add(one)
    set_2.add(two)
    
    assert backup.check_for_deleted(set_1, set_2) == [one, two]


def test_user_input():
    # Running this one last since I'm altering sys.argv. Doesn't seem to impact anything else but just in case - could also make context manager
    # Passing in all currently available cli flags
    sys.argv[1:] = ['-c', 'path/to/test_config.json', '-f', '-i', '-u', 'http://192.168.1.100:8089', '-p', '5']
    assert backup.user_input() == (Path('path/to/test_config.json'), True, True, 'http://192.168.1.100:8089', 5)
    sys.argv = ['']  # Pretending we're calling command with no additional cli flags
    assert backup.user_input() == (Path().cwd().joinpath('config.json'), False, False, None, None)


def test_load_config():
    config_dict = {'save_dir': '/Users/devin/Documents/Supernote', 'device_url': 'http://192.168.1.105:8089/'}
    with NamedTemporaryFile(mode='w+t', encoding='utf-8', prefix='dtb', delete_on_close=False) as temp:
        temp.write(json.dumps(config_dict))
        temp.seek(0)
        pth = Path(temp.name)
        assert backup.load_config(pth) == config_dict
