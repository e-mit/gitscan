"""Entry point to run as package."""
import argparse
import logging

from .gitscan import gitscan

DEFAULT_LOG_LEVEL = 'ERROR'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
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
