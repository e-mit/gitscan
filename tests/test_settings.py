import unittest
from pathlib import Path
import shutil
import os
import uuid
import tempfile

from gitscan.scanner import settings

list_path_to_git = ['/a/b/c/d.git',
                    '/home/me/python/test/.git',
                    'the/path/to/file']
preferences = {'float_pref': 3.14, 'int_pref': 5,
         'str_pref': 'hello', 'list_pref': [9, 2.1, 'b']}


class TestSaveSettings(unittest.TestCase):
    def setUp(self) -> None:
        self.settings_dir = Path(tempfile.mkdtemp())

    def test_save_repo_list(self) -> None:
        settings.save_repo_list(self.settings_dir, list_path_to_git)
        expected_path = self.settings_dir / settings.REPO_LIST_FILENAME
        self.assertTrue(expected_path.exists())
        self.assertTrue(expected_path.is_file())

    def test_save_preferences(self) -> None:
        settings.save_preferences(self.settings_dir, preferences)
        expected_path = self.settings_dir / settings.PREFERENCES_FILENAME
        self.assertTrue(expected_path.exists())
        self.assertTrue(expected_path.is_file())

    def tearDown(self) -> None:
        shutil.rmtree(self.settings_dir)


class TestGetSettingsDirectory(unittest.TestCase):
    def test_get_settings_directory(self) -> None:
        settings_dir = settings.get_settings_directory()
        self.assertIsInstance(settings_dir, Path)
        self.assertTrue(settings_dir.parent.is_dir())


class TestLoadSettings(unittest.TestCase):
    def setUp(self) -> None:
        self.settings_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.settings_dir)

    def test_no_settings_dir(self) -> None:
        test_dir = self.settings_dir / str(uuid.uuid4())
        self.assertFalse(test_dir.exists())
        (_preferences, _list_path_to_git) = settings.load_settings(test_dir)
        self.assertIsNone(_preferences)
        self.assertIsNone(_list_path_to_git)

    def test_empty_settings_dir(self) -> None:
        test_dir = self.settings_dir / str(uuid.uuid4())
        self.assertFalse(test_dir.exists())
        os.mkdir(test_dir)
        self.assertTrue(test_dir.exists())
        (_preferences, _list_path_to_git) = settings.load_settings(test_dir)
        self.assertIsNone(_preferences)
        self.assertIsNone(_list_path_to_git)

    def test_bad_prefs_file(self) -> None:
        test_dir = self.settings_dir / str(uuid.uuid4())
        os.mkdir(test_dir)
        self.assertTrue(test_dir.exists())
        test_file = test_dir / settings.PREFERENCES_FILENAME
        with open(test_file, 'w', encoding="utf-8") as file:
            file.write("8y89kj8h=-=-k,.\n")
        self.assertTrue(test_file.exists())
        (_preferences, _list_path_to_git) = settings.load_settings(test_dir)
        self.assertIsNone(_preferences)
        self.assertIsNone(_list_path_to_git)

    def test_save_and_load_preferences(self) -> None:
        settings.save_preferences(self.settings_dir, preferences)
        (_preferences, _list_path_to_git) = settings.load_settings(
                                                    self.settings_dir)
        self.assertIsNone(_list_path_to_git)
        self.assertEqual(_preferences, preferences)

    def test_save_and_load_list_file(self) -> None:
        settings.save_repo_list(self.settings_dir, list_path_to_git)
        (_preferences, _list_path_to_git) = settings.load_settings(
                                                    self.settings_dir)
        self.assertIsNone(_preferences)
        self.assertEqual(_list_path_to_git, list_path_to_git)


if __name__ == '__main__':
    unittest.main()
