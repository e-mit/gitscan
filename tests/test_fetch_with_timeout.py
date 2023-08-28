import unittest
from pathlib import Path
import shutil
import time
import tempfile

from gitscan.scanner import read
from tests import test_helpers

UNREACHABLE_REPO = "ssh://e@172.24.1.1:322/fake/repo.git"
PRIVATE_REPO = "https://github.com/e-mit/test_auth"


class TestFetchWithTimeout(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root_dir = Path(tempfile.mkdtemp())
        self.dirs_to_delete = [self.temp_root_dir]

    def test_not_a_git_repo(self) -> None:
        print("test_not_a_git_repo")
        result = read.git_fetch_with_timeout(self.temp_root_dir)
        self.assertEqual(result, "error")

    def test_no_remotes(self) -> None:
        # Expect "None" if default fetch is used, or
        # "error" if any remote is specified by name
        (repo_dir, _) = test_helpers.create_git_repo(
                                            self.temp_root_dir,
                                            "no_remote", 1,
                                            [], 0, False,
                                            "main", 1, False,
                                            True, False)
        result = read.git_fetch_with_timeout(repo_dir)
        self.assertIsNone(result)
        result = read.git_fetch_with_timeout(repo_dir, remote_name='origin')
        self.assertEqual(result, "error")
        result = read.git_fetch_with_timeout(repo_dir, remote_name='thename')
        self.assertEqual(result, "error")

    def test_nothing_to_fetch(self) -> None:
        print("test_nothing_to_fetch")
        (origin_repo_dir, _) = test_helpers.create_git_repo(
                                            self.temp_root_dir,
                                            "origin_repo", 3,
                                            ["dev"], 0, False,
                                            "main", 0, False,
                                            False, False)
        (containing_dir,
         repo_dir, _) = test_helpers.create_temp_clone_git_repo(
                                        origin_repo_dir,
                                        "clone_repo",
                                        False)
        self.dirs_to_delete.append(containing_dir)
        result = read.git_fetch_with_timeout(repo_dir)
        self.assertIsNone(result)

    def test_successful_fetch(self) -> None:
        print("test_successful_fetch")
        (origin_repo_dir, _) = test_helpers.create_git_repo(
                                            self.temp_root_dir,
                                            "origin_repo", 3,
                                            ["dev"], 0, False,
                                            "main", 0, False,
                                            False, False)
        (containing_dir,
         repo_dir, _) = test_helpers.create_temp_clone_git_repo(
                                        origin_repo_dir,
                                        "clone_repo",
                                        False)
        self.dirs_to_delete.append(containing_dir)
        test_helpers.create_commits(origin_repo_dir, 3)
        result = read.git_fetch_with_timeout(repo_dir)
        self.assertIsNone(result)

    def test_successful_large_fetch(self) -> None:
        print("test_successful_large_fetch")
        (origin_repo_dir, _) = test_helpers.create_git_repo(
                                            self.temp_root_dir,
                                            "origin_repo", 3,
                                            ["dev"], 0, False,
                                            "main", 0, False,
                                            False, False)
        (containing_dir,
         repo_dir, _) = test_helpers.create_temp_clone_git_repo(
                                        origin_repo_dir,
                                        "clone_repo",
                                        False)
        self.dirs_to_delete.append(containing_dir)
        test_helpers.create_commits(origin_repo_dir, 1000)
        result = read.git_fetch_with_timeout(repo_dir)
        self.assertIsNone(result)

    def test_unreachable_remote(self) -> None:
        print("test_unreachable_remote")
        (repo_dir, _) = test_helpers.create_git_repo(
                                            self.temp_root_dir,
                                            "no_remote", 1,
                                            [], 0, False,
                                            "main", 1, False,
                                            True, False)
        # the following remote will cause the fetch command to hang until SSH timeout
        test_helpers.add_remote(repo_dir, "origin", UNREACHABLE_REPO)
        result = read.git_fetch_with_timeout(repo_dir)
        self.assertEqual(result, "timeout")

    def test_password_hang(self) -> None:
        print("test_password_hang")
        (repo_dir, _) = test_helpers.create_git_repo(
                                            self.temp_root_dir,
                                            "no_remote", 1,
                                            [], 0, False,
                                            "main", 1, False,
                                            True, False)
        # the following remote requires a username and password
        remote_name = "needs_auth"
        test_helpers.add_remote(repo_dir, remote_name, PRIVATE_REPO)
        result = read.git_fetch_with_timeout(repo_dir, remote_name=remote_name)
        self.assertEqual(result, "timeout")

    def test_fetch_in_parallel(self) -> None:
        print("test_fetch_in_parallel")
        # create several repos with different properties. These are:
        # not a repo, no remotes, up-to-date, fetch ok,
        # large fetch ok, unreachable, password hang
        (no_remotes, _) = test_helpers.create_git_repo(
                                            self.temp_root_dir,
                                            "no_remote", 1,
                                            [], 0, False,
                                            "main", 1, False,
                                            True, False)
        (containing_dir1,
         large_fetch_ok, _) = test_helpers.create_temp_clone_git_repo(
                                        no_remotes,
                                        "clone_repo1",
                                        False)
        self.dirs_to_delete.append(containing_dir1)
        test_helpers.create_commits(no_remotes, 1000)
        (containing_dir2,
         fetch_ok, _) = test_helpers.create_temp_clone_git_repo(
                                        no_remotes,
                                        "clone_repo2",
                                        False)
        self.dirs_to_delete.append(containing_dir2)
        test_helpers.create_commits(no_remotes, 3)
        (containing_dir3,
         up_to_date, _) = test_helpers.create_temp_clone_git_repo(
                                        no_remotes,
                                        "clone_repo3",
                                        False)
        self.dirs_to_delete.append(containing_dir3)
        (unreachable, _) = test_helpers.create_git_repo(
                                            self.temp_root_dir,
                                            "unreachable", 1,
                                            [], 0, False,
                                            "main", 1, False,
                                            True, False)
        test_helpers.add_remote(unreachable, "origin", UNREACHABLE_REPO)
        (password_hang, _) = test_helpers.create_git_repo(
                                            self.temp_root_dir,
                                            "hang", 1,
                                            [], 0, False,
                                            "main", 1, False,
                                            True, False)
        test_helpers.add_remote(password_hang, "origin", PRIVATE_REPO)
        git_repo_directories = [self.temp_root_dir, no_remotes,
                                large_fetch_ok, fetch_ok, up_to_date,
                                unreachable, password_hang]
        expected_results = ["error", None, None, None,
                            None, "timeout", "timeout"]
        results = read.git_fetch_parallel(git_repo_directories)
        self.assertEqual(results, expected_results)

    def tearDown(self) -> None:
        for d in self.dirs_to_delete:
            shutil.rmtree(d)


if __name__ == '__main__':
    unittest.main()
