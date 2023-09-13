import unittest
from pathlib import Path
from random import randrange, sample
import shutil
import os
import uuid
import tempfile

from gitscan.scanner import search
from tests import test_helpers


def create_git_directory_tree(containing_dir: Path,
                              repo_count_range: tuple[int, int],
                              subdir_count_range: tuple[int, int],
                              recursion_depth_remaining: int
                              ) -> tuple[list[Path], list[Path]]:
    """Randomly create git repositories and subfolders, called recursively.

    This does not create git submodules (repo inside repo).
    """
    repo_list = []
    dir_list = []  # all directories, excluding git directories
    for i in range(randrange(repo_count_range[0],
                             repo_count_range[1] + 1)):  # nosec
        repo_list.append(test_helpers.create_random_repo(containing_dir))

    if (recursion_depth_remaining > 0):
        recursion_depth_remaining -= 1
        for i in range(randrange(subdir_count_range[0],
                                 subdir_count_range[1] + 1)):  # nosec
            new_dir = containing_dir / str(uuid.uuid4())
            dir_list.append(new_dir)
            os.mkdir(new_dir)
            (r_list, d_list) = create_git_directory_tree(
                new_dir,
                repo_count_range,
                subdir_count_range,
                recursion_depth_remaining)
            repo_list.extend(r_list)
            dir_list.extend(d_list)
    return (repo_list, dir_list)


class TestFindGitRepos(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root_dir = Path(tempfile.mkdtemp())
        repo_count_range = (0, 3)
        subdir_count_range = (1, 3)
        recursion_depth_remaining = 6
        (repo_list, self.actual_dir_list) = create_git_directory_tree(
            self.temp_root_dir,
            repo_count_range,
            subdir_count_range,
            recursion_depth_remaining)
        self.actual_repo_list = [str(x) for x in repo_list]

    def test_search(self) -> None:
        list_path_to_git = search.find_git_repos(self.temp_root_dir)
        with self.subTest(test="length"):
            self.assertEqual(len(self.actual_repo_list), len(list_path_to_git))
        with self.subTest(test="sets"):
            self.assertEqual(set(self.actual_repo_list), set(list_path_to_git))

    def test_search_with_exclude(self) -> None:
        # Randomly choose 1/3 of the directories to exclude:
        exclude_dirs = sample(self.actual_dir_list,
                              int(len(self.actual_dir_list) / 3))
        expected_list = []
        for repo_dir in self.actual_repo_list:
            if not any(str(ex) in repo_dir for ex in exclude_dirs):
                expected_list.append(repo_dir)

        list_path_to_git = search.find_git_repos(self.temp_root_dir,
                                                 exclude_dirs)
        with self.subTest(test="length"):
            self.assertEqual(len(expected_list), len(list_path_to_git))
        with self.subTest(test="sets"):
            self.assertEqual(set(expected_list), set(list_path_to_git))

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_root_dir)


if __name__ == '__main__':
    unittest.main()
