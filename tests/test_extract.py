import unittest
from pathlib import Path
from typing import Any
from gitscan.scanner import scanner


class TestExtractRepoName(unittest.TestCase):
    git_dir = ["data/clean_repo/.git", "/fake/folder/data/bare_repo_2.git",
               "data/folder_1/bare_repo_1"]
    actual_repo_name = ["clean_repo", "bare_repo_2", "bare_repo_1"]
    actual_repo_path = [Path("data"), Path("/fake/folder/data"),
                        Path("data/folder_1")]

    def test_with_Path(self) -> None:
        for i in range(len(self.git_dir)):
            with self.subTest(i=i):
                (repo_name, repo_path) = scanner.extract_repo_name(
                    Path(self.git_dir[i]))
                self.assertEqual(repo_name, self.actual_repo_name[i])
                self.assertEqual(repo_path, self.actual_repo_path[i])

    def test_with_string(self) -> None:
        for i in range(len(self.git_dir)):
            with self.subTest(i=i):
                (repo_name, repo_path) = scanner.extract_repo_name(
                    self.git_dir[i])
                self.assertEqual(repo_name, self.actual_repo_name[i])
                self.assertEqual(repo_path, self.actual_repo_path[i])


class TestReadRepo(unittest.TestCase):

    def setUp(self) -> None:
        self.path_to_git = "/home/e/Desktop/data/clean_repo/.git"
        # create the git repo
        # do the steps
        self.expected_info = {'name': 'clean_repo',
                              'path': Path('/home/e/Desktop/data'),
                              'bare': False,
                              'remote_count': 0,
                              'branch_count': 2,
                              'tag_count': 1,
                              'untracked_count': 0,
                              'index_changes': False,
                              'working_tree_changes': False,
                              'stash': True,
                              'branch_name': 'master',
                              'detached_head': False,
                              'ahead_count': 0,
                              'behind_count': 0,
                              'up_to_date': True
                              }

    def tearDown(self) -> None:
        # delete the git repo
        ...

    def test_with_Path(self) -> None:
        info: dict[str, Any] = scanner.read_repo(self.path_to_git)
        self.assertEqual(set(info.keys()), set(self.expected_info.keys()))
        for k in self.expected_info:
            with self.subTest(key=k):
                self.assertEqual(info[k], self.expected_info[k])


if __name__ == '__main__':
    unittest.main()
