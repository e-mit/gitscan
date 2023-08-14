from pathlib import Path
import tempfile
import uuid
from git import Repo  # type: ignore


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
            repo.git.checkout("HEAD~0")

    for i in range(untracked_count):
        (repo_dir / f'untracked{i}.txt').touch()

    if index_changes:
        file_name = "index_changed.txt"
        (repo_dir / file_name).touch()
        repo.index.add([file_name])

    repo.close()
    return (containing_dir, repo_dir, path_to_git)


def create_temp_clone_git_repo(origin_repo_dir: str | Path,
                               new_repo_name: str,
                               bare: bool) -> tuple[Path, Path, Path]:
    """Create a new clone of a git repo, in a new temporary directory.

    If bare, the git files are placed directly in origin_repo_dir.
    If not bare, a .git directory is made in origin_repo_dir."""
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
        repo.index.commit(f"Commit {i}: {file_name}")
