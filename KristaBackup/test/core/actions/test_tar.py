import os
import unittest
from test import utils

from core.actions.archiver import ArchiverZip as TarArchiver


class TestActionNameGeneration(unittest.TestCase):
    """
    Проверяет генерацию пути исходного файла и всё, что
    с ней связано.

    """

    def setUp(self):
        name = utils.get_random_string()
        self.action = TarArchiver(name)

    def test_generate_dirname_with_level(self):
        random_dest_path = '/'.join(
            utils.get_random_string()
            for _ in range(3)
        )
        self.action.dest_path = random_dest_path
        self.action.level_folders = ['test']
        random_test_path = os.path.join(
            random_dest_path,
            self.action.level_folders[self.action.level],
        )
        self.assertEqual(random_test_path, self.action.generate_dirname())

    def test_generate_dirname_without_folders(self):
        random_dest_path = '/'.join(
            utils.get_random_string()
            for _ in range(3)
        )

        self.action.dest_path = random_dest_path
        self.assertEqual(random_dest_path, self.action.generate_dirname())

    def test_generate_dirname_with_chosen_level(self):
        random_dest_path = '/'.join(
            utils.get_random_string()
            for _ in range(3)
        )
        self.action.dest_path = random_dest_path
        self.action.level_folders = ['test', 'example']

        level = 1
        random_test_path = os.path.join(
            random_dest_path,
            self.action.level_folders[level],
        )
        self.assertEqual(random_test_path, self.action.generate_dirname(level=level))
