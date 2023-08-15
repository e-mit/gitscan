import unittest
from pathlib import Path
from random import randrange
import shutil
import os
import uuid
import tempfile

from gitscan.scanner import search
from tests import test_helpers


def create_git_directory_tree(containing_dir: Path,
                              repo_count_range: tuple[int, int],
                              subdir_count_range: tuple[int, int],
                              recursion_depth_remaining: int) -> list[Path]:
    """Randomly create git repositories and subfolders, called recursively."""
    repo_list = []
    for i in range(randrange(repo_count_range[0],
                             repo_count_range[1] + 1)):  # nosec
        repo_list.append(test_helpers.create_random_repo(containing_dir))

    if (recursion_depth_remaining > 0):
        recursion_depth_remaining -= 1
        for i in range(randrange(subdir_count_range[0],
                                 subdir_count_range[1] + 1)):  # nosec
            new_dir = containing_dir / str(uuid.uuid4())
            os.mkdir(new_dir)
            repo_list.extend(create_git_directory_tree(
                                                new_dir,
                                                repo_count_range,
                                                subdir_count_range,
                                                recursion_depth_remaining))
    return repo_list


class TestFindGitRepos(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_root_dir = Path(tempfile.mkdtemp())
        repo_count_range = (0, 3)
        subdir_count_range = (1, 3)
        recursion_depth_remaining = 6
        self.actual_repo_list = create_git_directory_tree(
                                    self.temp_root_dir,
                                    repo_count_range,
                                    subdir_count_range,
                                    recursion_depth_remaining)

    def test_search(self) -> None:
        list_path_to_git = search.find_git_repos(self.temp_root_dir)
        with self.subTest(test="length"):
            self.assertEqual(len(self.actual_repo_list), len(list_path_to_git))
        with self.subTest(test="sets"):
            self.assertEqual(set(self.actual_repo_list), set(list_path_to_git))

    def tearDown(self) -> None:
        pass
        shutil.rmtree(self.temp_root_dir)


if __name__ == '__main__':
    unittest.main()
