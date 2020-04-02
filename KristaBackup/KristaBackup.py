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
    args = arguments.ArgsManager(is_packed).process_args()

    try:
        import core
        core.executor(args)
    except Exception:
        logger.exception('Ошибка во время выполнения')


if __name__ == '__main__':
    main(is_packed=False)
