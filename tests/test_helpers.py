from pathlib import Path
import tempfile
import uuid
from git import Repo  # type: ignore
from random import random
from random import randrange

TEST_POLL_PERIOD_S = 0.1
TEST_TIMEOUT_A_S = 20.0
TEST_TIMEOUT_B_S = 3


def make_path_to_git(containing_dir: Path | str, repo_name: str,
                     bare: bool) -> tuple[Path, Path]:
    """path_to_git is the directory which contains the HEAD file."""
    if bare:
        path_to_git = Path(containing_dir) / (repo_name + ".git")
        repo_dir = Path(path_to_git)
    else:
        path_to_git = Path(containing_dir) / repo_name / ".git"
        repo_dir = Path(containing_dir) / repo_name
    return (path_to_git, repo_dir)


def create_temp_git_repo(repo_name: str, commit_count: int,
                         extra_branches: list[str],
                         tag_count: int, stash: bool,
                         active_branch: str,
                         untracked_count: int,
                         index_changes: bool,
                         working_tree_changes: bool,
                         detached_head: bool) -> tuple[Path, Path, Path]:
    """Create a git repo in a temporary directory"""
    containing_dir = Path(tempfile.mkdtemp())
    (repo_dir, path_to_git) = create_git_repo(containing_dir,
                                              repo_name, commit_count,
                                              extra_branches,
                                              tag_count, stash,
                                              active_branch,
                                              untracked_count,
                                              index_changes,
                                              working_tree_changes,
                                              detached_head)
    return (containing_dir, repo_dir, path_to_git)


def create_git_repo(containing_dir: Path,
                    repo_name: str, commit_count: int,
                    extra_branches: list[str],
                    tag_count: int, stash: bool,
                    active_branch: str,
                    untracked_count: int,
                    index_changes: bool,
                    working_tree_changes: bool,
                    detached_head: bool) -> tuple[Path, Path]:
    """Create a git repo in a specified directory"""
    (path_to_git, repo_dir) = make_path_to_git(containing_dir, repo_name,
                                               bare=False)
    repo = Repo.init(repo_dir)
    repo.git.checkout(b='main')

    if commit_count > 0:
        file_path = repo_dir / "main.txt"
        file_path.touch()
        repo.index.add([file_path])
        repo.index.commit("Initial commit.")

        for i in range(tag_count):
            repo.create_tag(f'v{i + 1}.0', message=f"Version {i + 1}.0")

        if stash:
            stash_file = "stash_file.txt"
            (repo_dir / stash_file).touch()
            repo.index.add([stash_file])
            repo.git.stash('save', 'Stash example')

        # Create the specified extra branches
        for i, branch_name in enumerate(extra_branches):
            repo.git.checkout(b=branch_name)
            branch_file = f"{branch_name}.txt"
            (repo_dir / branch_file).touch()
            repo.index.add([branch_file])
            repo.index.commit(f"New branch '{branch_name}'.")

        # switch to chosen branch and make more commits:
        repo.git.checkout(active_branch)
        do_commits(repo, repo_dir, commit_count - 1)

        if working_tree_changes:
            with open(repo_dir / (f"{active_branch}.txt"), 'w') as file:
                file.write("Modified working tree.\n")

        if detached_head:
            repo.git.checkout(f"HEAD~{commit_count - 1}")

    for i in range(untracked_count):
        (repo_dir / f'untracked{i}.txt').touch()

    if index_changes:
        file_name = "index_changed.txt"
        (repo_dir / file_name).touch()
        repo.index.add([file_name])

    repo.close()
    return (repo_dir, path_to_git)


def create_temp_clone_git_repo(origin_repo_dir: str | Path,
                               new_repo_name: str,
                               bare: bool) -> tuple[Path, Path, Path]:
    """Create a new clone of a git repo, in a new temporary directory.

    If bare, the git files are placed directly in repo_dir.
    If not bare, a .git directory is made in repo_dir."""
    containing_dir = Path(tempfile.mkdtemp())
    repo = Repo(origin_repo_dir)
    (new_path_to_git, repo_dir) = make_path_to_git(containing_dir,
                                                   new_repo_name, bare)
    if bare:
        repo.clone(repo_dir, multi_options=['--bare'])
    else:
        repo.clone(repo_dir)
    repo.close()
    return (containing_dir, repo_dir, new_path_to_git)


def add_remote(path_to_current_repo: str | Path,
               new_remote_name: str,
               remote_url: str | Path) -> None:
    repo = Repo(path_to_current_repo)
    repo.git.remote("add", new_remote_name, remote_url)
    repo.close()


def create_remote_tracking_branches(path_to_current_repo: str | Path,
                                    new_remote_name: str,
                                    remote_url: str | Path) -> list[str]:
    """Add a new remote and track its branch(es) locally.

    Add the new remote and, for each of its branches, make a
    tracking branch locally.
    """
    repo = Repo(path_to_current_repo)
    refs_set_before = set(repo.refs)
    repo.git.remote("add", new_remote_name, remote_url)
    repo.git.fetch(new_remote_name)
    new_refs = set(repo.refs) - refs_set_before
    branch_names = []
    for ref in new_refs:
        new_branch_name = new_remote_name + "_" + Path(str(ref)).stem
        repo.git.branch(new_branch_name, str(ref))
        branch_names.append(new_branch_name)
    repo.close()
    return branch_names


def do_commits_on_branches(repo_dir: str | Path, branch_names: list[str],
                           commit_counts: list[int]) -> None:
    """Do a number of commits on each branch."""
    if (len(branch_names) != len(commit_counts)):
        raise ValueError("Inconsistent list lengths.")
    repo = Repo(repo_dir)
    for i in range(len(branch_names)):
        repo.git.checkout(branch_names[i])
        do_commits(repo, Path(repo_dir), commit_counts[i])
    repo.close()


def create_local_branches(path_to_current_repo: str | Path,
                          new_branch_count) -> None:
    """Add new branches which do not track remotes."""
    repo = Repo(path_to_current_repo)
    for i in range(new_branch_count):
        repo.git.branch(f"local{i}")
    repo.close()


def create_commits(repo_dir: Path, commit_count: int) -> None:
    repo = Repo(repo_dir)
    do_commits(repo, repo_dir, commit_count)
    repo.close()


def do_commits(repo: Repo, repo_dir: Path, commit_count: int) -> None:
    """Create and commit files."""
    for i in range(commit_count):
        file_name = str(uuid.uuid4())
        (repo_dir / file_name).touch()
        repo.index.add([file_name])
        repo.index.commit(f"""Commit {i}: {file_name}.

                          This is a multiline string.""")


def create_random_repo(containing_dir: Path) -> Path:
    repo_name = str(uuid.uuid4())
    commit_count = randrange(3)  # nosec
    extra_branches: list[str] = []
    tag_count = randrange(3)  # nosec
    stash = random() < 0.5  # nosec
    active_branch = 'main'
    untracked_count = randrange(3)  # nosec
    index_changes = random() < 0.5  # nosec
    working_tree_changes = random() < 0.5  # nosec
    detached_head = random() < 0.5  # nosec
    (_, path_to_git) = create_git_repo(
        containing_dir,
        repo_name,
        commit_count,
        extra_branches,
        tag_count, stash,
        active_branch,
        untracked_count,
        index_changes,
        working_tree_changes,
        detached_head)
    return path_to_git
