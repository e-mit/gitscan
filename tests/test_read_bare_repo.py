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
        self.expected_info['repo_dir'] = self.repo_dir
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
    stash = True


class TestReadBareRepoBranches(TestReadBareRepo):
    extra_branches = ['dev', 'test']


class TestReadBareRepoTags(TestReadBareRepo):
    tag_count = 3


class TestReadBareRepoActiveBranch(TestReadBareRepo):
    extra_branches = ['dev', 'test']
    active_branch = 'dev'
    less_than_2_commits = False


class TestReadBareRepoUntracked(TestReadBareRepo):
    untracked_count = 2


class TestReadBareRepoIndex(TestReadBareRepo):
    index_changes = True


class TestReadBareRepoWorkingTree(TestReadBareRepo):
    working_tree_changes = True


class TestReadBareRepoDetachedHead(TestReadBareRepo):
    detached_head = True


class TestReadBareRepoUntrackedModified(TestReadBareRepo):
    extra_branches = ['dev']
    active_branch = 'dev'
    working_tree_changes = True
    untracked_count = 4
    less_than_2_commits = False


class TestReadBareRepoUntrackedIndex(TestReadBareRepo):
    index_changes = True
    untracked_count = 3


class TestReadBareRepoDetachedIndex(TestReadBareRepo):
    index_changes = True
    detached_head = True


class TestReadBareRepoNoCommits(TestReadBareRepo):
    commit_count = 0


class TestReadBareRepoNoCommitsUntracked(TestReadBareRepo):
    commit_count = 0
    untracked_count = 1


class TestReadBareRepoNoCommitsIndex(TestReadBareRepo):
    commit_count = 0
    index_changes = True


if __name__ == '__main__':
    unittest.main()
