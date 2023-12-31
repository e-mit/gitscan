"""Extract information from git repositories."""
from pathlib import Path
from typing import Any, Sequence
import subprocess  # nosec
import time
import multiprocessing as mp
import multiprocessing.synchronize
from functools import partial
from enum import Flag, auto
import logging

import psutil
from git import Repo  # type: ignore

MP_EVENT = multiprocessing.synchronize.Event

DETACHED_BRANCH_DISPLAY_NAME = "DETACHED"
NO_BRANCH_DISPLAY_NAME = "-"
UNFETCHED_REMOTE_WARNING = "Remotes not fetched"
FETCH_FAILED_WARNING = "Fetch failed"
FETCH_TIMEOUT_WARNING = "Fetch timed-out"

logger = logging.getLogger(__name__)
_stop_event_global: MP_EVENT | None = None


class FetchStatus(Flag):
    """Represents the result of an attempt to fetch a single remote."""

    TIMEOUT = auto()
    ERROR = auto()
    CANCEL = auto()
    OK = auto()


def _init_pool_stop_event(evt: MP_EVENT | None) -> None:
    """Initialize the global event object which is read in read_repo()."""
    global _stop_event_global
    _stop_event_global = evt


def read_repo_parallel(paths_to_git: Sequence[Path | str],
                       fetch_remotes: bool = True,
                       stop_event: MP_EVENT | None = None,
                       pool_size: int | None = None,
                       poll_period_s: float = 0.005,
                       timeout_A_s: float = 10.0,
                       timeout_B_s: float = 1.5
                       ) -> list[None | dict[str, Any]]:
    """Run multiple repo readers from a process pool.

    pool_size=None uses cpu_count.
    """
    pfunc = partial(read_repo, fetch_remotes=fetch_remotes,
                    poll_period_s=poll_period_s,
                    timeout_A_s=timeout_A_s,
                    timeout_B_s=timeout_B_s)
    with mp.Pool(processes=pool_size, initializer=_init_pool_stop_event,
                 initargs=(stop_event,)) as p:
        results = p.map(pfunc, paths_to_git)
    return results


def git_fetch_with_timeout(git_directory: Path | str,
                           remote_name: str | None = None,
                           stop_event: MP_EVENT | None = None,
                           poll_period_s: float = 0.005,
                           timeout_A_s: float = 10.0,
                           timeout_B_s: float = 1.5
                           ) -> FetchStatus:
    """Run git fetch in a subprocess and kill it if necessary.

    Returns a string description of the problem, or None if success.
    """
    args = (['git', 'fetch'] if remote_name is None
            else ['git', 'fetch', remote_name])
    proc = subprocess.Popen(args,  # nosec
                            bufsize=0, close_fds=True,
                            cwd=git_directory,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            text=False)
    the_process = psutil.Process(proc.pid)
    pid_str = str(proc.pid)
    logger.debug("Proc %s : Fetch %s/%s", pid_str, git_directory, remote_name)
    startA = time.time()
    startB = time.time()
    timeout = False
    three_processes = False
    stop = False
    while proc.poll() is None:
        processes = the_process.children(recursive=True)
        processes.append(the_process)
        logger.debug("Proc %s : %s", pid_str, [x.status() for x in processes])
        if not three_processes and (len(processes) >= 3):
            # This is usually a sign that the fetch is proceeding successfully
            logger.debug("Proc %s : 3 or more processes", pid_str)
            three_processes = True
            timeout_B_s = timeout_B_s * 2
            timeout_A_s = timeout_A_s * 2
        if any([x.status() in [psutil.STATUS_IDLE, psutil.STATUS_RUNNING]
                for x in processes]):
            logger.debug("Proc %s : Resetting B period", pid_str)
            startB = time.time()
        if (time.time() - startB) > timeout_B_s:
            timeout = True
            logger.debug("Proc %s : TIMEOUT B (non-running timeout)", pid_str)
            break
        if (time.time() - startA) > timeout_A_s:
            timeout = True
            logger.debug("Proc %s : TIMEOUT A (overall timeout)", pid_str)
            break
        if (stop_event is not None) and stop_event.is_set():
            logger.debug("Proc %s : BREAK due to stop_event", pid_str)
            stop = True
            break
        time.sleep(poll_period_s)
    logger.debug("Proc %s : Exit poll loop", pid_str)

    if timeout or stop:
        processes = the_process.children(recursive=True)
        processes.append(the_process)
        for p in processes:
            p.kill()
        # Wait for the process to end: this is
        # needed to avoid a ResourceWarning
        proc.wait(timeout_A_s)
        if stop:
            return FetchStatus.CANCEL
        else:
            return FetchStatus.TIMEOUT
    else:
        if proc.returncode != 0:
            logger.debug("Proc %s : Fetch function error returncode: %s",
                         pid_str, proc.returncode)
            return FetchStatus.ERROR
        logger.debug("Proc %s : Fetch function exit OK", pid_str)
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
              poll_period_s: float = 0.005,
              timeout_A_s: float = 10.0,
              timeout_B_s: float = 1.5
              ) -> None | dict[str, Any]:
    """Extract basic information about the repo.

    see extract_repo_name() for path_to_git definition.
    """
    if (_stop_event_global is not None) and _stop_event_global.is_set():
        return None
    try:
        repo = Repo(path_to_git)
        info: dict[str, Any] = {}
        (info['name'], info['repo_dir'],
            info['containing_dir']) = extract_repo_name(path_to_git)
        info['bare'] = repo.bare
        info['detached_head'] = repo.head.is_detached
        info['remote_count'] = len(repo.remotes)
        info['remote_names'] = [x.name for x in repo.remotes]
        info['branch_count'] = len(repo.branches)  # type: ignore
        info['branch_names'] = [x.name for x in repo.branches]  # type: ignore
        info['tag_count'] = len(repo.tags)
        info['submodule_names'] = [x.name for x in repo.submodules]
        info['index_changes'] = repo.is_dirty(index=True,
                                              working_tree=False,
                                              untracked_files=False,
                                              submodules=True)
        info['working_tree_changes'] = repo.is_dirty(index=False,
                                                     working_tree=True,
                                                     untracked_files=False,
                                                     submodules=True)

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
        for branch in repo.branches:  # type: ignore
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
                    if (_stop_event_global is not None
                            and _stop_event_global.is_set()):
                        return None
                    start = time.time()
                    status = git_fetch_with_timeout(
                        info['repo_dir'],
                        remote.name,
                        _stop_event_global,
                        poll_period_s,
                        timeout_A_s,
                        timeout_B_s)
                    elapsed = time.time() - start
                    if (status == FetchStatus.ERROR
                       or status == FetchStatus.TIMEOUT):
                        log_func = logger.warning
                    else:
                        log_func = logger.info
                    log_func("%s|%s : fetch %s %.2f",
                             info['repo_dir'],
                             remote.name,
                             status.name.lower(), elapsed)  # type: ignore
                    if info['fetch_status'] is None:
                        info['fetch_status'] = status
                    else:
                        info['fetch_status'] |= status

            for branch in repo.branches:  # type: ignore
                if (branch.tracking_branch() is not None
                        and branch.tracking_branch()  # type: ignore
                        in repo.refs):
                    info['ahead_count'] += sum(1 for _ in repo.iter_commits(
                        f"{branch.tracking_branch()}..{branch}"))
                    info['behind_count'] += sum(1 for _ in repo.iter_commits(
                        f"{branch}..{branch.tracking_branch()}"))

        info['up_to_date'] = ((info['behind_count'] == 0)
                              and (info['ahead_count'] == 0))
        info['warning'] = None
        if (not fetch_remotes and info['remote_count'] > 0):
            info['warning'] = UNFETCHED_REMOTE_WARNING
        elif info['fetch_status'] is None:
            pass
        elif FetchStatus.ERROR in info['fetch_status']:
            info['warning'] = FETCH_FAILED_WARNING
        elif FetchStatus.TIMEOUT in info['fetch_status']:
            info['warning'] = FETCH_TIMEOUT_WARNING
        repo.close()
    except Exception:
        # Not unexpected, so do not log on high priority level:
        logger.info("Routine exception with %s", path_to_git, exc_info=True)
        return None
    return info


def read_commits(path_to_git: str | Path,
                 commit_count: int) -> list[dict[str, str]] | None:
    """Get the most recent commit information from the repo active branch.

    Return up to 'commit_count' commits, or fewer if not available.
    """
    try:
        repo = Repo(path_to_git)
    except Exception:
        return None
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
