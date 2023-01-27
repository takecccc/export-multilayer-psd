import inspect
import substance_painter.logging
import pathlib

def _log(severity, channel, message):
    if type(message) is not str:
        message = f"{type(message).__name__}:{str(message)}"
    substance_painter.logging.log(severity=severity, channel=channel, message=message)

def log_info(message):
    filename = inspect.stack()[1].filename
    filename = pathlib.Path(filename).name
    _log(substance_painter.logging.INFO, f"Python:{filename}", message)

def log_warn(message):
    filename = inspect.stack()[1].filename
    filename = pathlib.Path(filename).name
    _log(substance_painter.logging.WARNING, f"Python:{filename}", message)

def log_error(message):
    filename = inspect.stack()[1].filename
    filename = pathlib.Path(filename).name
    _log(substance_painter.logging.ERROR, f"Python:{filename}", message)