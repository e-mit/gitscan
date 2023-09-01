import unittest
from pathlib import Path
import shutil
import tempfile

from gitscan.scanner import read
from tests import test_helpers

UNREACHABLE_REPO = "ssh://e@172.24.1.1:322/fake/repo.git"
PRIVATE_REPO = "https://github.com/e-mit/test_auth"
FAIL_REPO = "https://example.com/fake-repo"


class TestFetchWithTimeout(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root_dir = Path(tempfile.mkdtemp())
        self.dirs_to_delete = [self.temp_root_dir]

    def test_not_a_git_repo(self) -> None:
        result = read.git_fetch_with_timeout(self.temp_root_dir)
        self.assertEqual(result, read.FetchStatus.ERROR)

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
        self.assertEqual(result, read.FetchStatus.OK)
        result = read.git_fetch_with_timeout(repo_dir, remote_name='origin')
        self.assertEqual(result, read.FetchStatus.ERROR)
        result = read.git_fetch_with_timeout(repo_dir, remote_name='thename')
        self.assertEqual(result, read.FetchStatus.ERROR)

    def test_nothing_to_fetch(self) -> None:
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
        self.assertEqual(result, read.FetchStatus.OK)

    def test_successful_fetch(self) -> None:
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
        self.assertEqual(result, read.FetchStatus.OK)

    def test_successful_large_fetch(self) -> None:
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
        self.assertEqual(result, read.FetchStatus.OK)

    def test_unreachable_remote(self) -> None:
        (repo_dir, _) = test_helpers.create_git_repo(
                                            self.temp_root_dir,
                                            "no_remote", 1,
                                            [], 0, False,
                                            "main", 1, False,
                                            True, False)
        # the following remote will cause the fetch command to
        # hang until SSH timeout
        test_helpers.add_remote(repo_dir, "origin", UNREACHABLE_REPO)
        result = read.git_fetch_with_timeout(repo_dir)
        self.assertEqual(result, read.FetchStatus.TIMEOUT)

    def test_password_hang(self) -> None:
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
        self.assertEqual(result, read.FetchStatus.TIMEOUT)

    def test_fetch_in_parallel(self) -> None:
        # create several repos with different properties. These are:
        # no remotes, up-to-date, fetch ok,
        # large fetch ok, unreachable, password hang
        (no_remotes, no_remotes_git) = test_helpers.create_git_repo(
                                            self.temp_root_dir,
                                            "no_remotes", 1,
                                            [], 0, False,
                                            "main", 1, False,
                                            True, False)
        (containing_dir1, _,
         large_fetch_ok_git) = test_helpers.create_temp_clone_git_repo(
                                        no_remotes,
                                        "large_fetch_ok",
                                        False)
        self.dirs_to_delete.append(containing_dir1)
        test_helpers.create_commits(no_remotes, 1000)  # wants repo folder
        (containing_dir2, _,
         fetch_ok_git) = test_helpers.create_temp_clone_git_repo(
                                        no_remotes,
                                        "fetch_ok",
                                        False)
        self.dirs_to_delete.append(containing_dir2)
        # repo with one OK remote and one that hangs unreachable:
        (containing_dir2b, fetch_ok_hang,
         fetch_ok_hang_git) = test_helpers.create_temp_clone_git_repo(
                                        no_remotes,
                                        "fetch_ok_hang",
                                        False)
        self.dirs_to_delete.append(containing_dir2b)
        test_helpers.add_remote(fetch_ok_hang, "hanger", UNREACHABLE_REPO)
        # repo with one OK remote and one that hangs for password:
        (containing_dir2c, fetch_ok_pword,
         fetch_ok_pword_git) = test_helpers.create_temp_clone_git_repo(
                                        no_remotes,
                                        "fetch_ok_pword",
                                        False)
        self.dirs_to_delete.append(containing_dir2c)
        test_helpers.add_remote(fetch_ok_pword, "pword", PRIVATE_REPO)
        ###
        # repo with one OK remote, one that hangs for password, one
        # that hangs unreachable, one that errors
        (containing_dir2d, fetch_4,
         fetch_4_git) = test_helpers.create_temp_clone_git_repo(
                                        no_remotes,
                                        "fetch_4",
                                        False)
        self.dirs_to_delete.append(containing_dir2d)
        test_helpers.add_remote(fetch_4, "private", PRIVATE_REPO)
        test_helpers.add_remote(fetch_4, "unreachable", UNREACHABLE_REPO)
        test_helpers.add_remote(fetch_4, "error", FAIL_REPO)
        ###
        test_helpers.create_commits(no_remotes, 3)
        (containing_dir3, _,
         up_to_date_git) = test_helpers.create_temp_clone_git_repo(
                                        no_remotes,
                                        "up_to_date",
                                        False)
        self.dirs_to_delete.append(containing_dir3)
        (unreachable, unreachable_git) = test_helpers.create_git_repo(
                                            self.temp_root_dir,
                                            "unreachable", 1,
                                            [], 0, False,
                                            "main", 1, False,
                                            True, False)
        test_helpers.add_remote(unreachable, "origin", UNREACHABLE_REPO)
        (password_hang, password_hang_git) = test_helpers.create_git_repo(
                                            self.temp_root_dir,
                                            "hang", 1,
                                            [], 0, False,
                                            "main", 1, False,
                                            True, False)
        test_helpers.add_remote(password_hang, "origin", PRIVATE_REPO)
        (non_exist, non_exist_git) = test_helpers.create_git_repo(
                                            self.temp_root_dir,
                                            "non_exist", 1,
                                            [], 0, False,
                                            "main", 1, False,
                                            True, False)
        test_helpers.add_remote(non_exist, "foo", FAIL_REPO)
        ##########
        paths_to_git = [no_remotes_git,
                        large_fetch_ok_git, fetch_ok_git, fetch_ok_hang_git,
                        fetch_ok_pword_git, fetch_4_git, up_to_date_git,
                        unreachable_git, password_hang_git, non_exist_git]
        expected_status = [None,
                           read.FetchStatus.OK, read.FetchStatus.OK,
                           read.FetchStatus.OK | read.FetchStatus.TIMEOUT,
                           read.FetchStatus.OK | read.FetchStatus.TIMEOUT,
                           (read.FetchStatus.OK | read.FetchStatus.TIMEOUT
                            | read.FetchStatus.ERROR), read.FetchStatus.OK,
                           read.FetchStatus.TIMEOUT, read.FetchStatus.TIMEOUT,
                           read.FetchStatus.ERROR]
        expected_ahead = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        expected_behind = [0, 1003, 3, 3, 3, 3, 0, 0, 0, 0]
        expected_remotes = [0, 1, 1, 2, 2, 4, 1, 1, 1, 1]
        results = read.read_repo_parallel(paths_to_git)
        for i in range(len(paths_to_git)):
            with self.subTest(i=i):
                self.assertEqual(results[i]['fetch_status'],
                                 expected_status[i])
                self.assertEqual(results[i]['ahead_count'],
                                 expected_ahead[i])
                self.assertEqual(results[i]['behind_count'],
                                 expected_behind[i])
                self.assertEqual(results[i]['remote_count'],
                                 expected_remotes[i])

    def tearDown(self) -> None:
        for d in self.dirs_to_delete:
            shutil.rmtree(d)


if __name__ == '__main__':
    unittest.main()
