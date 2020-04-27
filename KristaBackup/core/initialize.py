# -*- encoding: utf-8 -*-

import os

from common import Logging, procutil
from common.arguments.constants import (
    DISABLE_OPTS,
    ENABLE_OPTS,
    RUN_OPTS,
    STOP_OPTS,
)
from common.YamlConfig import AppConfig, ConfigError


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


def switch_choice(args):
    """Выбор запускаемого модуля.

    Модуль выбирается в зависимости от аргументов командной строки.

    Args:
        args: Namespace, аргументы командной строки.

    """
    if args.command in RUN_OPTS:
        if args.unit == 'web':
            if AppConfig.flask_on:
                webapp_handler()
            else:
                logger = Logging.get_generic_logger()
                logger.exception('Невозможно импортировать модуль flask!')
        elif args.unit == 'webapi':
            webapi_handler()
        else:
            from core import Runner
            try:
                Logging.configure_logging(args.verbose)  # TODO move to initialize
            except PermissionError as exc:
                logger = Logging.get_generic_logger()
                logger.error('Ошибка при инициализации логирования: %s', exc)
                raise BaseException
            Runner(args.unit, args.dry).start_task()
    elif args.command in STOP_OPTS:
        if args.unit == 'web':
            webapp_handler(stop=True)
        elif args.unit == 'webapi':
            webapi_handler(stop=True)
    else:
        from common.daemon_managers import crontab_manager
        if args.command in ENABLE_OPTS:
            crontab_manager.activate_task(args.unit)
        elif args.command in DISABLE_OPTS:
            crontab_manager.deactivate_task(args.unit)


def initialize(args, is_packed):
    """Инициализация приложения.

    1. Меняет рабочую директорию на необходимую.
    2. Загружает конфигурацию приложения.

    """
    AppConfig.is_packed = is_packed
    update_working_dir()
    try:
        AppConfig.set_unit_name(args.unit)
    except FileNotFoundError:
        logger = Logging.get_generic_logger()
        logger.error('Файл конфигурации не найден!')
        raise BaseException
    except ConfigError as exc:
        logger = Logging.get_generic_logger()
        logger.error('Ошибка в файле конфигураций: %s', exc)
        raise BaseException