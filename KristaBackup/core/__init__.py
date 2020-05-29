# -*- encoding: utf-8 -*-

"""__init__ модуль пакета core.

Содержит импорты исполняемых ресурсов, а также содержит правки,
необходимые для поддержки более старых версий Python.

"""

from .initialize import switch_choice, update_working_dir

try:
    FileNotFoundError = FileNotFoundError
except NameError:
    __builtins__['FileNotFoundError'] = EnvironmentError

try:
    PermissionError = PermissionError
except NameError:
    __builtins__['PermissionError'] = EnvironmentError


def run(args):
    update_working_dir()
    switch_choice(args)
