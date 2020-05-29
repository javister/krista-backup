# -*- encoding: utf-8 -*-

import os

from common import Logging, procutil
from common.arguments import constants
from common.daemon_managers import crontab_manager
from common.YamlConfig import AppConfig, ConfigError
from .runner import Runner
import sys


def webapp_handler(stop=False):
    """Метод для запуска и остановки веб-приложения."""
    from web.webapp.WebAppRunner import WebApp
    apprun = WebApp()
    if not stop:
        apprun.run()
    else:
        apprun.stop()


def webapi_handler(stop=False):
    """Метод для запуска и остановки веб-api."""
    from web.webapi.WebModuleRunner import WebModule
    apprun = WebModule()
    if not stop:
        apprun.run()
    else:
        apprun.stop()


def update_working_dir():
    """Меняет рабочую директорию на директорию с приложением."""
    dirpath = os.path.dirname(procutil.get_entrypoint_path())
    os.chdir(dirpath)


def _initialize_configuration(unit):
    """Инициализация конфигурации приложения для запуска задания."""
    try:
        AppConfig.set_unit_name(unit)
    except FileNotFoundError:
        logger = Logging.get_generic_logger()
        logger.error('Файл конфигурации не найден!')
        raise BaseException
    except ConfigError as exc:
        logger = Logging.get_generic_logger()
        logger.error('Ошибка в файле конфигураций: %s', exc)
        raise BaseException


def _configure_logging(verbose=False):
    try:
        Logging.configure_logging(verbose)
    except PermissionError as exc:
        logger = Logging.get_generic_logger()
        logger.error('Ошибка при инициализации логирования: %s', exc)
        raise BaseException


def _handle_run_option(args):
    _initialize_configuration(args.unit)
    _configure_logging(args.verbose)
    Runner(args.unit, args.dry).start_task()


def _handle_web_option(args):
    if args.command == constants.START_OPT_NAME:
        if args.api:
            webapi_handler()
        else:
            if AppConfig.flask_on:  # TODO исключить
                webapp_handler()
            else:
                logger = Logging.get_generic_logger()
                logger.error('Отсутствует flask.')
                raise BaseException
    elif args.command == constants.STOP_OPT_NAME:
        if args.api:
            webapi_handler(stop=True)
        else:
            if AppConfig.flask_on:  # TODO исключить
                webapp_handler(stop=True)
            else:
                logger = Logging.get_generic_logger()
                logger.error('Отсутствует flask.')
                raise BaseException
    elif args.command == 'users':
        if not AppConfig.flask_on:  # TODO исключить
            logger = Logging.get_generic_logger()
            logger.error('Отсутствует flask.')
            raise BaseException
        from web.webapp import Users
        if args.user_choice == 'list':
            for user in Users.users.values():
                print('[*]', user)
        elif args.user_choice == 'add':
            user = Users.get(args.user)
            if user:
                print('Пользователь с данным username уже существует!')
            else:
                Users.add(
                    args.user,
                    args.email,
                    args.password,
                    admin=args.admin,
                )
                print('Добавлен пользователь', args.user)
        elif args.user_choice == 'upd':
            user = Users.get(args.user)
            if user is None:
                print('Пользователь не найден.')
                sys.exit(-1)
            user.email = args.email
            user.set_password(args.password)
            if user.adm and args.no_admin:
                user.adm = False
                print('Права пользователя упразднены.')
            if not user.adm and args.admin:
                user.adm = True
                print('Пользователю даны права администратора.')
            Users.storeUser(user.id, user)
        elif args.user_choice == 'rm':
            Users.delete(args.user)
            print('Удален пользователь ', args.user)
###############################


def switch_choice(args):
    """Выбор запускаемого модуля.

    Модуль выбирается в зависимости от аргументов командной строки.

    Args:
        args: Namespace, аргументы командной строки.

    """
    if args.option == constants.RUN_OPT_NAME:
        _handle_run_option(args)
    elif args.option in constants.ENABLE_OPTS_NAME:
        crontab_manager.activate_task(args.unit)
    elif args.option in constants.DISABLE_OPTS_NAME:
        crontab_manager.deactivate_task(args.unit)
    elif args.option == 'web':
        _handle_web_option(args)
