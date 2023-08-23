"""Manage the application preference and data files."""
import os
import sys
from pathlib import Path
from typing import Any
import json
from enum import Enum, auto

APP_SETTINGS_DIRECTORY_NAME = "gitscan"
PREFERENCES_FILENAME = "preferences.json"
REPO_LIST_FILENAME = "repo_list.txt"


class Platform(Enum):
    """Supported OS/platforms."""
    LINUX = auto()
    WINDOWS = auto()


def get_platform() -> Platform:
    """Find the OS/platform, allowing either "linux" or "windows"."""
    if sys.platform.startswith('win32'):
        return Platform.WINDOWS
    elif sys.platform.startswith('linux'):
        return Platform.LINUX
    else:
        raise NotImplementedError(f"{sys.platform} not supported")


def get_settings_directory() -> Path:
    """Choose directory where program settings and data are stored.

    Directory is platform-dependent. Create it if it does not exist.
    """
    platform = get_platform()
    if platform == Platform.WINDOWS:
        settings_dir = (Path(os.environ['APPDATA'])
                        / APP_SETTINGS_DIRECTORY_NAME)
    else:  # if platform == Platform.LINUX:
        if 'XDG_CONFIG_HOME' in os.environ:
            settings_dir = (Path(os.environ['XDG_CONFIG_HOME'])
                            / APP_SETTINGS_DIRECTORY_NAME)
        elif (Path(os.environ['HOME']) / '.config').is_dir():
            settings_dir = (Path(os.environ['HOME']) / '.config'
                            / APP_SETTINGS_DIRECTORY_NAME)
        else:
            settings_dir = (Path(os.environ['HOME'])
                            / ('.' + APP_SETTINGS_DIRECTORY_NAME))

    if not settings_dir.parent.is_dir():
        raise NotADirectoryError(f"{settings_dir.parent} does not exist.")

    try:
        os.mkdir(settings_dir)
        # The directory was newly created
    except FileExistsError:
        pass
    return settings_dir


def load_settings(settings_dir: Path | str) -> tuple[None | dict[str, Any],
                                                     None | list[str]]:
    """Attempt to read the preferences file and repo list file.

    Return None if they do not exist or have bad format.
    """
    settings_dir = Path(settings_dir)
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
            list_path_to_git = [x.rstrip() for x in file]
    except FileNotFoundError:
        list_path_to_git = None

    return (preferences, list_path_to_git)


def save_preferences(settings_dir: Path | str,
                     preferences: dict[str, Any]) -> None:
    """Save preferences as json file."""
    with open(Path(settings_dir) / PREFERENCES_FILENAME,
              'w', encoding="utf-8") as file:
        json.dump(preferences, file)


def save_repo_list(settings_dir: Path | str,
                   list_path_to_git: list[str]) -> None:
    """Save list of repo paths to text file."""
    with open(Path(settings_dir) / REPO_LIST_FILENAME,
              'w', encoding="utf-8") as file:
        for line in list_path_to_git:
            file.write(f"{line}\n")


class AppSettings:
    """Store/save/load application settings."""

    _preferences_keys = ['ide_command', 'fetch_remotes',
                         'terminal_command', 'search_path']

    def __init__(self) -> None:
        """Read app settings from file, or create defaults if no file."""
        self.settings_directory = str(get_settings_directory())
        self._create_default_settings()
        (preferences,
         list_path_to_git) = load_settings(self.settings_directory)
        self.repo_list = [] if list_path_to_git is None else list_path_to_git
        self._validate_and_set(preferences)

    def _validate_and_set(self,
                          preferences: dict[str, str | bool] | None) -> bool:
        """Check for, and apply, the expected preferences."""
        if preferences is None:
            return False
        for k in self._preferences_keys:
            if k in preferences:
                self.__setattr__(k, preferences[k])
        return True

    def _save_preferences(self) -> None:
        """Save current app preferences to a platform-dependent location."""
        preferences = {}
        for k in self._preferences_keys:
            preferences[k] = self.__getattribute__(k)
        save_preferences(self.settings_directory, preferences)

    def _save_repo_list(self) -> None:
        """Save current repo list to a platform-dependent location."""
        save_repo_list(self.settings_directory, self.repo_list)

    def _create_default_settings(self) -> None:
        self.exclude_dirs: list[str] = []
        self.ide_command = "code"
        self.search_path = ""
        self.fetch_remotes = True
        if get_platform() == Platform.LINUX:
            self.terminal_command = "gnome-terminal"
            trash_path = Path(os.environ['HOME']) / '.local/share/Trash'
            if trash_path.is_dir():
                self.exclude_dirs = [str(trash_path)]
        else:  # Windows
            self.terminal_command = "cmd.exe"

    def set_search_path(self, search_path: str) -> None:
        """Change only the search path, and save preferences to file."""
        self.search_path = search_path
        self._save_preferences()

    def set(self, new_preferences: dict[str, str | bool]) -> None:
        """Check, then apply and save, new preferences."""
        if self._validate_and_set(new_preferences):
            self._save_preferences()

    def set_repo_list(self, repo_list: list[str]) -> None:
        """Change only the repo list, and save to file."""
        self.repo_list = repo_list
        self._save_repo_list()
