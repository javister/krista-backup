# -*- encoding: utf-8 -*-

"""__init__ модуль пакета core.

Содержит импорты исполняемых ресурсов, а также содержит правки,
необходимые для поддержки более старых версий Python.

"""

from .runner import Runner
from .initialize import initialize, switch_choice


try:
    FileNotFoundError = FileNotFoundError
except NameError:
    __builtins__['FileNotFoundError'] = IOError

try:
    PermissionError = PermissionError
except NameError:
    __builtins__['PermissionError'] = IOError

def run(args, is_packed):
    initialize(args, is_packed)
    switch_choice(args)
