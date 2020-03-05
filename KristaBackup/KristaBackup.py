#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys

from common import Logging, arguments


def main(is_packed=True):
    """Точка входа в программу.

    Args:
        is_packed (bool, optional): Параметр, определяющий точку запуска:
        упакованный файл или исходные файлы. Стандартное значение True.

    """
    logger = Logging.get_generic_logger()
    if sys.version_info < (3, 5):
        logger.warning('Приложение может работать не стабильно!')
        logger.warning(
            'Для запуска требуется версия python3 >= 3.5 (current: %s)',
            '.'.join(map(str, sys.version_info[:3])),
        )
    try:
        args = arguments.ArgsManager(is_packed).process_args()
    except Exception:
        logger.exception('Ошибка во время обработки аргументов')

    try:
        import core
        core.executor(args)
    except Exception:
        logger.exception('Ошибка во время выполнения')


if __name__ == '__main__':
    main(is_packed=False)
