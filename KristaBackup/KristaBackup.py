#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys

import core
from common import Logging, arguments


def main(is_packed=True):
    """Точка входа в программу.

    Args:
        is_packed (bool, optional): Параметр, определяющий точку запуска:
        упакованный файл или исходные файлы. Стандартное значение True.

    """
    args = arguments.ArgsManager().parse_args()

    try:
        core.run(args, is_packed)
    except Exception:
        logger = Logging.get_generic_logger()
        logger.exception('Ошибка во время выполнения:')
    except BaseException:
        pass


if __name__ == '__main__':
    sys.exit(main(is_packed=False))
