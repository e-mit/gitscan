import unittest
from pathlib import Path
from typing import Any
from gitscan.scanner import scanner
from tests import test_helpers


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
    # default/simplest values:
    repo_name = "testrepo"
    commit_count = 5
    extra_branches: list[str] = []
    tag_count = 0
    stash = False
    active_branch = 'main'
    untracked_count = 0
    index_changes = False
    working_tree_changes = False
    detached_head = False

    def setUp(self) -> None:
        self.repo_base_dir = test_helpers.create_temp_git_repo(
                                            self.repo_name,
                                            self.commit_count,
                                            self.extra_branches,
                                            self.tag_count, self.stash,
                                            self.active_branch,
                                            self.untracked_count,
                                            self.index_changes,
                                            self.working_tree_changes,
                                            self.detached_head)
        self.path_to_git = self.repo_base_dir / self.repo_name / ".git"
        self.expected_info = {
            'name': self.repo_name,
            'path': self.repo_base_dir,
            'bare': False,
            'remote_count': 0,
            'branch_count': len(self.extra_branches) + 1,
            'tag_count': self.tag_count,
            'untracked_count': self.untracked_count,
            'index_changes': self.index_changes,
            'working_tree_changes': self.working_tree_changes,
            'stash': self.stash,
            'branch_name':
                "detached" if self.detached_head else self.active_branch,
            'detached_head': self.detached_head,
            'ahead_count': 0,
            'behind_count': 0,
            'up_to_date': True
            }

    def tearDown(self) -> None:
        test_helpers.delete_temp_directory(self.repo_base_dir)

    def test_read_repo(self) -> None:
        info: dict[str, Any] = scanner.read_repo(self.path_to_git)
        self.assertEqual(set(info.keys()), set(self.expected_info.keys()))
        for k in self.expected_info:
            with self.subTest(key=k):
                self.assertEqual(info[k], self.expected_info[k])


class TestReadRepoStash(TestReadRepo):
    def setUp(self) -> None:
        self.stash = True
        super().setUp()


class TestReadRepoBranches(TestReadRepo):
    def setUp(self) -> None:
        self.extra_branches = ['dev', 'test']
        super().setUp()


class TestReadRepoTags(TestReadRepo):
    def setUp(self) -> None:
        self.tag_count = 3
        super().setUp()


class TestReadRepoActiveBranch(TestReadRepo):
    def setUp(self) -> None:
        self.extra_branches = ['dev', 'test']
        self.active_branch = 'dev'
        super().setUp()


class TestReadRepoUntracked(TestReadRepo):
    def setUp(self) -> None:
        self.untracked_count = 2
        super().setUp()


class TestReadRepoIndex(TestReadRepo):
    def setUp(self) -> None:
        self.index_changes = True
        super().setUp()


class TestReadRepoWorkingTree(TestReadRepo):
    def setUp(self) -> None:
        self.working_tree_changes = True
        super().setUp()


class TestReadRepoDetachedHead(TestReadRepo):
    def setUp(self) -> None:
        self.detached_head = True
        super().setUp()


class TestReadRepoUntrackedModified(TestReadRepo):
    def setUp(self) -> None:
        self.extra_branches = ['dev']
        self.active_branch = 'dev'
        self.working_tree_changes = True
        self.untracked_count = 4
        super().setUp()


class TestReadRepoUntrackedIndex(TestReadRepo):
    def setUp(self) -> None:
        self.index_changes = True
        self.untracked_count = 3
        super().setUp()


class TestReadRepoDetachedIndex(TestReadRepo):
    def setUp(self) -> None:
        self.index_changes = True
        self.detached_head = True
        super().setUp()


if __name__ == '__main__':
    unittest.main()
