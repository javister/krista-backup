# -*- coding: UTF-8 -*-

import fnmatch
import logging
import re
import subprocess
import uuid
from threading import Thread

from .decorators import side_effecting
from .utils import create_sha1sum_file


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

    DRYRUN_POSTFIX = 'DRYRUN'

    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(name)
        self.source = None

        self.basename = _generate_random_basename()
        self.scheme = None

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

    def prepare_pattern(self, pattern):
        """Обработка первичных паттернов.

        Args:
            pattern: Строка. Если use_re_in_patterns is True,
                то считается, что паттерн имеет формат shell и
                переводится в формат regex.

        Returns:
            Строку, готовый к использованию/компиляции паттерн.

        """
        pattern = pattern.strip()
        if self.use_re_in_patterns:
            return pattern
        translated = fnmatch.translate(pattern)
        if translated.endswith('(?ms)'):
            translated = translated[:-5]
        if translated.endswith('\\Z'):
            translated = translated[:-2]
        return r'\A{0}\Z'.format(translated)

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

    def create_checksum_file(self, src_file, dest_file):
        """Создаёт файл с хэшсуммой.

        Метод нужен для логирования. Основная работа происходит в _create_checksum_file.

        """
        try:
            hash_value = self._create_checksum_file(
                src_file,
                dest_file,
            )
        except PermissionError as exc:
            self.logger.warning(
                'Невозможно создать файл с хэшсуммой: %s',
                exc,
            )
        else:
            if self.dry:
                hash_value = '(dryrun, хэшсумма не подсчитывается)'
            self.logger.info(
                'Создан файл %s с хэшсуммой %s',
                dest_file,
                hash_value,
            )

    @side_effecting
    def _create_checksum_file(self, src_file, dest_file):
        return create_sha1sum_file(
            src_file,
            dest_file,
        )

    def __repr__(self):
        name = self.__class__.__name__
        attrs = self.__dict__.copy()
        if attrs.get('source'):
            attrs['source'] = '<{cls} \'{name}\'>'.format(
                cls=attrs.get('source').__class__.__name__,
                name=attrs.get('source').name,
            )

        return '{name}: {attrs}'.format(
            name=name,
            attrs=attrs,
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
