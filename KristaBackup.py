#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import os
import time

from model.Logging import configure_generic_logger
from model.YamlConfig import AppConfig


def check_and_create_files():

    pass

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


class WebModule(object):
    pass


def main(is_packed=True):
    """
    Точка входа программы.

    Attributes:
        is_packed (bool, optional): Параметр, определяющий точку запуска:
        упакованный файл или исходные файлы. Стандартное значение True.

    """
    dirpath = os.path.dirname(get_entrypoint_path(is_packed))
    os.chdir(dirpath)

    lgr = configure_generic_logger()
    lgr.info('Парсим входные параметры')
    args = parse_args()
    if args.action == 'run':
        if args.entity == 'web':
            if not AppConfig.flask_on:
                lgr.exception('Исключение при запуске веб-приложения: невозможно импортировать модуль flask')
            else:
                try:
                    from webapp.WebAppRunner import WebApp
                    apprun = WebApp()
                    apprun.run()
                except Exception as e:
                    lgr.exception('Исключение при запуске веб-приложения', e)
        elif args.entity == 'webapi':
            try:
                from webapp.WebModuleRunner import WebModule
                apprun = WebModule()
                apprun.run()
            except Exception as e:
                lgr.exception('Исключение при запуске веб-api', e)
        else:
            try:
                from runner import ScheduleRunner
                ScheduleRunner(args.entity, args.verbose).start_task()
            except Exception as e:
                lgr.exception('Исключение при выполнении задания', e)
    elif args.action == 'stop':
        if args.entity == 'web':
                from webapp.WebAppRunner import WebApp
                appstop = WebApp()
                appstop.stop()
        elif args.entity == 'webapi':
                from webapp.WebModuleRunner import WebModule
                appstop = WebModule()
                appstop.stop()
    else:
        from model.Schedules import activate_schedule, deactivate_schedule
        if args.action in {'enable', 'en'}:
            activate_schedule(args.entity, get_entrypoint_path(is_packed))
        elif args.action in {'disable', 'dis'}:
            deactivate_schedule(args.entity)


if __name__ == '__main__':
    main(is_packed=False)

