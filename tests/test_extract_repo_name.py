import unittest
from pathlib import Path

from gitscan.scanner import scanner


class TestExtractRepoName(unittest.TestCase):
    git_dir = ["data/clean_repo/.git",
               "/fake/folder/data/bare_repo_2.git",
               "data/folder_1/bare_repo_1"]
    actual_repo_name = ["clean_repo", "bare_repo_2", "bare_repo_1"]
    actual_repo_path = [Path("data/clean_repo"),
                        Path("/fake/folder/data/bare_repo_2.git"),
                        Path("data/folder_1/bare_repo_1")]
    actual_containing_path = [Path("data"), Path("/fake/folder/data"),
                              Path("data/folder_1")]

    def test_with_Path(self) -> None:
        for i in range(len(self.git_dir)):
            with self.subTest(i=i):
                (repo_name, repo_path,
                 containing_path) = scanner.extract_repo_name(
                                        Path(self.git_dir[i]))
                self.assertEqual(repo_name, self.actual_repo_name[i])
                self.assertEqual(repo_path, self.actual_repo_path[i])
                self.assertEqual(containing_path,
                                 self.actual_containing_path[i])

    def test_with_string(self) -> None:
        for i in range(len(self.git_dir)):
            with self.subTest(i=i):
                (repo_name, repo_path,
                 containing_path) = scanner.extract_repo_name(
                                                self.git_dir[i])
                self.assertEqual(repo_name, self.actual_repo_name[i])
                self.assertEqual(repo_path, self.actual_repo_path[i])
                self.assertEqual(containing_path,
                                 self.actual_containing_path[i])


if __name__ == '__main__':
    unittest.main()
