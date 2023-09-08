"""Entry point to run as package."""
import argparse
import logging

from gitscan import gitscan

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    default_level = 'ERROR'
    help_message = ("Choose stdout logging level."
                    f" Default: {default_level}."
                    " Valid values: "
                    + ", ".join(logging._nameToLevel.keys()))
    parser.add_argument('-log',
                        '--loglevel',
                        default=default_level,
                        help=help_message)
    log_level = parser.parse_args().loglevel.upper()
    gitscan.main(log_level)
