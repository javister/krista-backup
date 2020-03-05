# -*- encoding: utf-8 -*-

import argparse

from _version import __version__
from common.YamlConfig import AppConfig

from .constants import ALL, ARGS_ACTION_OPTS, DISABLE_OPTS, ENABLE_OPTS


class ArgsManager(object):

    def __init__(self, is_packed):
        self.is_packed = is_packed

    def process_args(self):
        """Обработка аргументов командной строки и инициализация AppConfing."""
        AppConfig.is_packed = self.is_packed

        return self._parse_args()

    def _parse_args(self):
        """Обработка параметров командной строки."""
        parser = argparse.ArgumentParser(
            description='Централизованная система бэкапа',
        )
        parser.add_argument(
            metavar='команда',
            dest='command',
            type=str,
            choices=ARGS_ACTION_OPTS,
            help='требуемая команда ({opts})'.format(opts=ARGS_ACTION_OPTS),
        )
        parser.add_argument(
            metavar='задание/действие',
            dest='unit',
            type=str,
            help='имя задания/действия ({en} и {dis} поддерживают {all}) или web для запуска веб-интерфейса'
            .format(en=ENABLE_OPTS, dis=DISABLE_OPTS, all=ALL),
        )
        parser.add_argument(
            '--dry',
            action='store_true',
            help='запуск в тестовом режиме (только для действий!)',
        )
        parser.add_argument(
            '--verbose',
            '-v',
            action='store_true',
            help='выводить продробный лог в консоль во время выполнения',
        )
        parser.add_argument(
            '--version',
            action='version',
            version='%(prog)s {0}'.format(__version__),
            help='вывод программной версии и выход',
        )
        return parser.parse_args()


def parse_action_record(action_record):
    """Обработка записи действия в описании задания.

    Используется в случаях, когда действие задано в формате списка.
    Например: ['action_name', '--dry']

    Args:
        action_record (list): описание вызова действия

    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        metavar='действие',
        dest='action_name',
        type=str,
    )
    parser.add_argument('--dry', action='store_true')
    return parser.parse_args(action_record)
