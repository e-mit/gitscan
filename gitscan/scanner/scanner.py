"""Extract information from git repos."""
from pathlib import Path
from typing import Any
from git import Repo  # type: ignore


DETACHED_BRANCH_DISPLAY_NAME = "DETACHED"
NO_BRANCH_DISPLAY_NAME = "-"


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


def read_repo(path_to_git: str | Path) -> dict[str, Any]:
    """Extract basic information about the repo.

    path_to_git is the path to the .git or X.git directory.
    """
    repo = Repo(path_to_git)
    info: dict[str, Any] = {}
    (info['name'], info['path']) = extract_repo_name(path_to_git)
    info['bare'] = repo.bare
    info['remote_count'] = len(repo.remotes)
    info['branch_count'] = len(repo.branches)  # type: ignore
    info['tag_count'] = len(repo.tags)
    info['index_changes'] = repo.is_dirty(index=True,
                                          working_tree=False,
                                          untracked_files=False,
                                          submodules=False)
    info['working_tree_changes'] = repo.is_dirty(index=False,
                                                 working_tree=True,
                                                 untracked_files=False,
                                                 submodules=False)
    if not repo.bare:
        info['untracked_count'] = len(repo.untracked_files)
        info['stash'] = len(repo.git.stash("list")) > 0
    else:
        info['untracked_count'] = 0
        info['stash'] = False

    if info['branch_count'] == 0:
        info['branch_name'] = NO_BRANCH_DISPLAY_NAME
        info['detached_head'] = False
        info['last_commit_datetime'] = None
    else:
        info['last_commit_datetime'
            ] = repo.iter_commits().__next__().committed_datetime
        try:
            info['branch_name'] = repo.active_branch.name
            info['detached_head'] = False
        except TypeError:
            info['detached_head'] = True
            info['branch_name'] = DETACHED_BRANCH_DISPLAY_NAME

    info['ahead_count'] = 0
    info['behind_count'] = 0
    failed_count = 0
    for remote in repo.remotes:
        try:
            remote.fetch()
        except Exception:
            # Failed fetch can have many causes
            failed_count += 1
        else:
            info['ahead_count'] += sum(1 for _ in
                repo.iter_commits(
                  f"{remote.name}/{info['branch_name']}..{info['branch_name']}"
                ))
            info['behind_count'] += sum(1 for _ in
                repo.iter_commits(
                  f"{info['branch_name']}..{remote.name}/{info['branch_name']}"
                ))
    info['up_to_date'] = ((info['behind_count'] == 0) and
                          (info['ahead_count'] == 0))
    return info
