"""Worker classes to run tasks on QThreads."""
from typing import Union
from pathlib import Path
import threading
import multiprocessing
import multiprocessing.synchronize

from PyQt6.QtCore import pyqtSignal, QObject

from ..scanner import search, read

EVENT_TYPE = Union[threading.Event, multiprocessing.synchronize.Event]


class CancellableTaskWorker(QObject):
    """ABC for an object which runs a task on a QThread and can be stopped."""

    finished = pyqtSignal(list)
    stop_event: EVENT_TYPE

    def run(self) -> None:
        """Run the task and emit finished signal when done."""
        raise NotImplementedError

    def get_stop_event(self) -> EVENT_TYPE:
        """Provide the Event used to stop the task early."""
        return self.stop_event


class SearchWorker(CancellableTaskWorker):
    """Search for repos; will run on a QThread and can be stopped."""

    stop_event: threading.Event

    def __init__(self,
                 start_dir: str | Path,
                 exclude_dirs: list[Path] = []):
        self.start_dir = start_dir
        self.exclude_dirs = exclude_dirs
        self.stop_event = threading.Event()
        super().__init__()

    def run(self) -> None:
        """Run the task and emit finished signal when done."""
        list_path_to_git = search.find_git_repos(self.start_dir,
                                                 self.exclude_dirs,
                                                 self.stop_event)
        self.finished.emit(list_path_to_git)


class ReadWorker(CancellableTaskWorker):
    """Read repo data; will run on a QThread and can be stopped."""

    stop_event: multiprocessing.synchronize.Event

    def __init__(self,
                 repo_list: list[str],
                 fetch_remotes: bool):
        self.repo_list = repo_list
        self.fetch_remotes = fetch_remotes
        self.stop_event = multiprocessing.Event()
        super().__init__()

    def run(self) -> None:
        """Run the task and emit finished signal when done."""
        results = read.read_repo_parallel(self.repo_list,
                                          self.fetch_remotes,
                                          self.stop_event)
        self.finished.emit(results)
