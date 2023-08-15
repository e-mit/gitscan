import unittest
from pathlib import Path
import shutil

from test_read_repo import TestReadRepo
from gitscan.scanner import read
from tests import test_helpers


class TestReadBareRepo(TestReadRepo):
    def setUp(self) -> None:
        super().setUp()  # Produces a new test repo
        self.origin_containing_dir = Path(self.containing_dir)
        # Make a bare clone of the repo and update expected properties
        bare_repo_name = "bare1"
        (self.containing_dir, self.repo_dir,
         self.path_to_git) = test_helpers.create_temp_clone_git_repo(
                                self.repo_dir, bare_repo_name, bare=True)
        self.expected_info['name'] = bare_repo_name
        self.expected_info['containing_dir'] = self.containing_dir
        self.expected_info['remote_count'] = 1
        # the following properties should always be true for bare repos:
        if self.commit_count == 0:
            self.expected_info['branch_name'] = read.NO_BRANCH_DISPLAY_NAME
        else:
            self.expected_info['branch_name'] = self.active_branch
        self.expected_info['bare'] = True
        self.expected_info['untracked_count'] = 0
        self.expected_info['index_changes'] = False
        self.expected_info['working_tree_changes'] = False
        self.expected_info['stash'] = False
        self.expected_info['detached_head'] = False

    def tearDown(self) -> None:
        super().tearDown()
        shutil.rmtree(self.origin_containing_dir)


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
