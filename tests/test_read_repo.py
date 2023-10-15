import unittest
from typing import Any
from datetime import datetime
from zoneinfo import ZoneInfo
import shutil
import warnings

from gitscan.scanner import read
from tests import test_helpers


MAX_EXPECTED_TEST_COMMIT_AGE_S = 30.0
READ_COMMIT_COUNT = 3


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
    less_than_2_commits = True

    def calculate_expected_commits(self):
        if self.commit_count == 0:
            self.total_commits = 0
        else:
            self.total_commits = self.commit_count
            if self.active_branch != 'main':
                self.total_commits += (
                    1 + self.extra_branches.index(self.active_branch))
        if self.detached_head:
            self.total_commits -= self.commit_count - 1

    def setUp(self) -> None:
        warnings.filterwarnings("ignore", category=ResourceWarning)
        self.calculate_expected_commits()
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
            'repo_dir': self.repo_dir,
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
            'fetch_status': None,
            'submodule_names': []}

    def tearDown(self) -> None:
        shutil.rmtree(self.containing_dir)

    def update_uptodate(self):
        self.expected_info['up_to_date'] = (
            self.expected_info['ahead_count'] == 0
            and self.expected_info['behind_count'] == 0)

    def test_read_repo(self) -> None:
        self.update_uptodate()
        info: None | dict[str, Any] = read.read_repo(self.path_to_git)
        if info is None:
            raise ValueError("Git repository was nonexistent or corrupt.")
        for pop_name in ['warning', 'branch_names', 'remote_names']:
            info.pop(pop_name)
        last_commit_datetime = info.pop('last_commit_datetime')
        with self.subTest(key='last_commit_datetime'):
            if (self.commit_count == 0):
                self.assertIsNone(last_commit_datetime)
            else:
                self.assertTrue(last_commit_datetime
                                < datetime.now(ZoneInfo('UTC')))
                self.assertTrue((datetime.now(ZoneInfo('UTC'))
                                - last_commit_datetime).total_seconds()
                                < MAX_EXPECTED_TEST_COMMIT_AGE_S)
        commit_count = info.pop('commit_count')
        with self.subTest(key='commit_count'):
            self.assertEqual(commit_count < 2, self.less_than_2_commits)
        fetch_status = info.pop('fetch_status')
        with self.subTest(key='fetch_status'):
            self.assertEqual(
                fetch_status == read.FetchStatus.OK,
                self.expected_info['fetch_status'] == read.FetchStatus.OK)
        self.expected_info.pop('fetch_status')
        with self.subTest(key='key_sets'):
            self.assertEqual(set(info.keys()), set(self.expected_info.keys()))
        for k in self.expected_info:
            with self.subTest(key=k):
                self.assertEqual(info[k], self.expected_info[k])

    def test_read_commits(self) -> None:
        commits = read.read_commits(self.path_to_git, READ_COMMIT_COUNT)
        self.assertIsNotNone(commits)
        if commits is not None:
            expected_commit_count = min([READ_COMMIT_COUNT,
                                        self.total_commits])
            self.assertEqual(expected_commit_count, len(commits))
            for i in range(len(commits)):
                with self.subTest(i=i):
                    self.assertNotIn("\n", commits[i]['summary'])


class TestReadRepoStash(TestReadRepo):
    stash = True


class TestReadRepoBranches(TestReadRepo):
    extra_branches = ['dev', 'test']


class TestReadRepoTags(TestReadRepo):
    tag_count = 3


class TestReadRepoActiveBranch(TestReadRepo):
    extra_branches = ['dev', 'test']
    active_branch = 'dev'
    less_than_2_commits = False


class TestReadRepoUntracked(TestReadRepo):
    untracked_count = 2


class TestReadRepoIndex(TestReadRepo):
    index_changes = True


class TestReadRepoWorkingTree(TestReadRepo):
    working_tree_changes = True


class TestReadRepoDetachedHead(TestReadRepo):
    detached_head = True


class TestReadRepoUntrackedModified(TestReadRepo):
    extra_branches = ['dev']
    active_branch = 'dev'
    working_tree_changes = True
    untracked_count = 4
    less_than_2_commits = False


class TestReadRepoUntrackedIndex(TestReadRepo):
    index_changes = True
    untracked_count = 3


class TestReadRepoDetachedIndex(TestReadRepo):
    index_changes = True
    detached_head = True


class TestReadRepoNoCommits(TestReadRepo):
    commit_count = 0


class TestReadRepoNoCommitsUntracked(TestReadRepo):
    commit_count = 0
    untracked_count = 1


class TestReadRepoNoCommitsIndex(TestReadRepo):
    commit_count = 0
    index_changes = True


class TestReadCommits(unittest.TestCase):
    def test_return_none(self) -> None:
        self.assertIsNone(read.read_commits("/fake/directory/not_git", 3))


if __name__ == '__main__':
    unittest.main()
