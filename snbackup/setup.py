"""User interactive setup"""
import re
import json
from pathlib import Path


class SetupConf:
    """Assist in setting up a config file for application"""

    config = 'config.json'
    home_conf = Path().home().joinpath(f'.config/snbackup/{config}')

    def __init__(self) -> None:
        self.save = Path().home().joinpath('Documents/Supernote')
        self.port = '8089'
    
    def prompt(self) -> None:
        """Collect user input"""
        try:
            print(' SETUP '.center(50, '='))
            print('Where do you want to save your Supernote backups?')
            print(f'Default location is {self.save}')
            self.save = input()
            print('Connect to WiFi and enable Browse & Access on your device.')
            print('Enter the IP address for your Supernote device. For example 192.168.1.105')
            self.ip = input()
            print(f'Enter the device port number. Default is port {self.port}')
            self.port = input()
            print('How many backups would you like to keep locally?')
            print('For example 5 will keep only the five most recent backups.')
            print('Default is 0 (unlimited backups)')
            self.backups = input()
            print(' CONFIRM '.center(50, '='))
            print(f'Backing up Supernote files to {self.save}')
            print(f'Device URL is {self.url}')
            choice = input('Press Y to confirm or N to cancel: ')
            if choice.strip().upper() != 'Y':
                raise SystemExit('Canceling setup')
        except KeyboardInterrupt:
            raise SystemExit(' Canceling setup')

    @property
    def save(self) -> Path:
        return self._save
    
    @save.setter
    def save(self, save_dir: str) -> None:
        self._save = Path(save_dir) if save_dir else self.save

    @property
    def port(self) -> str:
        return self._port
    
    @port.setter
    def port(self, device_port: str) -> None:
        if device_port == '':
            return None

        expr = r'^\d{2,5}$'
        if not re.match(expr, device_port):
            print(f'Invalid device port: {device_port}')
            raise SystemExit('Aborting. Restart setup process with command "snbackup --setup"')
        self._port = device_port

    @property
    def url(self) -> str:
        return f'http://{self.ip}:{self.port}/'

    @property
    def ip(self) -> str:
        return self._ip
    
    @ip.setter
    def ip(self, addr: str) -> None:
        # Good enough IPv4 validation
        expr = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(expr, addr):
            self._ip = 'x.x.x.x'
            print(f'Invalid IPv4 address: {addr}')
            raise SystemExit('Aborting. Restart setup process with command "snbackup --setup"')
        self._ip = addr


    def _create_folders(self, *, folder: str) -> None:
        """Create save and config folders as needed"""
        try:
            if folder == 'save':
                if not self.save.exists():
                    self.save.mkdir(parents=True)
            else:
                if not self.home_conf.parent.exists():
                    self.home_conf.parent.mkdir(parents=True)
        except PermissionError as e:
            raise SystemExit(f'Unable to create folders due to OS permissions: {e}')
        except OSError as e:
            raise SystemExit(f'An OS error occurred: {e}')

    def _construct(self) -> dict:
        """Separating out to leave room for additional configs"""
        return {
            'save_dir': str(self.save),
            'device_url': self.url,
        }

    def write_config(self) -> None:
        self._create_folders(folder='save')
        self._create_folders(folder='config')
        with open(self.home_conf, 'wt') as config:
            json.dump(self._construct(), config, indent=4)
            
        

