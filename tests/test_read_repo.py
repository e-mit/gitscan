import unittest
from typing import Any
from datetime import datetime
from zoneinfo import ZoneInfo
import shutil

from gitscan.scanner import read
from tests import test_helpers


MAX_EXPECTED_TEST_COMMIT_AGE_S = 20.0


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
        (self.containing_dir, self.repo_dir,
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
            expected_branch_name = read.DETACHED_BRANCH_DISPLAY_NAME
        elif self.commit_count == 0:
            expected_branch_name = read.NO_BRANCH_DISPLAY_NAME
        else:
            expected_branch_name = self.active_branch
        self.expected_info = {
            'name': self.repo_name,
            'containing_dir': self.containing_dir,
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
            'fetch_failed': False
            }

    def tearDown(self) -> None:
        shutil.rmtree(self.containing_dir)

    def update_uptodate(self):
        self.expected_info['up_to_date'] = (
                    self.expected_info['ahead_count'] == 0 and
                    self.expected_info['behind_count'] == 0)

    def test_read_repo(self) -> None:
        self.update_uptodate()
        info: dict[str, Any] = read.read_repo(self.path_to_git)
        last_commit_datetime = info.pop('last_commit_datetime')
        with self.subTest(key='last_commit_datetime'):
            if (self.commit_count == 0):
                self.assertIsNone(last_commit_datetime)
            else:
                self.assertTrue(last_commit_datetime <
                                datetime.now(ZoneInfo('UTC')))
                self.assertTrue((datetime.now(ZoneInfo('UTC')) -
                                last_commit_datetime).total_seconds()
                                < MAX_EXPECTED_TEST_COMMIT_AGE_S)
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


if __name__ == '__main__':
    unittest.main()
