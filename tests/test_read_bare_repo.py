import unittest
from pathlib import Path
from test_read_repo import TestReadRepo

from gitscan.scanner import scanner
from tests import test_helpers


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
