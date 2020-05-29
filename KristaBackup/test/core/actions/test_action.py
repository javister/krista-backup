import os
import re
import unittest
from test import utils
from test.utils import AppConfig

from core.actions.action import Action, _generate_random_basename

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
