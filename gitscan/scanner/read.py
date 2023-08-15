"""Extract information from git repos."""
from pathlib import Path
from typing import Any
from git import Repo  # type: ignore
from git.exc import GitCommandError

DETACHED_BRANCH_DISPLAY_NAME = "DETACHED"
NO_BRANCH_DISPLAY_NAME = "-"


def extract_repo_name(path_to_git: str | Path) -> tuple[str, Path, Path]:
    """Get the repo name, without .git extension (if any).

    Also get the path of the repo directory and the
    directory that contains the repo directory.
    path_to_git is the directory which contains the HEAD file
    and is returned from a search.
    """
    gitpath = Path(path_to_git)
    if gitpath.stem == '.git':
        repo_name = gitpath.parent.stem
        containing_dir = gitpath.parents[1]
        repo_dir = gitpath.parent
    else:
        repo_name = gitpath.stem
        containing_dir = gitpath.parent
        repo_dir = gitpath
    return (repo_name, repo_dir, containing_dir)


def read_repo(path_to_git: str | Path) -> dict[str, Any]:
    """Extract basic information about the repo.

    see extract_repo_name() for path_to_git definition.
    """
    repo = Repo(path_to_git)
    info: dict[str, Any] = {}
    (info['name'], _, info['containing_dir']) = extract_repo_name(path_to_git)
    info['bare'] = repo.bare
    info['detached_head'] = repo.head.is_detached
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
        info['last_commit_datetime'] = None
    else:
        info['last_commit_datetime'] = repo.iter_commits(
                                        ).__next__().committed_datetime
        try:
            info['branch_name'] = repo.active_branch.name
        except TypeError:
            info['branch_name'] = NO_BRANCH_DISPLAY_NAME

    if repo.head.is_detached:
        info['branch_name'] = DETACHED_BRANCH_DISPLAY_NAME

    # Find the smallest number of commits ahead, and the number
    # of unique commits behind.
    remote_commits: set[str] = set()
    ahead_counts: list[int] = []
    info['fetch_failed'] = False
    if not repo.bare and info['branch_count']:
        for remote in repo.remotes:
            try:
                repo.git.fetch(remote.name)
                ahead_counts.append(sum(1 for _ in repo.iter_commits(
                            f"{remote.name}/{info['branch_name']}"
                            f"..{info['branch_name']}")))
                remote_commits.update(c.hexsha for c in repo.iter_commits(
                            f"{info['branch_name']}"
                            f"..{remote.name}/{info['branch_name']}"))
            except GitCommandError:
                info['fetch_failed'] = True

    info['behind_count'] = len(remote_commits)
    info['ahead_count'] = 0 if not ahead_counts else min(ahead_counts)
    info['up_to_date'] = ((info['behind_count'] == 0) and
                          (info['ahead_count'] == 0))
    return info