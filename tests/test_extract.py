import unittest
from pathlib import Path
from typing import Any
from datetime import datetime
from zoneinfo import ZoneInfo

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
    commit_count = 1
    extra_branches: list[str] = []
    tag_count = 0
    stash = False
    active_branch = 'main'
    untracked_count = 0
    index_changes = False
    working_tree_changes = False
    detached_head = False

    def setUp(self) -> None:
        (self.repo_base_dir,
         self.path_to_git) = test_helpers.create_temp_git_repo(
                                            self.repo_name,
                                            self.commit_count,
                                            self.extra_branches,
                                            self.tag_count, self.stash,
                                            self.active_branch,
                                            self.untracked_count,
                                            self.index_changes,
                                            self.working_tree_changes,
                                            self.detached_head)
        if self.detached_head:
            expected_branch_name = scanner.DETACHED_BRANCH_DISPLAY_NAME
        elif self.commit_count == 0:
            expected_branch_name = scanner.NO_BRANCH_DISPLAY_NAME
        else:
            expected_branch_name = self.active_branch
        self.expected_info = {
            'name': self.repo_name,
            'path': self.repo_base_dir,
            'bare': False,
            'remote_count': 0,
            'branch_count': (0 if self.commit_count == 0
                             else len(self.extra_branches) + 1),
            'tag_count': self.tag_count,
            'untracked_count': self.untracked_count,
            'index_changes': self.index_changes,
            'working_tree_changes': self.working_tree_changes,
            'stash': self.stash,
            'branch_name': expected_branch_name,
            'detached_head': self.detached_head,
            'ahead_count': 0,
            'behind_count': 0,
            'up_to_date': True
            }

    def tearDown(self) -> None:
        test_helpers.delete_temp_directory(self.repo_base_dir)

    def test_read_repo(self) -> None:
        info: dict[str, Any] = scanner.read_repo(self.path_to_git)
        last_commit_datetime = info.pop('last_commit_datetime')
        with self.subTest(key='last_commit_datetime'):
            if (self.commit_count == 0):
                self.assertIsNone(last_commit_datetime)
            else:
                self.assertTrue(last_commit_datetime <
                                datetime.now(ZoneInfo('UTC')))
                self.assertTrue((datetime.now(ZoneInfo('UTC')) -
                                last_commit_datetime).total_seconds() < 20.0)
        with self.subTest(key='key_sets'):
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


class TestReadRepoNoCommits(TestReadRepo):
    def setUp(self) -> None:
        self.commit_count = 0
        super().setUp()


class TestReadRepoNoCommitsUntracked(TestReadRepo):
    def setUp(self) -> None:
        self.commit_count = 0
        self.untracked_count = 1
        super().setUp()


class TestReadRepoNoCommitsIndex(TestReadRepo):
    def setUp(self) -> None:
        self.commit_count = 0
        self.index_changes = True
        super().setUp()


class TestReadBareRepo(TestReadRepo):
    def setUp(self) -> None:
        super().setUp()  # Produces a new test repo
        self.origin_repo_base_dir = Path(self.repo_base_dir)
        # Make a bare clone of the repo and update expected properties
        bare_repo_name = "bare1"
        (self.repo_base_dir,
         self.path_to_git) = test_helpers.create_temp_clone_git_repo(
                                self.path_to_git, bare_repo_name)
        self.expected_info['name'] = bare_repo_name
        self.expected_info['path'] = self.repo_base_dir
        self.expected_info['remote_count'] = 1
        # the following properties should always be true for bare repos:
        if self.commit_count == 0:
            expected_branch_name = scanner.NO_BRANCH_DISPLAY_NAME
        else:
            expected_branch_name = self.active_branch
        self.expected_info['bare'] = True
        self.expected_info['untracked_count'] = 0
        self.expected_info['index_changes'] = False
        self.expected_info['working_tree_changes'] = False
        self.expected_info['stash'] = False
        self.expected_info['detached_head'] = False
        self.expected_info['branch_name'] = expected_branch_name

    def tearDown(self) -> None:
        super().tearDown()
        test_helpers.delete_temp_directory(self.origin_repo_base_dir)


class TestReadBareRepoStash(TestReadBareRepo):
    def setUp(self) -> None:
        self.stash = True
        super().setUp()


class TestReadBareRepoBranches(TestReadBareRepo):
    def setUp(self) -> None:
        self.extra_branches = ['dev', 'test']
        super().setUp()


class TestReadBareRepoTags(TestReadBareRepo):
    def setUp(self) -> None:
        self.tag_count = 3
        super().setUp()


class TestReadBareRepoActiveBranch(TestReadBareRepo):
    def setUp(self) -> None:
        self.extra_branches = ['dev', 'test']
        self.active_branch = 'dev'
        super().setUp()


class TestReadBareRepoUntracked(TestReadBareRepo):
    def setUp(self) -> None:
        self.untracked_count = 2
        super().setUp()


class TestReadBareRepoIndex(TestReadBareRepo):
    def setUp(self) -> None:
        self.index_changes = True
        super().setUp()


class TestReadBareRepoWorkingTree(TestReadBareRepo):
    def setUp(self) -> None:
        self.working_tree_changes = True
        super().setUp()


class TestReadBareRepoDetachedHead(TestReadBareRepo):
    def setUp(self) -> None:
        self.detached_head = True
        super().setUp()


class TestReadBareRepoUntrackedModified(TestReadBareRepo):
    def setUp(self) -> None:
        self.extra_branches = ['dev']
        self.active_branch = 'dev'
        self.working_tree_changes = True
        self.untracked_count = 4
        super().setUp()


class TestReadBareRepoUntrackedIndex(TestReadBareRepo):
    def setUp(self) -> None:
        self.index_changes = True
        self.untracked_count = 3
        super().setUp()


class TestReadBareRepoDetachedIndex(TestReadBareRepo):
    def setUp(self) -> None:
        self.index_changes = True
        self.detached_head = True
        super().setUp()


class TestReadBareRepoNoCommits(TestReadBareRepo):
    def setUp(self) -> None:
        self.commit_count = 0
        super().setUp()


class TestReadBareRepoNoCommitsUntracked(TestReadBareRepo):
    def setUp(self) -> None:
        self.commit_count = 0
        self.untracked_count = 1
        super().setUp()


class TestReadBareRepoNoCommitsIndex(TestReadBareRepo):
    def setUp(self) -> None:
        self.commit_count = 0
        self.index_changes = True
        super().setUp()


if __name__ == '__main__':
    unittest.main()
