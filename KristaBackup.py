#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import os

from model.Logging import configure_generic_logger
from model.YamlConfig import AppConfig


def parse_args():
    """Обработчик параметров командной строки."""
    parser = argparse.ArgumentParser(
        description='Централизованная система бэкапа',
    )
    parser.add_argument(
        metavar='действие',
        dest='action',
        type=str,
        choices=['run', 'stop', 'enable', 'en', 'disable', 'dis'],
        help="требуемое действие ('run', 'stop', 'enable/en', 'disable/dis')",
    )
    parser.add_argument(
        metavar='задание',
        dest='entity',
        type=str,
        help='имя задания (en/dis поддерживают all) или web для запуска веб-интерфейса',
    )
    parser.add_argument('--verbose', '-v', action='store_true')
    return parser.parse_args()


def get_entrypoint_path(is_packed):
    """Возвращает путь к исполняемому файлу."""
    dirpath = os.path.realpath(__file__)
    if is_packed:
        dirpath = os.path.dirname(dirpath)
    return dirpath


def webapp_handler(stop=False):
    """Метод для запуска и остановки веб-приложения."""
    from webapp.WebAppRunner import WebApp
    apprun = WebApp()
    if not stop:
        apprun.run()
    else:
        apprun.stop()


def webapi_handler(stop=False):
    """Метод для запуска и остановки веб-api."""
    from webapp.WebModuleRunner import WebModule
    apprun = WebModule()
    if not stop:
        apprun.run()
    else:
        apprun.stop()


def main(is_packed=True):
    """Точка входа в программу.

    Attributes:
        is_packed (bool, optional): Параметр, определяющий точку запуска:
        упакованный файл или исходные файлы. Стандартное значение True.

    """
    excecutable_path = get_entrypoint_path(is_packed)
    AppConfig.excecutable_path = excecutable_path

    dirpath = os.path.dirname(excecutable_path)
    os.chdir(dirpath)

    args = parse_args()
    if args.action == 'run':
        if args.entity == 'web':
            if not AppConfig.flask_on:
                lgr = configure_generic_logger()
                lgr.exception('Исключение при запуске веб-приложения: невозможно импортировать модуль flask')
            else:
                try:
                    webapp_handler()
                except Exception:
                    lgr = configure_generic_logger()
                    lgr.exception('Исключение при запуске веб-приложения')
        elif args.entity == 'webapi':
            try:
                webapi_handler()
            except Exception:
                lgr = configure_generic_logger()
                lgr.exception('Исключение при запуске веб-api')
        else:
            try:
                from runner import ScheduleRunner
                ScheduleRunner(args.entity, args.verbose).start_task()
            except Exception:
                lgr = configure_generic_logger()
    elif args.action == 'stop':
        if args.entity == 'web':
            webapp_handler(stop=True)
        elif args.entity == 'webapi':
            webapi_handler(stop=True)
    else:
        from model.Schedules import activate_task, deactivate_task
        if args.action in {'enable', 'en'}:
            activate_task(args.entity)
        elif args.action in {'disable', 'dis'}:
            deactivate_task(args.entity)


if __name__ == '__main__':
    main(is_packed=False)
