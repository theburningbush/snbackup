from .backup import backup
from .utilities import Timer


def main():
    with Timer() as timer:
        backup()
    print(f'Exec time: {timer.elapsed:.2f}s')
