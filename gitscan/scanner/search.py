"""Search for git repositories."""
import os
from pathlib import Path


def find_git_repos(start_dir: str | Path,
                   exclude_dirs: list[Path] = []) -> list[str]:
    """Search for repos in all directories inside start_dir."""
    list_path_to_git = []
    for root, dirs, files in os.walk(start_dir):
        dirs[:] = [x for x in dirs if (Path(root)/x) not in exclude_dirs]
        if "HEAD" in files and "refs" in dirs and "objects" in dirs:
            list_path_to_git.append(root)
    list_path_to_git.sort()
    return list_path_to_git
