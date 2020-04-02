# -*- encoding: utf-8 -*-

"""__init__ модуль пакета core.

Содержит импорты исполняемых ресурсов, а также содержит правки,
необходимые для поддержки более старых версий Python.

"""

from .runner import Runner
from .executor import executor


try:
    FileNotFoundError = FileNotFoundError
except NameError:
    __builtins__['FileNotFoundError'] = IOError
