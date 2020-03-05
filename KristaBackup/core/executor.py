# -*- encoding: utf-8 -*-

import os

from common import Logging, procutil
from common.arguments.constants import (
    DISABLE_OPTS,
    ENABLE_OPTS,
    RUN_OPTS,
    STOP_OPTS,
)
from common.YamlConfig import AppConfig


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


def executor(args):
    logger = Logging.get_generic_logger()
    update_working_dir()

    if args.command in RUN_OPTS:
        if args.unit == 'web':
            if AppConfig.flask_on:
                try:
                    webapp_handler()
                except Exception:
                    logger.exception('Исключение при запуске веб-приложения')
            else:
                logger.exception(
                    'Исключение при запуске веб-приложения: невозможно импортировать модуль flask')
        elif args.unit == 'webapi':
            try:
                webapi_handler()
            except Exception:
                logger.exception('Исключение при запуске веб-api')
        else:
            try:
                from core import Runner
                Runner(args.unit, args.verbose, args.dry).start_task()
            except Exception:
                logger.exception('Исключение при запуске задания')
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
