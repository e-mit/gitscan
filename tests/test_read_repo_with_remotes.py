import unittest
from pathlib import Path
import shutil

from test_read_repo import TestReadRepo
from tests import test_helpers
from gitscan.scanner import read


class TestReadRepoWithRemotes(TestReadRepo):
    ahead_of_each_remote_count = [0]
    behind_each_remote_count = [0]
    local_only_branch_count = 0

    def setUp(self) -> None:
        super().setUp()  # Produces a new test repo
        self.remote_count = len(self.behind_each_remote_count)
        if (len(self.ahead_of_each_remote_count) != self.remote_count):
            raise ValueError("Ahead and behind counts have "
                             "inconsistent lengths")
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
                                                          self.repo_dir,
                                                          self.clone_repo_name,
                                                          bare=False)
        # Set all repos as remotes of the final repo, and create a local
        # branch which tracks that remote's main. Do not do this for
        # the penultimate repo because it is already added (as 'origin')
        tracking_branch_names = []
        for rem in range(self.remote_count - 1):
            branch_name = test_helpers.create_remote_tracking_branches(
                self.repo_dir, f"remote{rem}", self.remote_repo_dir[rem])
            tracking_branch_names.append(branch_name[0])
        tracking_branch_names.append(self.active_branch)

        # If required, do commits on the remotes to go "behind"
        for rem in range(self.remote_count):
            test_helpers.create_commits(self.remote_repo_dir[rem],
                                        self.behind_each_remote_count[rem])

        # If required, do commits on the final repo to go "ahead"
        if self.commit_count > 0 and not self.detached_head:
            test_helpers.do_commits_on_branches(
                self.repo_dir,
                tracking_branch_names,
                self.ahead_of_each_remote_count)

        test_helpers.create_local_branches(self.repo_dir,
                                           self.local_only_branch_count)
        self.total_commits += self.ahead_of_each_remote_count[-1]
        self.expected_info['name'] = self.clone_repo_name
        self.expected_info['containing_dir'] = self.containing_dir
        self.expected_info['repo_dir'] = self.repo_dir
        self.expected_info['bare'] = False
        self.expected_info['remote_count'] = self.remote_count
        self.expected_info['branch_count'] = (self.remote_count
                                              + len(self.extra_branches)
                                              + self.local_only_branch_count)
        self.expected_info['untracked_count'] = 0
        self.expected_info['index_changes'] = False
        self.expected_info['working_tree_changes'] = False
        self.expected_info['stash'] = False
        self.expected_info['behind_count'] = sum(self.behind_each_remote_count)
        self.expected_info['fetch_status'] = read.FetchStatus.OK
        self.expected_info['ahead_count'] = sum(
            self.ahead_of_each_remote_count)

    def tearDown(self) -> None:
        super().tearDown()  # this deletes the final cloned repo
        for temp_dir in self.remote_containing_dirs:
            shutil.rmtree(temp_dir)


class TestReadRepoWithMultipleRemotes(TestReadRepoWithRemotes):
    behind_each_remote_count = [0, 0]
    ahead_of_each_remote_count = [0, 0]


class TestReadRepoWithManyRemotes(TestReadRepoWithRemotes):
    behind_each_remote_count = [0, 0, 0, 0]
    ahead_of_each_remote_count = [0, 0, 0, 0]
    extra_branches = ['dev', 'test']
    active_branch = 'dev'
    working_tree_changes = True
    untracked_count = 4
    index_changes = True
    tag_count = 2
    stash = True
    less_than_2_commits = False


class TestReadRepoAheadOfRemotes(TestReadRepoWithRemotes):
    ahead_of_each_remote_count = [3]
    less_than_2_commits = False


class TestReadRepoBehindRemotes(TestReadRepoWithRemotes):
    behind_each_remote_count = [3]


class TestReadRepoBehindManyRemotes(TestReadRepoWithRemotes):
    behind_each_remote_count = [2, 1, 3]
    ahead_of_each_remote_count = [0, 0, 0]


class TestReadRepoAheadAndBehindRemotes(TestReadRepoWithRemotes):
    ahead_of_each_remote_count = [1, 0, 1, 1]
    behind_each_remote_count = [1, 3, 1, 0]
    less_than_2_commits = False


class TestReadRepoAheadAndBehindRemotesWithLocals(TestReadRepoWithRemotes):
    ahead_of_each_remote_count = [2, 1, 0, 0]
    behind_each_remote_count = [1, 3, 1, 0]
    less_than_2_commits = True
    local_only_branch_count = 2


class TestReadRepoFailFetch(TestReadRepoWithRemotes):
    def setUp(self) -> None:
        self.ahead_of_each_remote_count = [1, 1, 0, 1]
        self.behind_each_remote_count = [1, 3, 1, 0]
        super().setUp()
        test_helpers.add_remote(self.path_to_git, "fakerepo",
                                "https://example.com/fake-repo")
        self.expected_info['fetch_status'] = (read.FetchStatus.ERROR
                                              | read.FetchStatus.OK)
        self.expected_info['remote_count'] = self.remote_count + 1
        self.less_than_2_commits = False


class TestReadRepoCloneOfEmpty(TestReadRepoWithRemotes):
    def setUp(self) -> None:
        self.commit_count = 0
        super().setUp()
        self.expected_info['branch_count'] = 0
        self.expected_info['fetch_status'] = None


class TestReadRepoCloneOfEmptyWithCommits(TestReadRepoWithRemotes):
    def setUp(self) -> None:
        self.ahead_of_each_remote_count = [2]
        self.commit_count = 0
        super().setUp()
        self.expected_info['ahead_count'] = 0
        self.expected_info['branch_count'] = 0
        self.less_than_2_commits = True
        self.total_commits = 0
        self.expected_info['fetch_status'] = None


class TestReadRepoCloneOfDetachedHead(TestReadRepoWithRemotes):
    def setUp(self) -> None:
        self.commit_count = 3
        self.detached_head = True
        super().setUp()
        self.commit_count = 0
        self.expected_info['branch_count'] = 0
        self.expected_info['fetch_status'] = None


if __name__ == '__main__':
    unittest.main()
