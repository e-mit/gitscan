"""Entry point to run as package."""
import argparse
import logging

from .gitscan import gitscan

DEFAULT_LOG_LEVEL = 'ERROR'

__name__ = "hello"

parser = argparse.ArgumentParser(prog="python -m " + gitscan.APP_TITLE.lower())
help_message = ("Choose stdout logging level."
                f" Default: {DEFAULT_LOG_LEVEL}."
                " Valid values: "
                + ", ".join(logging._nameToLevel.keys()))
parser.add_argument('-log',
                    '--loglevel',
                    default=DEFAULT_LOG_LEVEL,
                    help=help_message)
log_level = parser.parse_args().loglevel.upper()
gitscan.main(log_level)
