#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys

import core
from common import Logging, arguments


def main():
    """Точка входа в программу."""
    args = arguments.ArgsManager().parse_args()
    try:
        core.run(args)
    except Exception:
        logger = Logging.get_generic_logger()
        logger.exception('Ошибка во время выполнения:')
    except BaseException:
        pass


if __name__ == '__main__':
    sys.exit(main())
