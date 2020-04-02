import unittest

from common import arguments
from argparse import Namespace


class ArgumentsTestCase(unittest.TestCase):

    def test_parse_action_record(self):
        actual = arguments.parse_action_record(['action_name', '--dry'])
        expected = Namespace(action_name='action_name', dry=True)
        self.assertEqual(actual, expected, 'Аргументы обработаны некорректно')
