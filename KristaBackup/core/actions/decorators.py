# -*- encoding: utf-8 -*-

"""Модуль содержит декораторы для действий."""

import functools


def side_effecting(method):
    """Декоратор для методов, изменяющих состояние системы.

    Нужен для пропуска потенциально опасных методов
    во время dry-run выполнения.

    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwords):
        if self.dry:
            return lambda: None
        return method(self, *args, **kwords)
    return wrapper
