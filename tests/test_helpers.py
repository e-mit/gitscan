import os
from pathlib import Path
import tempfile
import time
from git import Repo  # type: ignore


def create_temp_git_repo(repo_name: str) -> Path:
    """Create a git repo in a temporary directory"""
    temp_base_dir = Path(tempfile.mkdtemp())
    repo_dir = temp_base_dir / repo_name
    repo = Repo.init(repo_dir)
    repo.git.checkout(b='main')

    # Create text files in the repository
    file_names = ['file1.txt', 'file2.txt', 'file3.txt',
                  'file4.txt', 'file5.txt']
    for file_name in file_names:
        file_path = repo_dir / file_name
        with open(file_path, 'w') as file:
            file.write(f"This is {file_name}\n")

    repo.index.add(file_names)
    repo.index.commit("Initial commit")

    repo.create_tag('v1.0', message="Version 1.0")

    # Create a stash
    stash_file_path = repo_dir / "stash_file.txt"
    with open(stash_file_path, 'w') as stash_file:
        stash_file.write("hello")
    repo.index.add(['stash_file.txt'])
    repo.git.stash('save', 'Stash example')

    # Add more commits
    for i in range(2, 6):
        with open(file_path, 'a') as file:
            file.write(f"Appending data in {file_name}\n")
        repo.index.add([file_name])
        repo.index.commit(f"Commit {i}")

    # Create and switch to 'dev' branch
    repo.git.checkout(b='dev')
    hi_file_path = repo_dir / "hi.txt"
    with open(hi_file_path, 'w') as hi_file:
        hi_file.write("Hi, there!")
    repo.index.add(['hi.txt'])
    repo.index.commit("Add hi.txt on 'new' branch")

    # switch to 'main' branch and close
    repo.git.checkout('main')
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
    repo_base_dir = create_temp_git_repo(repo_name)
    print(f"Temporary Git repository {repo_name} created in {repo_base_dir}")
    time.sleep(6)
    delete_temp_directory(repo_base_dir)
    print("Temporary Git repository deleted.")
