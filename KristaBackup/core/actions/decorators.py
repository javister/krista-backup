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


def use_levels(cls):
    """Декоратор класса.

    Добавляет атрибуты для работы с уровнями бэкапа.
    """
    method = cls.__init__
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        self.level = 0
        self.level_folders = ['0', '1']
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


def use_periods(cls):
    """Декоратор класса.

    Добавляет атрибуты для работы с периодами.
    """
    method = cls.__init__
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        self.basename_list = []
        self.periods = {}
        return method(self, *args, **kwargs)
    cls.__init__ = wrapper
    return cls


def use_postgres(cls):
    """Декоратор класса.

    Добавляет атрибуты для работы с бэкапом postgres.
    """
    method = cls.__init__
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        self.host = None
        self.port = 5432
        self.user = None
        self.password = None
        self.databases = []
        return method(self, *args, **kwargs)
    cls.__init__ = wrapper
    return cls
