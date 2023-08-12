import os
from pathlib import Path
import tempfile
import time
from git import Repo  # type: ignore


def create_temp_git_repo(repo_name: str, commit_count: int,
                         extra_branches: list[str],
                         tag_count: int, stash: bool,
                         active_branch: str) -> Path:
    """Create a git repo in a temporary directory"""
    temp_base_dir = Path(tempfile.mkdtemp())
    repo_dir = temp_base_dir / repo_name
    repo = Repo.init(repo_dir)
    repo.git.checkout(b='main')

    # Create and commit text files in the repository
    for i in range(1, commit_count + 1):
        file_name = f'file{i}.txt'
        file_path = repo_dir / file_name
        with open(file_path, 'w') as file:
            file.write(f"This is {file_name}\n")
        repo.index.add([file_name])
        repo.index.commit(f"Commit {i}")

    for i in range(tag_count):
        repo.create_tag(f'v{i + 1}.0', message=f"Version {i + 1}.0")

    if stash:
        stash_file = "stash_file.txt"
        stash_file_path = repo_dir / stash_file
        with open(stash_file_path, 'w') as file:
            file.write("hello")
        repo.index.add([stash_file])
        repo.git.stash('save', 'Stash example')

    for i, branch_name in enumerate(extra_branches):
        repo.git.checkout(b=branch_name)
        branch_file = f"branch{i}.txt"
        branch_file_path = repo_dir / branch_file
        with open(branch_file_path, 'w') as file:
            file.write("A new branch.")
        repo.index.add([branch_file])
        repo.index.commit(f"Add {branch_file} on new branch")

    # switch to chosen branch and close
    repo.git.checkout(active_branch)
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
                                         active_branch='main')
    print(f"Temporary Git repository {repo_name} created in {repo_base_dir}")
    time.sleep(6)
    delete_temp_directory(repo_base_dir)
    print("Temporary Git repository deleted.")
