# -*- encoding: utf-8 -*-

import argparse
import sys

from _version import __version__
from common import procutil

from . import constants


class ArgsManager:

    def parse_args(self):
        """Создаёт парсер и обрабатывает аргументы.

        Структура:
            KristaBackup.py run unit [--dry] [--verbose]
                            en  task
                            dis task
                            web start/stop [--api]
                                users (add,rm,upd) ...

            Общие флаги: --version, --help.
        """
        parser = argparse.ArgumentParser(
            description='Централизованная система бэкапа',
        )
        self._add_default_opts(parser)

        subparsers = parser.add_subparsers(
            metavar='<действие>',
            dest='option',
        )

        parser_run = subparsers.add_parser(
            constants.RUN_OPT_NAME,
            help='запустить задание/действие',
        )
        self._add_default_opts(parser_run)
        self._add_unit(parser_run)
        parser_run.add_argument(
            '--dry',
            action='store_true',
            help='запуск в тестовом режиме (только для действий!)',
        )

        parser_en = subparsers.add_parser(
            constants.ENABLE_OPT_NAME_ALIAS,
            help='добавить в crontab',
            aliases=(constants.ENABLE_OPT_NAME,))
        self._add_unit(parser_en, _help='имя задания или действия (или all)')

        parser_dis = subparsers.add_parser(
            constants.DISABLE_OPT_NAME_ALIAS,
            help='убрать из crontab',
            aliases=(constants.DISABLE_OPT_NAME,),
        )
        self._add_unit(parser_dis, _help='имя задания или действия (или all)')

        parser_web = subparsers.add_parser('web', help='настроить веб-модуль')
        self._add_default_opts(parser_web)
        self._add_api(parser_web)

        web_subparsers = parser_web.add_subparsers(
            title='web',
            dest='command',
            metavar='<команда>',
        )

        start_web_parser = web_subparsers.add_parser(
            constants.START_OPT_NAME,
            help='запустить веб-сервер',
        )
        self._add_default_opts(start_web_parser)
        self._add_api(start_web_parser)

        stop_web_parser = web_subparsers.add_parser(
            constants.STOP_OPT_NAME,
            help='остановить веб-сервер',
        )
        self._add_default_opts(stop_web_parser)
        self._add_api(stop_web_parser)

        users_parser = web_subparsers.add_parser(
            'users',
            help='работа с пользователями',
        )
        self._configure_users_parser(users_parser)

        args = parser.parse_args()
        self.check_required(args, parser)

        return args

    def _add_default_opts(self, parser):
        parser.add_argument(
            '--verbose',
            '-v',
            action='store_true',
            help='логгирование в консоль во время выполнения',
        )
        parser.add_argument(
            '--version',
            action='version',
            version='{prog} {version}'.format(
                prog=procutil.get_executable_filename(),
                version=__version__,
            ),
            help='вывести версию программы',
        )

    def _add_unit(self, parser, _help=None):
        parser.add_argument(
            metavar='unit',
            dest='unit',
            type=str,
            help=_help or 'имя задания или действия',
        )

    def _add_api(self, parser):
        parser.add_argument(
            '--api',
            action='store_true',
            help='управлять web-api',
        )

    def _configure_users_parser(self, parser):
        subparsers = parser.add_subparsers(
            metavar='<действие>',
            dest='user_choice',
        )
        add_parser = subparsers.add_parser('list', help='список пользователей')

        add_parser = subparsers.add_parser('add', help='добавить пользователя')
        self._add_user_args(add_parser)

        add_parser = subparsers.add_parser('upd', help='обновить пользователя')
        self._add_user_args(add_parser)

        add_parser = subparsers.add_parser('rm', help='удалить пользователя')
        self._add_user_args(add_parser, username_only=True)

    def _add_user_args(self, parser, username_only=False):
        parser.add_argument('user', help='имя пользователя')
        if username_only:
            return
        parser.add_argument('email', help='почтовый адрес')
        parser.add_argument('password', help='пароль')

        adm_group = parser.add_mutually_exclusive_group()
        adm_group.add_argument(
            '--plain',
            action='store_true',
            dest='no_admin',
            help='назначить стандартные права (default)',
        )
        adm_group.add_argument(
            '--admin',
            action='store_true',
            dest='admin',
            help='назначить права администратора',
        )

    def check_required(self, args, parser):
        # TODO нужная опция появилась в python3.7+
        required = []
        if not args.option:  # первый аргумент
            required.append('<действие>')

        if args.option == 'web':
            if not args.command:
                required.append('<команда> для web')
            else:
                if args.command == 'users':
                    if not args.user_choice:
                        required.append('<действие> для users')

        if not required:
            return
        parser.exit(
            2,
            '{0} error: the following arguments are required: {1}\n'.format(
                parser.prog,
                ', '.join(required),
            ),
        )


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
