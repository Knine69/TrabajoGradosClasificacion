from enum import Enum


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
        message_color: str = OutputColors.WHITE.value) -> None:
    print(f"{message_color}{message}{OutputColors.WHITE.value}")
