"""Extract information from git repos."""
from pathlib import Path
from typing import Any, Sequence
import subprocess
import time
import os
import multiprocessing as mp
from functools import partial
from enum import Flag, auto

import psutil
from git import Repo  # type: ignore

DETACHED_BRANCH_DISPLAY_NAME = "DETACHED"
NO_BRANCH_DISPLAY_NAME = "-"


class FetchStatus(Flag):
    """Represents the result of an attempt to fetch a single remote."""
    TIMEOUT = auto()
    ERROR = auto()
    OK = auto()


def read_repo_parallel(paths_to_git: Sequence[Path | str],
                       fetch_remotes: bool = True,
                       thread_pool_size: int | None = None,
                       poll_period_s: float = 0.2,
                       timeout_A_count: int = 50,
                       timeout_B_count: int = 5
                       ) -> list[None | dict[str, Any]]:
    """Run multiple repo readers from a thread pool.

    thread_pool_size=None uses cpu_count.
    """
    pfunc = partial(read_repo, fetch_remotes=fetch_remotes,
                    poll_period_s=poll_period_s,
                    timeout_A_count=timeout_A_count,
                    timeout_B_count=timeout_B_count)
    with mp.Pool(processes=thread_pool_size) as p:
        results = p.map(pfunc, paths_to_git)
    return results


def git_fetch_with_timeout(git_directory: Path | str,
                           remote_name: str | None = None,
                           poll_period_s: float = 0.2,
                           timeout_A_count: int = 50,
                           timeout_B_count: int = 5
                           ) -> FetchStatus:
    """Run git fetch in a subprocess and kill it if necessary.

    Returns a string description of the problem, or None if success.
    """
    parent = psutil.Process(os.getpid())
    args = (['git', 'fetch'] if remote_name is None
            else ['git', 'fetch', remote_name])
    process = subprocess.Popen(args,
                               shell=False, bufsize=0, close_fds=True,
                               cwd=git_directory,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL,
                               text=False)
    count_A = 0
    count_B = 0
    timeout = False
    while process.poll() is None:
        children = parent.children(recursive=True)
        if any([child.status() != 'sleeping' for child in children]):
            count_B = 0
        else:
            count_B += 1
        count_A += 1
        if count_A >= timeout_A_count or count_B >= timeout_B_count:
            timeout = True
            break
        time.sleep(poll_period_s)

    if timeout:
        children = parent.children(recursive=True)
        for child in children:
            child.kill()
        # Wait for the process to end: this is
        # needed to avoid a ResourceWarning
        process.wait(timeout_A_count*poll_period_s)
        return FetchStatus.TIMEOUT
    else:
        if process.returncode != 0:
            return FetchStatus.ERROR
        return FetchStatus.OK


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


def read_repo(path_to_git: str | Path,
              fetch_remotes: bool = True,
              poll_period_s: float = 0.2,
              timeout_A_count: int = 50,
              timeout_B_count: int = 5
              ) -> None | dict[str, Any]:
    """Extract basic information about the repo.

    see extract_repo_name() for path_to_git definition.
    """
    try:
        repo = Repo(path_to_git)
    except Exception:
        return None
    info: dict[str, Any] = {}
    (info['name'], info['repo_dir'],
     info['containing_dir']) = extract_repo_name(path_to_git)
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

    try:
        info['commit_count'] = sum(1 for _ in repo.iter_commits())
    except ValueError:
        # occurs with no commits
        info['commit_count'] = 0

    if not repo.bare:
        info['untracked_count'] = len(repo.untracked_files)
        info['stash'] = len(repo.git.stash("list")) > 0
    else:
        info['untracked_count'] = 0
        info['stash'] = False

    last_commits = []
    for branch in repo.branches:
        last_commits.append(
            repo.iter_commits(branch).__next__().committed_datetime)
    info['last_commit_datetime'] = (None if not last_commits
                                    else max(last_commits))

    if info['branch_count'] == 0:
        info['branch_name'] = NO_BRANCH_DISPLAY_NAME
    else:
        try:
            info['branch_name'] = repo.active_branch.name
        except TypeError:
            info['branch_name'] = NO_BRANCH_DISPLAY_NAME

    if repo.head.is_detached:
        info['branch_name'] = DETACHED_BRANCH_DISPLAY_NAME

    # Find ahead/behind counts summed over all local branches which
    # track remotes
    info['behind_count'] = 0
    info['ahead_count'] = 0
    info['fetch_status'] = None
    if not repo.bare and info['branch_count']:
        if fetch_remotes:
            for remote in repo.remotes:
                status = git_fetch_with_timeout(
                                            info['repo_dir'],
                                            remote.name,
                                            poll_period_s,
                                            timeout_A_count,
                                            timeout_B_count)
                if info['fetch_status'] is None:
                    info['fetch_status'] = status
                else:
                    info['fetch_status'] |= status

        for branch in repo.branches:
            if (branch.tracking_branch() is not None
                    and branch.tracking_branch() in repo.refs):
                info['ahead_count'] += sum(1 for _ in repo.iter_commits(
                            f"{branch.tracking_branch()}..{branch}"))
                info['behind_count'] += sum(1 for _ in repo.iter_commits(
                            f"{branch}..{branch.tracking_branch()}"))

    info['up_to_date'] = ((info['behind_count'] == 0) and
                          (info['ahead_count'] == 0))
    repo.close()
    return info


def read_commits(path_to_git: str | Path,
                 commit_count: int) -> list[dict[str, str]]:
    """Get the most recent commit information from the repo active branch.

    Return up to 'commit_count' commits, or fewer if not available.
    """
    repo = Repo(path_to_git)
    commits: list[dict[str, str]] = []
    try:
        iter_commits = repo.iter_commits()
    except ValueError:
        # occurs with no commits
        pass
    else:
        for i, commit in enumerate(iter_commits):
            if (i == commit_count):
                break
            commit_data = {}
            commit_data['hash'] = str(commit)
            commit_data['author'] = str(commit.committer)
            commit_data['date'] = str(commit.committed_datetime)
            commit_data['summary'] = str(commit.summary)
            commits.append(commit_data)
    repo.close()
    return commits
