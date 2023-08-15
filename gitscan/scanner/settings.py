"""Manage the application preference and data files."""
import os
import sys
from pathlib import Path
from typing import Any
import json


APP_SETTINGS_DIRECTORY_NAME = "gitscan"
PREFERENCES_FILENAME = "preferences.json"
REPO_LIST_FILENAME = "repo_list.txt"


def get_settings_directory() -> Path:
    """Choose directory where program settings and data are stored.

    Directory is platform-dependent. Create it if it does not exist.
    """
    if sys.platform.startswith('win32'):
        settings_dir = (Path(os.environ['APPDATA'])
                        / APP_SETTINGS_DIRECTORY_NAME)
    elif sys.platform.startswith('linux'):
        if 'XDG_CONFIG_HOME' in os.environ:
            settings_dir = (Path(os.environ['XDG_CONFIG_HOME'])
                            / APP_SETTINGS_DIRECTORY_NAME)
        elif (Path(os.environ['HOME']) / '.config').exists():
            settings_dir = (Path(os.environ['HOME']) / '.config'
                            / APP_SETTINGS_DIRECTORY_NAME)
        else:
            settings_dir = (Path(os.environ['HOME'])
                            / ('.' + APP_SETTINGS_DIRECTORY_NAME))
    elif sys.platform.startswith('darwin'):
        # Apple macos
        settings_dir = (Path(os.environ['HOME']) / 'Library' /
                        'Application Support' / APP_SETTINGS_DIRECTORY_NAME)
    else:
        raise NotImplementedError(f"{sys.platform} OS not supported")

    if not settings_dir.parent.exists():
        raise NotADirectoryError(f"{settings_dir.parent} does not exist.")

    try:
        os.mkdir(settings_dir)
        # The directory was newly created
    except FileExistsError:
        pass
    return settings_dir


def load_settings(settings_dir: Path) -> tuple[None | dict[str, Any],
                                               None | list[Path]]:
    """Attempt to read the preferences file and repo list file.

    Return None if they do not exist or have bad format.
    """
    try:
        with open(settings_dir / PREFERENCES_FILENAME,
                  encoding="utf-8") as file:
            preferences = json.load(file)
        if not isinstance(preferences, dict):
            preferences = None
    except (json.JSONDecodeError, FileNotFoundError):
        preferences = None

    try:
        with open(settings_dir / REPO_LIST_FILENAME, encoding="utf-8") as file:
            list_path_to_git = [Path(x.rstrip()) for x in file]
    except FileNotFoundError:
        list_path_to_git = None

    return (preferences, list_path_to_git)


def save_preferences(settings_dir: Path, preferences: dict[str, Any]) -> None:
    """Save preferences as json file."""
    with open(settings_dir / PREFERENCES_FILENAME,
              'w', encoding="utf-8") as file:
        json.dump(preferences, file)


def save_repo_list(settings_dir: Path, list_path_to_git: list[Path]) -> None:
    """Save list of repo paths to text file."""
    with open(settings_dir / REPO_LIST_FILENAME,
              'w', encoding="utf-8") as file:
        for line in list_path_to_git:
            file.write(f"{line}\n")
