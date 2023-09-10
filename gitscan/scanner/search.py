"""Search for git repositories."""
import os
from pathlib import Path
from threading import Event
import logging

logger = logging.getLogger(__name__)


def find_git_repos(start_dir: str | Path,
                   exclude_dirs: list[Path] = [],
                   stop_event: Event | None = None) -> list[str]:
    """Search for repos in all directories inside start_dir.

    Can be stopped early with a threading event. Full paths listed
    in exclude_dirs (and all their descendants) are excluded.
    Git submodule directories are also excluded.
    """
    list_path_to_git = []
    for root, dirs, files in os.walk(start_dir):
        if (stop_event is not None) and stop_event.is_set():
            break
        root_path = Path(root)
        dirs[:] = [x for x in dirs if (root_path/x) not in exclude_dirs
                   and not ((x == "modules") and (root_path.stem == ".git"))]
        if "HEAD" in files and "refs" in dirs and "objects" in dirs:
            list_path_to_git.append(root)
    list_path_to_git.sort()
    return list_path_to_git
