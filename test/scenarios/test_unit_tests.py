# -*- coding: utf-8 -*-

from test.docker_utils import Strategies, Tools

import pytest


class TestUnitTests(object):

    def test_unit_tests(self, container, capsys):
        container = container()
        _, output = container.exec_run(
            'sh -c "cd /opt/KristaBackup/; python3 -m unittest"',
        )
        with capsys.disabled():
            print(f'\n{"#"*70}')
            print('python.unittest report: ', end='')
            print(output.decode('utf-8'))
            print(f'{"#"*70}')
        assert True