import unittest
from pathlib import Path
from test_read_repo import TestReadRepo

from tests import test_helpers


class TestReadRepoWithRemotes(TestReadRepo):
    remote_count = 1
    ahead_count = 0

    def setUp(self) -> None:
        super().setUp()  # Produces a new origin test repo
        self.behind_each_remote_count: list[int] = []
        self.remote_repo_base_dirs: list[Path] = []
        self.remote_repo_git_path: list[Path] = []
        clone_repo_name = ""
        for clone_count in range(self.remote_count):
            # save the previous temp directory so it can be deleted/remoted:
            self.remote_repo_base_dirs.append(Path(self.repo_base_dir))
            self.remote_repo_git_path.append(Path(self.path_to_git))
            # Make a new clone
            clone_repo_name = f"clone{clone_count}"
            (self.repo_base_dir,
             self.path_to_git) = test_helpers.create_temp_clone_git_repo(
                                    self.path_to_git, clone_repo_name,
                                    bare=False)
            # set all previous repos as remotes:
            for rc in range(clone_count):
                test_helpers.add_remote(self.path_to_git, f"remote{rc}",
                                        self.remote_repo_git_path[rc])

        self.expected_info['name'] = clone_repo_name
        self.expected_info['path'] = self.repo_base_dir
        # the following properties apply to clones, irrespective of origin:
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
        for temp_dir in self.remote_repo_base_dirs:
            test_helpers.delete_temp_directory(temp_dir)


class TestReadRepoWithMultipleRemotes(TestReadRepoWithRemotes):
    def setUp(self) -> None:
        self.remote_count = 2
        super().setUp()


class TestReadRepoWithManyRemotes(TestReadRepoWithRemotes):
    def setUp(self) -> None:
        self.remote_count = 4
        self.extra_branches = ['dev', 'test']
        self.active_branch = 'dev'
        self.working_tree_changes = True
        self.untracked_count = 4
        self.index_changes = True
        self.tag_count = 2
        self.stash = True
        super().setUp()


if __name__ == '__main__':
    unittest.main()
