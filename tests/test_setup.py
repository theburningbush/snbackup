from pathlib import Path

from snbackup.setup import SetupConf

import pytest

@pytest.fixture
def setup_conf() -> SetupConf:
    return SetupConf()


def test_defaults(setup_conf):
    sc = setup_conf
    assert (sc.save, sc.port, sc.backups, sc.cleanup) == (
        Path().home().joinpath('Documents/Supernote'),
        '8089',
        0,
        False
    )

    assert (sc.config, sc.home_conf) == (
        'config.json',
        Path().home() / '.config/snbackup/config.json'
    )
