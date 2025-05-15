from pathlib import Path
from hashlib import sha256
from datetime import datetime, date
from functools import total_ordering


class BytesEmptyError(Exception):
    """Bytes object empty"""


class BadDateError(Exception):
    """Bad datetime format or value"""


@total_ordering
class SnFile:
    """Represent an individual Supernote file"""

    def __init__(
        self, save_to: Path,
        today: date,
        uri: str,
        modified: str,
        size: int,
        saved: str | None = None,
        current_loc: str | None = None,
        prev_hash: str | None = None
    ) -> None:
        self.save_to = save_to
        self.today = today
        self.file_uri = uri
        self.last_modified = modified
        self.size = size
        self.saved = saved
        self.current_loc = current_loc
        self.prev_hash = prev_hash
        self._file_bytes = b''

    @property
    def save_date(self) -> str:
        return self.base_path.name

    @property
    def full_path(self) -> Path:
        return self.base_path.joinpath(self.uri)

    @property
    def file_bytes(self) -> bytes:
        return self._file_bytes

    @file_bytes.setter
    def file_bytes(self, bytes_obj: bytes) -> None:
        if not isinstance(bytes_obj, bytes):
            raise TypeError('File must be bytes object')
        self._file_bytes = bytes_obj
        self._file_hash = self._calc_hash()

    @file_bytes.deleter
    def file_bytes(self) -> None:
        self._file_bytes = b''

    @property
    def file_hash(self) -> str:
        return self._file_hash

    @property
    def modified(self) -> datetime:
        return self._modified

    @modified.setter
    def modified(self, mod_date: str) -> None:
        try:
            self._modified = datetime.fromisoformat(mod_date)
        except (ValueError, TypeError) as e:
            self._modified = datetime(2000, 1, 1)
            raise BadDateError(e) from None

    def _calc_hash(self) -> str:
        if self.file_bytes == b'':
            return ''
        return sha256(self._file_bytes).hexdigest()
    
    def _make_dir(self) -> None:
        self.full_path.parent.mkdir(exist_ok=True, parents=True)

    def save_file(self) -> None:
        self._make_dir()
        with open(self.full_path, 'wb') as file_output:
            file_output.write(self.file_bytes)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (self.modified, self.size) == (other.modified, other.size)

    def __lt__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (self.modified, self.size) < (other.modified, other.size)

    def __hash__(self) -> int:
        return hash((self.uri, self.modified, self.size))

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.base_path!r}, {self.uri!r}, '{self.modified}', {self.size})"

    def make_record(self) -> dict:
        return {
            'saved': self.save_date,
            'current_loc': self.base_path.as_posix(),
            'uri': self.uri,
            'modified': self.modified.strftime('%Y-%m-%d %H:%M:%S'),
            'size': self.size,
            'prev_hash': self.file_hash,
        }
