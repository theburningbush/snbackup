from pathlib import Path
from hashlib import sha256
from datetime import datetime
from functools import total_ordering


class BytesEmptyError(Exception):
    """Bytes object empty"""


class BadDateError(Exception):
    """Bad datetime format or value"""


@total_ordering
class SnFiles:
    """Represent an individual Supernote file"""

    def __init__(self, base_path: Path, file_uri: str, last_modified: str, file_size: int) -> None:
        self.base_path = base_path
        self.file_uri = file_uri
        self.last_modified = last_modified
        self.file_size = file_size
        self.file_bytes = b''

    @property
    def save_date(self) -> str:
        return self.base_path.name

    @property
    def full_path(self) -> Path:
        return self.base_path.joinpath(self.file_uri)

    @property
    def file_bytes(self) -> bytes:
        return self._file_bytes

    @file_bytes.setter
    def file_bytes(self, bytes_obj: bytes) -> None:
        if not isinstance(bytes_obj, bytes):
            raise TypeError('File must be bytes object')
        self._file_bytes = bytes_obj

    @property
    def file_hash(self) -> str:
        if self.file_bytes == b'':
            raise BytesEmptyError(f'File is empty: {self.file_bytes!r}')
        return sha256(self.file_bytes).hexdigest()

    @property
    def last_modified(self) -> datetime:
        return self._last_modified

    @last_modified.setter
    def last_modified(self, mod_date: str) -> None:
        try:
            self._last_modified = datetime.fromisoformat(mod_date)
        except (ValueError, TypeError) as e:
            self._last_modified = datetime(2000, 1, 1)
            raise BadDateError(e) from None

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (self.last_modified, self.file_size) == (other.last_modified, other.file_size)

    def __lt__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (self.last_modified, self.file_size) < (other.last_modified, other.file_size)

    def __hash__(self) -> int:
        return hash((self.file_uri, self.last_modified, self.file_size))

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.base_path!r}, {self.file_uri!r}, '{self.last_modified}', {self.file_size})"

    def make_record(self) -> dict:
        return {
            'saved': self.save_date,
            'current_loc': self.base_path.as_posix(),
            'uri': self.file_uri,
            'modified': self.last_modified.strftime('%Y-%m-%d %H:%M:%S'),
            'size': self.file_size,
        }
