# -*- coding: UTF-8 -*-

import fnmatch
import functools
import logging
import os
import re
import subprocess
import uuid
from threading import Thread

from common.YamlConfig import AppConfig

from .decorators import side_effecting


class Action:
    """Абстрактный класс действия.

    Attributes:
        name: Строка, уникальное имя действия.
        src_path: Строка, путь к исходным файлам.
        dest_path: Строка, путь к выходным файлам.

        basename: Строка, не должна быть началом другого basename.
        Используется для связи сопряжённых действий.
        (Например, tar и cleaner для одного набора файлов)

        use_re_in_patterns: Логическое значение, если True, то паттерны
        regexp, иначе shell.

        continue_on_error: Логическое значение, определяет стоит ли продолжать
        выполнение после провала текущего действия.

        dry: Логическое значение, включает тестовый режим.

    """

    required_attrs = {'name'}  # набор обязательных атрибутов

    DRYRUN_POSTFIX = 'DRYRUN'

    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(name)

        self.basename = _generate_random_basename()
        self.src_path = '.'
        self.dest_path = '.'

        self.use_re_in_patterns = False
        self.continue_on_error = False
        self._dry = False

    @property
    def dry(self):
        return self._dry

    @dry.setter
    def dry(self, dry):
        if not self._dry and dry:
            self._dry = dry
            self.logger.name = '{0}_{1}'.format(
                self.logger.name,
                self.DRYRUN_POSTFIX,
            )

    def get_pattern_matcher(self):
        """Возвращает функцию для проверки паттернов и исключений.

        Returns:
            _matcher(pattern, name): функция, для проверки паттернов.

        """
        if self.use_re_in_patterns:
            _matcher = re.match
        else:
            @functools.wraps(fnmatch.fnmatch)
            def _matcher(*args):
                return fnmatch.fnmatch(*args[::-1])
        return _matcher

    def generate_filepath(self, name, extension):
        """Генерирует путь к выходному файлу.

        Args:
            name: Строка или None
            extension: Строка или None

        """
        time_suffix = AppConfig.get_starttime_str()
        dirname = self.generate_dirname()

        filename = self.generate_filename(name, time_suffix, extension)
        return os.path.join(dirname, filename)

    def generate_dirname(self):
        """Возвращает имя для выходной директории."""
        return self.dest_path

    def generate_filename(self, name, time_suffix, extension=None):
        """Возвращает имя для выходного файла."""
        parts = [self.basename, name, time_suffix]
        _name = '-'.join(
            [part for part in parts if part is not None],
        )
        if extension:
            return '.'.join([_name, extension])
        return _name

    @staticmethod
    def stream_watcher_filtered(
        stream,
        logger,
        filters=None,
        remove_header=False,
        default_level=None,
    ):
        """Наблюдатель за потоком данных.

        Args:
            stream: читаемый поток с данными
            filters (dict): словарь с фильтрами вида
                { log_level (int) : [pat1 (str), pat2 (str)], ... }
            remove_header (bool): удалять первое слово в строке
            default_level (int): стандартный уровень логгирования.

        """
        default_level = default_level or logging.NOTSET
        filters = filters or {}

        filter_tuples = [
            (pattern, status) for status, patterns in filters.items()
            for pattern in patterns
        ]

        try:
            for line in stream:
                line = line.strip()
                if remove_header and ' ' in line:
                    # удаление первого слова из строки, если оно не последнее
                    words = line.split()[1:]
                    line = ' '.join(words)

                if not line:
                    break

                for pattern, log_level in filter_tuples:
                    if re.match(pattern, line):
                        logger.log(level=log_level, msg=line)
                        break
                else:
                    logger.log(level=default_level, msg=line)
        except UnicodeDecodeError:
            logger.exception('Encoding in the output is corrupted :(')

        if not stream.closed:
            stream.close()

    def walk_apply(self, src, apply, recursive=True, apply_dirs=False):
        """Метод проходит по файлам и применяет к ним apply.

        На время выполнения меняет текущую директорию на src. По умолчанию
        проход рекурсивный.

        Args:
            src: Строка, исходная директория.
            apply: Функция, принимает файл/строку.
            recursive: Логическое значение, задаёт рекурсивный обход.
            apply_dirs: Логическое значение, обработка и директории.

        """
        if not os.path.isdir(src):
            raise AttributeError(
                'директория src не существует: {0}'.format(src),
            )

        self.logger.debug('Меняю текущую директорию на %s', src)
        current_dir = os.getcwd()
        os.chdir(src)

        walker = (
            (dirpath[2:], filenames)
            for dirpath, _, filenames in os.walk('.')
        )
        if not recursive:
            walker = [next(walker)]
        for (dirpath, filenames) in walker:
            if apply_dirs and dirpath.strip():
                apply(dirpath)
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                apply(filepath)
        self.logger.info('Обход файлов в директории %s завершён', src)
        self.logger.debug(
            'Возвращаю исходную рабочую директорию %s',
            current_dir,
        )
        os.chdir(current_dir)

    def execute_cmdline(
        self,
        cmdline,
        return_stdout=False,
        stdout_params=None,
        stderr_params=None,
    ):
        """Выполняет cmdline.

        Args:
            cmdline: Строка, которую следует выполнить в консоли
            return_stdout: Логическое значение, не использовать наблюдателей,
                после выполнения вернуть содержимое stdout.
            stdout_params: Словарь, параметры для наблюдателя за stdout вида
            {'default_level': logging.<LEVEL>, 'remove_header': <bool>, 'filters': <dict>}
            stderr_params: Словарь, параметры для наблюдателя за stderr вида
            {'default_level': logging.<LEVEL>, 'remove_header': <bool>, 'filters': <dict>}

        Формат filters можно найти в описании к stream_watcher_filtered.
        """
        process = subprocess.Popen(
            cmdline,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        )
        if return_stdout:
            process.wait()
            value = process.stdout.read()
            process.stdout.close()
            process.stderr.close()
            return value

        stdout_params['stream'] = process.stdout
        stdo = Thread(
            target=self.stream_watcher_filtered,
            name='stdout-watcher',
            kwargs=stdout_params,
        )

        stderr_params['stream'] = process.stderr
        stde = Thread(
            target=self.stream_watcher_filtered,
            name='stderr-watcher',
            kwargs=stderr_params,
        )
        stdo.start()
        stde.start()
        process.wait()
        stdo.join()
        stde.join()

        return None

    unsafe_execute_cmdline = classmethod(execute_cmdline)
    """Unsafe версия execute_cmdline."""

    execute_cmdline = side_effecting(execute_cmdline)

    def __repr__(self):
        return '{name}: {attrs}'.format(
            name=self.__class__.__name__,
            attrs=self.__dict__,
        )

    def start(self):
        """Абстрактный метод, запускает выполнение действия.

        Returns:
            False, если нужно прервать цепочку обработки.

        """
        raise NotImplementedError('Should have implemented this')


def _generate_random_basename():
    """Генерирует случайный basename."""
    return uuid.uuid4().hex.upper()[0:6]
