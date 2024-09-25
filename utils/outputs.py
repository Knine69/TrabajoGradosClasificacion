from enum import Enum
import os
import datetime


class OutputColors(Enum):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    WHITE = '\33[0m'


def print_console_message(
        message: str,
        app: str,
        message_color: str = OutputColors.WHITE.value,
        ) -> None:
    print(f"{message_color}{message}{OutputColors.WHITE.value}")
    path = f"logs/{app}"
    if os.path.exists(path):
        _write_to_log(path, message)
    else:
        os.mkdir(
            os.path.join(os.path.dirname('TrabajoGradosClasificacion'), path))
        _write_to_log(path, message)


def _write_to_log(path: str, message: str):
    with open(f"{path}/{datetime.date.today()}_logs.txt", 'a') as logs:
        logs.write(f"[{datetime.datetime.now()}] - {message}\n")


def print_header_message(message: str, app: str):
    print_console_message(
        message=message,
        message_color=OutputColors.HEADER.value,
        app=app
    )


def print_bold_message(message: str, app: str):
    print_console_message(
        message=message,
        message_color=OutputColors.BOLD.value,
        app=app
    )


def print_error(message: str, app) -> None:
    print_console_message(
        message=message,
        message_color=OutputColors.FAIL.value,
        app=app
    )


def print_successful_message(message, app):
    print_console_message(
        message=message,
        message_color=OutputColors.OKGREEN.value,
        app=app
    )


def print_warning_message(message, app):
    print_console_message(
        message=message,
        message_color=OutputColors.WARNING.value,
        app=app
    )
