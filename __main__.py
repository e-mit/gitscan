"""Entry point to run as package."""
import argparse

from gitscan import gitscan

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    help_message = ("""Choose stdout logging level.
                       Valid values: """
                    + ", ".join(gitscan.VALID_LOG_LEVELS))
    parser.add_argument('-log',
                        '--loglevel',
                        default='ERROR',
                        help=help_message)
    log_level = parser.parse_args().loglevel.upper()
    gitscan.main(log_level)
