import os
import re
import unittest
from test import utils
from test.utils import AppConfig

from core.actions.action import Action, _generate_random_basename


class TestActionNameGeneration(unittest.TestCase):
    """
    Проверяет генерацию пути исходного файла и всё, что
    с ней связано.

    """

    def setUp(self):
        name = utils.get_random_string()
        self.action = Action(name)

    def test_generate_dirname(self):
        random_test_path = '/'.join(
            utils.get_random_string()
            for _ in range(3)
        )
        self.action.dest_path = random_test_path
        self.assertEqual(random_test_path, self.action.generate_dirname())

    def test_generate_filename_with_ext(self):
        test_name = utils.get_random_string()
        time_suffix = AppConfig.get_starttime_str()
        ext = 'list'
        filename = self.action.generate_filename(
            test_name,
            time_suffix,
            ext,
        )
        expected = '{0}-{1}-{2}.{3}'.format(
            self.action.basename,
            test_name,
            time_suffix,
            ext,
        )
        self.assertEqual(
            expected,
            filename,
        )

    def test_generate_filename_without_ext(self):
        test_name = utils.get_random_string()
        time_suffix = AppConfig.get_starttime_str()
        filename = self.action.generate_filename(
            test_name,
            time_suffix,
        )
        expected = '{0}-{1}-{2}'.format(
            self.action.basename,
            test_name,
            time_suffix,
        )
        self.assertEqual(
            expected,
            filename,
        )

    def test_generate_filename_invalid_ext(self):
        test_name = utils.get_random_string()
        time_suffix = AppConfig.get_starttime_str()
        ext = 123

        with self.assertRaises(TypeError):
            self.action.generate_filename(
                test_name,
                time_suffix,
                ext,
            )

    def test_generate_filename_invalid_name(self):
        test_name = 123
        time_suffix = AppConfig.get_starttime_str()
        ext = utils.get_random_string()

        with self.assertRaises(TypeError):
            self.action.generate_filename(
                test_name,
                time_suffix,
                ext,
            )

    def test_generate_filepath_without_name(self):
        ext = utils.get_random_string()
        random_test_path = '/'.join(
            utils.get_random_string()
            for _ in range(3)
        )
        self.action.dest_path = random_test_path
        filepath = self.action.generate_filepath(
            None,
            ext,
        )
        expected = os.path.join(
            random_test_path,
            '{0}-{1}.{2}'.format(
                self.action.basename,
                AppConfig.get_starttime_str(),
                ext,
            ),
        )

        self.assertEqual(expected, filepath)

    def test_generate_filepath_without_ext(self):
        test_name = utils.get_random_string()
        random_test_path = '/'.join(
            utils.get_random_string()
            for _ in range(3)
        )
        self.action.dest_path = random_test_path

        filepath = self.action.generate_filepath(test_name, None)
        expected = os.path.join(random_test_path, '{0}-{1}-{2}'.format(
            self.action.basename,
            test_name,
            utils.AppConfig._start_time_str,
        ))
        self.assertEqual(expected, filepath)

    def test_generate_filepath_with_empty_ext(self):
        test_name = utils.get_random_string()
        extension = ''
        random_test_path = '/'.join(
            utils.get_random_string()
            for _ in range(3)
        )
        self.action.dest_path = random_test_path

        filepath = self.action.generate_filepath(test_name, extension='')
        expected = os.path.join(random_test_path, '{0}-{1}-{2}'.format(
            self.action.basename,
            test_name,
            utils.AppConfig._start_time_str,
        ))
        self.assertEqual(expected, filepath)


class TestActionDryProperty(unittest.TestCase):
    """
    Тестирует работу параметра dry.

    """

    def setUp(self):
        name = utils.get_random_string()
        self.action = Action(name)

    def test_default_value(self):
        self.assertFalse(self.action.dry)

    def test_switch_on(self):
        self.action.dry = True

        self.assertTrue(self.action.dry)
        self.assertIn(self.action.DRYRUN_POSTFIX, self.action.logger.name)

    def test_switch_back(self):
        self.action.dry = True
        self.action.dry = False

        self.assertTrue(self.action.dry)
        self.assertIn(self.action.DRYRUN_POSTFIX, self.action.logger.name)


class TestActionMatcherGenerator(unittest.TestCase):
    """
    Тестирует фабри
    """

    def setUp(self):
        name = utils.get_random_string()
        self.action = Action(name)

    def test_unix_wildcards_matcher(self):
        _pattern = '*l[abdcio]st.sh'
        _test = '/etc/last.sh'

        matcher = self.action.get_pattern_matcher()
        self.assertTrue(matcher(_pattern, _test))

    def test_re_matcher(self):
        """
        В реализации используется дефолтный матчер, поэтому
        достаточно их просто сравнить.
        """
        self.action.use_re_in_patterns = True
        matcher = self.action.get_pattern_matcher()
        self.assertEqual(re.match, matcher)


class TestActionCmdExcecution(unittest.TestCase):

    def setUp(self):
        name = utils.get_random_string()
        self.action = Action(name)

    def test_return_std_as_str(self):
        test_data = utils.get_random_string()

        payload = 'echo "{0}"'.format(test_data)

        return_data = self.action.execute_cmdline(
            cmdline=payload,
            return_stdout=True,
        )[:-1]
        self.assertEqual(test_data, return_data)


class TestRandomBasename(unittest.TestCase):

    def test_basename(self):
        _pattern = '[a-zA-Z0-9_]{1,}$'
        for _ in range(0, 3):
            basename = _generate_random_basename()
            self.assertTrue(re.match(_pattern, basename))
