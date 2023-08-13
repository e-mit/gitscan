import unittest
from pathlib import Path
from test_read_repo import TestReadRepo

from tests import test_helpers


class TestReadRepoWithRemotes(TestReadRepo):
    behind_each_remote_count: list[int] = []
    remote_count = 1
    ahead_count = 0
    remote_repo_base_dirs: list[Path] = []

    def setUp(self) -> None:
        super().setUp()  # Produces a new origin test repo
        self.remote_repo_base_dirs.append(Path(self.repo_base_dir))
        # Make a clone of the repo and update expected properties
        clone_repo_name = "clone1"
        (self.repo_base_dir,
         self.path_to_git) = test_helpers.create_temp_clone_git_repo(
                                self.path_to_git, clone_repo_name, bare=False)
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
        for d in self.remote_repo_base_dirs:
            test_helpers.delete_temp_directory(d)


#class TestReadBareRepoTags(TestReadRepoWithRemotes):
#    def setUp(self) -> None:
#        self.remote_count = 1
#        self.behind_each_remote_count = [2]
#        self.ahead_count = 3
#        super().setUp()


if __name__ == '__main__':
    unittest.main()
