import logging
from time import perf_counter


class Timer:
    """Context manager class to time code execution inside a with block"""

    def __init__(self):
        self.runs = []

    def __enter__(self):
        self.start = perf_counter()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.end = perf_counter()
        self.elapsed = self.end - self.start
        self.runs.append(self.elapsed)


class CustomLogger:
    """Used to setup a "standard" logger that allows for
    logging to file as well as to console if desired"""

    def __init__(self, level: str) -> None:
        self.level = level
        self.format = logging.Formatter(fmt='%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %H:%M:%S')
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.level)

    def to_console(self) -> None:
        """Allows logs to print to screen"""
        self.console = logging.StreamHandler()
        self.console.setFormatter(self.format)
        self.logger.addHandler(self.console)

    def to_file(self, fname: str) -> None:
        """Setup a log file to be used"""
        # This deals with __file__ being passed
        if fname.endswith('.py'):
            fname = fname.removesuffix('.py')

        self.file = logging.FileHandler(f'{fname}.log', encoding='utf-8')
        self.file.setFormatter(self.format)
        self.logger.addHandler(self.file)

    def get_logger(self) -> logging.Logger:
        return self.logger

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.level})'
