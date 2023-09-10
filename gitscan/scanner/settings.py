"""Manage the application preference and data files."""
import os
import sys
from pathlib import Path
from typing import Any
import json
from enum import Enum, auto
import logging

APP_SETTINGS_DIRECTORY_NAME = "gitscan"
PREFERENCES_FILENAME = "preferences.json"
REPO_LIST_FILENAME = "repo_list.txt"

logger = logging.getLogger(__name__)


class Platform(Enum):
    """Supported OS/platforms."""

    LINUX = auto()
    WINDOWS = auto()


def get_platform() -> Platform:
    """Find the OS/platform, allowing either "linux" or "windows"."""
    if sys.platform.startswith('win32'):
        raise NotImplementedError("Windows implementation is incomplete.")
    elif sys.platform.startswith('linux'):
        return Platform.LINUX
    else:
        raise NotImplementedError(f"Platform '{sys.platform}' is "
                                  "not supported")


def get_settings_directory() -> Path:
    """Choose directory where program settings and data are stored.

    Directory is platform-dependent. Create it if it does not exist.
    """
    if get_platform() == Platform.WINDOWS:
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
            logger.debug("Preferences file had bad contents.")
            preferences = None
    except (json.JSONDecodeError, FileNotFoundError):
        logger.debug("Preferences file could not be loaded.")
        preferences = None

    try:
        with open(settings_dir / REPO_LIST_FILENAME, encoding="utf-8") as file:
            list_path_to_git = [x.rstrip() for x in file]
    except FileNotFoundError:
        logger.debug("Repo list file did not exist.")
        list_path_to_git = None

    return (preferences, list_path_to_git)


def save_preferences(settings_dir: Path | str,
                     preferences: dict[str, Any]) -> None:
    """Save preferences as json file."""
    logger.debug("Saving preferences file.")
    with open(Path(settings_dir) / PREFERENCES_FILENAME,
              'w', encoding="utf-8") as file:
        json.dump(preferences, file)
        file.flush()
        os.fsync(file.fileno())


def save_repo_list(settings_dir: Path | str,
                   list_path_to_git: list[str]) -> None:
    """Save list of repo paths to text file."""
    logger.debug("Saving repo list file.")
    with open(Path(settings_dir) / REPO_LIST_FILENAME,
              'w', encoding="utf-8") as file:
        for line in list_path_to_git:
            file.write(f"{line}\n")
        file.flush()
        os.fsync(file.fileno())


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
        self.first_run = preferences is None and list_path_to_git is None
        self._validate_and_set_paths(list_path_to_git)
        self._validate_and_set_preferences(preferences)

    def _validate_and_set_paths(self,
                                list_path_to_git: list[str] | None) -> None:
        if list_path_to_git is None:
            self.repo_list = []
            return
        self.repo_list = [p for p in list_path_to_git if Path(p).is_dir()]
        if len(self.repo_list) != len(list_path_to_git):
            self._save_repo_list()

    def _validate_and_set_preferences(self,
                                      preferences: dict[str, str | bool] | None
                                      ) -> bool:
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
        self.exclude_dirs: list[Path] = []
        self.ide_command = "code"  # MSVSC
        self.fetch_remotes = True
        if get_platform() == Platform.LINUX:
            self.search_path = os.environ['HOME']
            self.terminal_command = "gnome-terminal"
            trash_path = Path(os.environ['HOME']) / '.local/share/Trash'
            if trash_path.is_dir():
                self.exclude_dirs = [trash_path]
        else:  # Windows
            self.search_path = os.environ['USERPROFILE']
            self.terminal_command = "start cmd.exe"

    def set_search_path(self, search_path: str) -> None:
        """Change only the search path, and save preferences to file."""
        self.search_path = search_path
        self._save_preferences()

    def set_preferences(self, new_preferences: dict[str, str | bool]) -> None:
        """Check, then apply and save, new preferences."""
        if self._validate_and_set_preferences(new_preferences):
            self._save_preferences()

    def set_repo_list(self, repo_list: list[str]) -> None:
        """Change only the repo list, and save to file."""
        self.repo_list = repo_list
        self._save_repo_list()
