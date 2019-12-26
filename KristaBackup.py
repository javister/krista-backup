#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import os
import time
import logging


def handle_unexpected_exception(exception):
    """Обработчик ошибок на этапе инициализации.

    Нужен для того, чтобы инициализировать логгирование
    максимально быстро, вывести ошибку и завершить выполнение.

    """
    from model.Logging import configure_logger
    logger = configure_logger('error', verbose=True)
    logger.error('Ошибка во время импорта зависимостей: %s', exception)
    exit(2)


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
        help='требуемое действие',
    )
    parser.add_argument(
        metavar='задание',
        dest='entity',
        type=str,
        help='имя задания (en/dis поддерживают all) или web_module',
    )
    parser.add_argument('--verbose', '-v', action='store_true')
    return parser.parse_args()


def get_entrypoint_path(is_packed):
    """Возвращает путь к исполняемому файлу."""
    dirpath = os.path.realpath(__file__)
    if is_packed:
        dirpath = os.path.dirname(dirpath)
    return dirpath


def main(is_packed=True):
    """Точка входа программы.

    Attributes:
        is_packed (bool, optional): Параметр, определяющий точку запуска:
        упакованный файл или исходные файлы. Стандартное значение True.

    """
    dirpath = os.path.dirname(get_entrypoint_path(is_packed))
    os.chdir(dirpath)

    try:
        from web.app import WebModule
        from runner.ScheduleRunner import ScheduleRunner
    except Exception as exc:
        handle_unexpected_exception(exc)

    args = parse_args()
    if args.action == 'run':
        if args.entity == 'web_module':
            pid = os.fork()
            if pid == 0:
                time.sleep(1)
                try:
                    WebModule.run()
                except Exception:
                    logging.exception('Исключение при запуске веб модуля:')
        else:
            try:
                ScheduleRunner(args.entity, args.verbose).start_task()
            except Exception:
                logging.exception('Исключение при выполнении задания:')
    elif args.action == 'stop':
        if args.entity == 'web_module':
            WebModule.stop()
    else:
        from model.Tasks import activate_task, deactivate_task

        if args.action in {'enable', 'en'}:
            activate_task(args.entity, get_entrypoint_path(is_packed))
        elif args.action in {'disable', 'dis'}:
            deactivate_task(args.entity)


if __name__ == '__main__':
    main(is_packed=False)
