# -*- coding: utf-8 -*-

from test.docker_utils import Strategies, Tools

import pytest


@pytest.mark.tar
class TestFullDump(object):
    def test_full_dump_default(self, container):
        container = container()
        assert Strategies.run_full_dump_default(container)
        assert Tools.check_trigger_success(container)


@pytest.mark.tar
class TestDiffDump(object):

    test_key = 'test_diff_dump'

    def test_diff_dump_create_full(self, container):
        container = container()
        # создание 0 уровня, из-за его отсутствия
        assert Strategies.run_inc_dump_default(container)
        assert Tools.check_trigger_warning(container)
        pytest.shared[self.test_key] = container

    def test_diff_dump_check_warning(self, container):
        container = pytest.shared[self.test_key]

        # создание 1 уровня
        assert Strategies.run_inc_dump_default(container)
        # значение осталось WARNING, так как прошло недостаточно времени
        # чтобы этот статус устарел
        assert Tools.check_trigger_warning(container)
        # очистка триггера
        Tools.clear_trigger(container)

    def test_diff_dump_create_diff(self, container):
        container = pytest.shared[self.test_key]
        assert Strategies.run_inc_dump_default(container)
        assert Tools.check_trigger_success(container)
