import os
from pathlib import Path
import tempfile
import time
from git import Repo  # type: ignore


def create_temp_git_repo(repo_name: str, commit_count: int,
                         extra_branches: list[str],
                         tag_count: int, stash: bool,
                         active_branch: str,
                         untracked_count: int,
                         index_changes: bool,
                         working_tree_changes: bool) -> Path:
    """Create a git repo in a temporary directory"""
    temp_base_dir = Path(tempfile.mkdtemp())
    repo_dir = temp_base_dir / repo_name
    repo = Repo.init(repo_dir)
    repo.git.checkout(b='main')

    # Create and commit files in the repository
    for i in range(1, commit_count + 1):
        file_name = f'file{i}.txt'
        (repo_dir / file_name).touch()
        repo.index.add([file_name])
        repo.index.commit(f"Commit {i}: {file_name}")

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
        branch_file = f"branch{i}.txt"
        (repo_dir / branch_file).touch()
        repo.index.add([branch_file])
        repo.index.commit(f"Add {branch_file} on new branch")

    # switch to chosen branch
    repo.git.checkout(active_branch)
    file_name = active_branch + ".txt"
    file_path = repo_dir / file_name
    file_path.touch()
    repo.index.add([file_name])
    repo.index.commit("Final commit.")
    if working_tree_changes:
        with open(file_path, 'w') as file:
            file.write("Modified working tree.\n")

    for i in range(1, untracked_count + 1):
        file_name = f'untracked{i}.txt'
        (repo_dir / file_name).touch()

    if index_changes:
        file_name = "index_changed.txt"
        (repo_dir / file_name).touch()
        repo.index.add([file_name])

    repo.close()
    return temp_base_dir


def delete_temp_directory(temp_dir: Path) -> None:
    for root, dirs, files in os.walk(temp_dir, topdown=False):
        for file in files:
            os.remove(Path(root) / file)
        for dir in dirs:
            os.rmdir(Path(root) / dir)
    os.rmdir(temp_dir)


if __name__ == "__main__":
    print("Preparing manual test for create_temp_git_repo()")
    repo_name = "myrepo"
    repo_base_dir = create_temp_git_repo(repo_name, commit_count=5,
                                         extra_branches=['dev', 'foo'],
                                         tag_count=1, stash=True,
                                         active_branch='main',
                                         untracked_count=0,
                                         index_changes=False,
                                         working_tree_changes=False)
    print(f"Temporary Git repository {repo_name} created in {repo_base_dir}")
    time.sleep(6)
    delete_temp_directory(repo_base_dir)
    print("Temporary Git repository deleted.")
