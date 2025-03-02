import sys
import json
import tomllib
from pathlib import Path
from datetime import date
from tempfile import NamedTemporaryFile

import pytest

from snbackup import helpers


class ArgvSwitcher:
    def __init__(self, current):
        self.current = list(current)

    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        sys.argv = self.current


def test_user_input():
    all_args = [
        '-c', 'path/to/test_config.json', '-f', 
        '-i', '-u', 'file1', '-d', 'note', '-ls',
        '-v', '--notes', '--cleanup', '--setup'
    ]
    
    all_args_results = (
        Path('path/to/test_config.json'), True, True,
        ['file1'], 'note', True, True, ['Note'], 10, True
    )
    
    zero_args_results = (
        None, False, False, 
        None, 'document', False, False, list(helpers.FOLDERS.values()), None, False
    )
    
    with ArgvSwitcher(sys.argv):
        sys.argv[1:] = all_args
        ns = helpers.user_input()  # Namespace
        assert (ns.config, ns.full, ns.inspect, ns.upload, ns.destination, ns.list, ns.version, ns.notes, ns.cleanup, ns.setup) == all_args_results

        sys.argv = ['']
        ns = helpers.user_input()
        assert (ns.config, ns.full, ns.inspect, ns.upload, ns.destination, ns.list, ns.version, ns.notes, ns.cleanup, ns.setup) == zero_args_results


def test_load_config():
    config_dict = {'save_dir': '/Users/devin/Documents/Supernote', 'device_url': 'http://192.168.1.105:8089/'}
    with NamedTemporaryFile(mode='w+t', encoding='utf-8', prefix='dtb', delete_on_close=False) as temp:
        temp.write(json.dumps(config_dict))
        temp.flush() 
        pth = Path(temp.name)
        assert helpers.load_config(pth) == config_dict

        temp.seek(0)
        temp.write(json.dumps('JUNK1Z$:$((]]:')) 
        temp.flush()
        with pytest.raises(SystemExit) as exc_info: 
            helpers.load_config(pth)
        assert f'Check your config at {temp.name}' in str(exc_info.value)

    with pytest.raises(SystemExit) as exc_info:  
        helpers.load_config(pth)  
    assert f'file not found at' in str(exc_info)


def test_today_path():
    todays_date = date.today()
    test_path = '/some/test/path'
    assert Path(f'{test_path}/{todays_date}') == helpers.today_pth(Path(test_path))


def test_check_version():
    """Read name and version number from pyproject.toml file"""
    try:
        with open('pyproject.toml', 'rb') as toml:
            data = tomllib.load(toml)
    except FileNotFoundError:
        with open('../pyproject.toml', 'rb') as toml:
            data = tomllib.load(toml)
    
    project = data.get('project', {})
    bad = 'INVALID'
    name = project.get('name', bad)
    version = project.get('version', bad)

    assert f'{name} v{version}' == helpers.check_version(name)


def test_bytes_to_mb():
    size1 = 23570000
    size2 = 10000000
    assert '23.57' == helpers.bytes_to_mb(size1)
    assert '10.00' == helpers.bytes_to_mb(size2)
