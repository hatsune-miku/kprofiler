import sys


def is_macos() -> bool:
    return sys.platform == "darwin"
