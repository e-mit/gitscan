"""Extract information from git repos."""
from pathlib import Path


def extract_repo_name(path_to_git: str | Path) -> tuple[str, Path]:
    """Get the repo name, without extension (if any).

    Also get the containing directory path.
    """
    gitpath = Path(path_to_git)
    if gitpath.stem == '.git':
        repo_name = gitpath.parents[0].stem
        repo_path = gitpath.parents[1]
    else:
        repo_name = gitpath.stem
        repo_path = gitpath.parent
    return (repo_name, repo_path)
