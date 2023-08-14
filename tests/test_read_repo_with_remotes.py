import unittest
from pathlib import Path
import shutil

from test_read_repo import TestReadRepo
from tests import test_helpers


class TestReadRepoWithRemotes(TestReadRepo):
    remote_count = 1
    ahead_count = 0
    behind_each_remote_count = [0]

    def setUp(self) -> None:
        super().setUp()  # Produces a new test repo
        self.remote_containing_dirs: list[Path] = []
        self.remote_repo_dir: list[Path] = []
        for clone_count in range(self.remote_count):
            # save the temp directory so it can be deleted/remoted:
            self.remote_containing_dirs.append(Path(self.containing_dir))
            self.remote_repo_dir.append(Path(self.repo_dir))
            # Make a new clone
            self.clone_repo_name = f"clone{clone_count}"
            (self.containing_dir, self.repo_dir,
             self.path_to_git) = test_helpers.create_temp_clone_git_repo(
                                    self.repo_dir, self.clone_repo_name,
                                    bare=False)
            # If required, do commits on the cloned repo:
            test_helpers.create_commits(
                self.remote_repo_dir[-1],
                self.behind_each_remote_count[clone_count])
        # Set all repos as remotes, except final one ('origin' by default):
        for rem in range(self.remote_count - 1):
            test_helpers.add_remote(self.path_to_git, f"remote{rem}",
                                    self.remote_repo_dir[rem])
        test_helpers.create_commits(self.repo_dir, self.ahead_count)
        self.expected_info['name'] = self.clone_repo_name
        self.expected_info['containing_dir'] = self.containing_dir
        # the following properties apply to the clones, irrespective of origin:
        self.expected_info['bare'] = False
        self.expected_info['remote_count'] = self.remote_count
        self.expected_info['branch_count'] = 1
        self.expected_info['untracked_count'] = 0
        self.expected_info['index_changes'] = False
        self.expected_info['working_tree_changes'] = False
        self.expected_info['stash'] = False
        self.expected_info['behind_count'] = sum(self.behind_each_remote_count)
        self.expected_info['ahead_count'] = self.ahead_count

    def tearDown(self) -> None:
        super().tearDown()  # this deletes the final cloned repo
        for temp_dir in self.remote_containing_dirs:
            shutil.rmtree(temp_dir)


class TestReadRepoWithMultipleRemotes(TestReadRepoWithRemotes):
    def setUp(self) -> None:
        self.remote_count = 2
        self.behind_each_remote_count = [0]*self.remote_count
        super().setUp()


class TestReadRepoWithManyRemotes(TestReadRepoWithRemotes):
    def setUp(self) -> None:
        self.remote_count = 4
        self.behind_each_remote_count = [0]*self.remote_count
        self.extra_branches = ['dev', 'test']
        self.active_branch = 'dev'
        self.working_tree_changes = True
        self.untracked_count = 4
        self.index_changes = True
        self.tag_count = 2
        self.stash = True
        super().setUp()


class TestReadRepoAheadOfRemotes(TestReadRepoWithRemotes):
    def setUp(self) -> None:
        self.ahead_count = 3
        super().setUp()


class TestReadRepoBehindRemotes(TestReadRepoWithRemotes):
    def setUp(self) -> None:
        self.behind_each_remote_count = [3]
        super().setUp()


class TestReadRepoBehindManyRemotes(TestReadRepoWithRemotes):
    def setUp(self) -> None:
        self.remote_count = 3
        self.behind_each_remote_count = [2, 1, 3]
        super().setUp()


class TestReadRepoAheadAndBehindRemotes(TestReadRepoWithRemotes):
    def setUp(self) -> None:
        self.ahead_count = 2
        self.remote_count = 4
        self.behind_each_remote_count = [1, 3, 1, 0]
        super().setUp()


class TestReadRepoFailFetch(TestReadRepoWithRemotes):
    def setUp(self) -> None:
        self.ahead_count = 2
        self.remote_count = 4
        self.behind_each_remote_count = [1, 3, 1, 0]
        super().setUp()
        test_helpers.add_remote(self.path_to_git, "fakerepo",
                                "https://example.com/fake-repo")
        self.expected_info['fetch_failed'] = True
        self.expected_info['remote_count'] = self.remote_count + 1


class TestReadRepoCloneOfEmpty(TestReadRepoWithRemotes):
    def setUp(self) -> None:
        self.commit_count = 0
        super().setUp()
        self.expected_info['branch_count'] = 0


class TestReadRepoCloneOfEmptyWithCommits(TestReadRepoWithRemotes):
    def setUp(self) -> None:
        self.ahead_count = 2
        self.commit_count = 0
        super().setUp()
        self.commit_count = 2
        self.expected_info['fetch_failed'] = True
        self.expected_info['branch_name'] = "master"  # the default
        self.expected_info['ahead_count'] = 0


class TestReadRepoCloneOfDetachedHead(TestReadRepoWithRemotes):
    def setUp(self) -> None:
        self.commit_count = 3
        self.detached_head = True
        super().setUp()
        self.commit_count = 0
        self.expected_info['branch_count'] = 0


if __name__ == '__main__':
    unittest.main()
