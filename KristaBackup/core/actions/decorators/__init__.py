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
            return None
        return method(self, *args, **kwords)

    return wrapper


def use_exclusions(cls):
    """Декоратор класса.

    Добавляет атрибуты для работы с исключениями.
    """
    method = cls.__init__
    @functools.wraps(cls.__init__)
    def wrapper(self, *args, **kwargs):
        self.exclusions = []
        self.prepared_exclusions = []
        return method(self, *args, **kwargs)
    cls.__init__ = wrapper
    return cls

def use_patterns(cls):
    """Декоратор класса.

    Добавляет атрибуты для работы с паттернами.
    """
    method = cls.__init__
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        self.patterns = []
        self.prepared_patterns = []
        return method(self, *args, **kwargs)
    cls.__init__ = wrapper
    return cls
