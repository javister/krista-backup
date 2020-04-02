# -*- coding: UTF-8 -*-

import datetime
import functools
import os
import re
import shutil

from common.YamlConfig import AppConfig

from .action import Action
from .pgdump import PgDump
from .decorators import (
    side_effecting, use_exclusions, use_levels,
    use_patterns, use_postgres,
)


@use_exclusions
@use_patterns
@use_levels
@use_postgres
class Cleaner(Action):
    """Класс действия для удаления файлов.

    Attributes:
        Внешние:
            patterns: Список необработанных паттернов
            dest_path: Строка с путём, содержащим удаляемые файлы
            days: Число, максимальное количество дней файлов в группе
            max_files: Число, максимальное количество файлов в группе
            exclusions: Список паттернов для исключения файлов из удаляемых

        Внутренние:
            full_files_list: Словарь со всеми найденными файлами
            files_to_remove: Список файлов дляя удаления
            prepared_patterns: Список подготовленных для работы паттернов
            prepared_exclusions: Список подготовленных исключений.
            parent_type: Строка с типом родительского действия

    По паттернам строится список файлов для удаления full_files_list с учетом
    пути dest_path (или требуемого в действии пути), включая подкаталоги.

    Список файлов - словарь, который содержит записи вида:
        (расширение файла, паттерн): путь к файлу.

    Список файлов для удаления определяется явными ограничениями и неявными.
    Пример явных:
        days, max_files и patterns.
    Пример неявных:
        при обработке чистильщика-наследника pgdump будут наследованы имена
        баз данных, а по ним будут построены паттерны.

    """

    def __init__(self, name):
        super().__init__(name)

        self.max_files = None
        self.days = None
        self.full_files_list = {}
        self.files_to_remove = []
        self.parent_type = None

        self._filename_dateformat = AppConfig.get_filename_dateformat()

    def add_re_pattern(self, group):
        """Добавление re паттерна в список паттернов."""
        pattern = r'{0}\S*'.format(group)
        try:
            compiled_pattern = re.compile(pattern)
        except Exception as exc:
            self.logger.warning(
                'Ошибка в регулярном выражении: %s, %s',
                pattern,
                exc,
            )
        else:
            self.prepared_patterns.append(compiled_pattern)

    def add_sh_pattern(self, pattern):
        """Добавление shell паттерна в список паттернов."""
        pattern = r'{0}*'.format(pattern)
        self.prepared_patterns.append(pattern)

    def retrieve_groups_from_pgdump(self):
        """Получение списка групп по данным из родительского pgdump.

        Метод пытается узнать список баз данных по предоставленным
        данным из родительского действия pgdump.
        Если в родительском действии есть список баз, то используется он,
        если нет - попытка получить список баз напрямую через pg_dump.

        Returns:
            Список групп вида {basename}-{dbname}.

        """
        retrieved_groups = []
        if self.databases:
            self.logger.debug('Список баз получен через атрибут databases.')
            databases = self.databases
        else:
            self.logger.debug('Атрибут databases со списком баз отсутствует.')
            self.logger.debug(
                'Пытаюсь получить список баз напрямую из postgres.',
            )
            if self.password:
                os.putenv('PGPASSWORD', self.password)
            try:
                databases = PgDump.get_database_list(
                    self.user,
                    self.host,
                    self.port,
                    logger=self.logger,
                )
            except AttributeError:
                databases = PgDump.get_database_list(logger=self.logger)

        self.logger.debug('Получены базы: %s', databases)

        for dbname in databases:
            retrieved_groups.append('-'.join([self.basename, dbname]))
        return retrieved_groups

    def parse_patterns(self, groups=None):
        """Обработка всех переданных патернов.

        В действие паттерны могут быть переданы явно (patterns)
        или неявно (через groups).

        Args:
            groups: Список паттернов, который был сгенерирован по атрибутам,
                которые были получены неявно, например, были получены от
                родителя.

        """
        if groups is None:
            groups = []
            if self.basename.strip():
                groups.append(self.basename)

        if self.use_re_in_patterns:
            for basename_group in groups:
                self.add_re_pattern(basename_group)
            for pattern in self.patterns:
                if pattern and pattern.strip():
                    self.add_re_pattern(pattern)

            self.logger.debug(
                'Добавлены группы для удаления (re): %s',
                self.patterns,
            )
        else:
            for basename_group in groups:
                self.add_sh_pattern(basename_group)
            for pattern in self.patterns:
                self.prepared_patterns.append(pattern)

            self.logger.debug(
                'Добавлены группы для удаления (sh): %s',
                self.prepared_patterns,
            )

    def parse_exclusions(self):
        """Обработка переданных исключений.

        Принцип обработки зависит от родительского действия.

        """
        if self.parent_type == 'pgdump':
            if self.use_re_in_patterns:
                for exclusion in self.exclusions:
                    exclusion = r'{bs}-{ex}\S*'.format(
                        bs=self.basename,
                        ex=exclusion,
                    )
                    self.prepared_exclusions.append(exclusion)

                self.logger.debug(
                    'Добавлены исключения (re): %s',
                    self.prepared_exclusions,
                )
            else:
                for exclusion in self.exclusions:
                    exclusion = r'{bs}-{ex}'.format(
                        bs=self.basename,
                        ex=exclusion,
                    )
                    self.prepared_exclusions.append(exclusion)

                self.logger.debug(
                    'Добавлены исключения (sh): %s',
                    self.prepared_exclusions,
                )

    def remove_matched_files(self):
        """Удаляет файлы из self.files_to_remove."""
        for filepath in self.files_to_remove:
            if os.path.exists(filepath):
                try:
                    self._remove(filepath)
                except FileNotFoundError as exc:
                    self.logger.info(
                        'Файл уже удалён %s, %s',
                        filepath,
                        exc,
                    )
                except Exception as exc:
                    self.logger.error(
                        'Ошибка при удалении файла %s, %s',
                        filepath,
                        exc,
                    )
                else:
                    self.logger.debug('Удалён: %s', filepath)

    def add_file_to_filelist(self, src, getkey, base_path=None):
        """Добавляет файл в self.full_files_list.

        Args:
            src: Строка, путь к файлу, чаще всего относительный.
            getkey: Функция получения сигнатуры, которая используется
            в качестве ключа в full_files_list.
            base_path: Строка, путь до относительного пути src.

        """
        key = getkey(src)
        if key:
            if base_path:
                src = os.path.join(base_path, src)
            self.full_files_list.setdefault(key, []).append(src)

    def fill_filelist(self, path=None):
        """Заполняет self.full_files_list файлами из директории path.

        Если path не указан, то файлы берутся из self.dest_path.
        """
        composed_filter = functools.partial(
            self._filter_file,
            pattern_matcher=self.get_pattern_matcher(),
        )

        if path is None:
            path = self.dest_path
        if self.parent_type == 'tar':
            path = os.path.join(self.dest_path, self.level_folders[self.level])

        apply = functools.partial(
            self.add_file_to_filelist,
            getkey=composed_filter,
            base_path=path,
        )
        try:
            self.walk_apply(path, apply, recursive=False, apply_dirs=False)
        except AttributeError:
            self.logger.info('Указаный путь не существует')

    def retrieve_time_from_name(self, filepath):
        """Достаёт время создания файла по его имени.

        Если время достать не удалось, то возвращает None.

        Returns:
            datetime.datetime с временной отметкой, либо None.

        """
        filename = os.path.basename(filepath)

        if '.' in filename:
            dot_index = filename.index('.')
            filepath_noext = filepath[:dot_index - len(filename)]
        else:
            filepath_noext = filepath

        splitted = filepath_noext.split('-')
        for part in reversed(splitted):
            try:
                return datetime.datetime.strptime(
                    part,
                    self._filename_dateformat,
                )
            except Exception:
                pass
        self.logger.warning('Временная отметка не найдена: %s', filepath)
        return None

    def fill_files_to_remove(self, path=None, days=None, max_files=None):
        """Собирает список файлов по группам и нужные добавляет на удаление.

        Args:
            path: Строка, путь к удаляемым файлам.
            days: Число, максимальное количество дней.
            max_files: Число, требуемое максимальное количество файлов в группе.

        """
        self.fill_filelist(path)

        if self.full_files_list.keys():
            self.logger.debug(
                'Файлы для обработки: %s',
                self.full_files_list,
            )

            if days is not None:
                self.filter_files_to_remove_by_days(days=days)

            if max_files is not None:
                self.filter_files_to_remove_by_amount(max_files=max_files)

            if self.files_to_remove:
                self.logger.debug(
                    'Файлы для удаления: %s',
                    self.files_to_remove,
                )
            else:
                self.logger.info('Нет файлов для удаления.')
        else:
            self.logger.info('Нет файлов для обработки.')

    def process_pgdump(self):
        """Выполнение очистки при наследовании от PgDump.

        В этой ветке выполняется следующий алгоритм:

        1. попытка явно получить список баз из pgdump или self.databases
        2. подготовка всех паттернов
        3. поиск файлов попадающих под критерии
        4. удаление файлов
        """
        try:
            retrieved_groups = self.retrieve_groups_from_pgdump()
        except Exception as exc:
            self.logger.debug(
                'Не удалось получить список баз явно, будут использоваться только паттерны, %s',
                exc,
            )
            retrieved_groups = []
        finally:
            self.parse_patterns(groups=retrieved_groups)
            self.parse_exclusions()

        if self.prepared_patterns:
            self.fill_files_to_remove(max_files=self.max_files, days=self.days)
        else:
            self.logger.warning('Не заданы паттерны')

        try:
            self.remove_matched_files()
        except Exception as exc:
            self.logger('Ошибка при выполнении очистки: %s', exc)
            return self.continue_on_error

        return True

    def process_move_bkp_period(self):
        """Выполнение очистки при наследовании от MoveBkpPeriod.

        В этой ветке выполняется следующий алгоритм:

        1. подготовка всех паттернов
        2. обработка периодов в цикле
            2.1 сбор файлов для данного периода
            2.2 удаление файлов

        """
        if not self.basename_list:
            self.basename_list = []
        self.parse_patterns(groups=self.basename_list)
        if self.prepared_patterns:
            error_caught = False
            # Если во время обработки одного из периодов произошла ошибка,
            # то error_caught её записывает и, после завершения обработки
            # всех периодов, происходит её обработка.

            for period_name in self.periods:
                period_path = os.path.join(
                    self.dest_path,
                    self.periods[period_name].get('path', period_name))
                max_files = self.periods[period_name].get('max_files')
                days = self.periods[period_name].get('days')
                self.fill_files_to_remove(
                    path=period_path,
                    max_files=max_files,
                    days=days,
                )
                try:
                    self.remove_matched_files()
                except Exception as exc:
                    self.logger('Ошибка при выполнении очистки: %s', exc)
                finally:
                    self.full_files_list = {}

            if error_caught:
                return self.continue_on_error
        else:
            self.logger.warning('Не заданы паттерны!')

        return True

    def start(self):
        """Входная точка действия.

        Содержит вызов веток выполнения для
        pgdump, move_bkp_period и остальных дейтсвий.

        Ветка выбирается проверкой типа родительского действия,
        которая находится в self.parent_type.

        """
        if self.parent_type == 'pgdump':
            self.logger.debug('Начало очистки pgdump')
            return self.process_pgdump()
        elif self.parent_type == 'move_bkp_period':
            self.logger.info('Начало очистки MoveBkpPeriod')
            return self.process_move_bkp_period()
        elif self.parent_type == 'tar':
            self.parse_patterns()
            path = os.path.join(self.dest_path, self.level_folders[self.level])
            if self.prepared_patterns:
                self.fill_files_to_remove(
                    path=path,
                    max_files=self.max_files,
                    days=self.days,
                )
            else:
                self.logger.warning('Не заданы паттерны')
            try:
                self.remove_matched_files()
            except Exception as exc:
                self.logger('Ошибка при выполнении очистки: %s', exc)
                return self.continue_on_error
        else:
            self.parse_patterns()
            if self.prepared_patterns:
                self.fill_files_to_remove(
                    max_files=self.max_files,
                    days=self.days,
                )
            else:
                self.logger.warning('Не заданы паттерны')

            try:
                self.remove_matched_files()
            except Exception as exc:
                self.logger('Ошибка при выполнении очистки: %s', exc)
                return self.continue_on_error
        return True

    def filter_files_to_remove_by_amount(self, max_files):
        """Фильтрует и исключает файлы из self.full_files_list по количеству в группе."""
        for key in self.full_files_list.keys():
            key_list = sorted(
                self.full_files_list[key],
                key=lambda file: self.retrieve_time_from_name(file),
                reverse=True,
            )
            while len(key_list) > max_files and len(key_list):
                file_to_remove = key_list.pop()
                self.files_to_remove.append(file_to_remove)

    def filter_files_to_remove_by_days(self, days):
        """Фильтрует и исключает файлы из self.full_files_list по количеству дней.

        Для получения времени из имени используется метод self.retrieve_time_from_name.
        """
        now_date = datetime.datetime.now()
        for key in self.full_files_list.keys():
            for file in sorted(self.full_files_list[key]):
                if os.path.isfile(file):
                    file_ctime = self.retrieve_time_from_name(file)
                    if file_ctime is not None:
                        if (now_date - file_ctime).days >= days:
                            self.files_to_remove.append(file)

    def _filter_file(self, filepath, pattern_matcher):
        """Проверяет попадание файл в паттерны и отсутствие в исключениях.

        Args:
            pattern_matcher: Функция для сравнения с паттерном.
        """
        full_filename = os.path.basename(filepath)
        filename, file_extension = os.path.splitext(full_filename)
        if file_extension == '':
            file_extension = ' '
        for pattern in self.prepared_patterns:
            if pattern_matcher(pattern, filename):
                for exclusion_pattern in self.prepared_exclusions:
                    if pattern_matcher(exclusion_pattern, filepath):
                        return False  # файл не прошёл exclusions
                return (file_extension, pattern)  # файл прошёл все exclusions
        return False

    @side_effecting
    def _remove(self, filepath):
        """Удалят определённый файл по filepath.

        Args:
            filepath (str): путь к файлу, директории или ссылке.

        """
        def onerror(function, path, excinfo):
            self.logger.warning(
                'Ошибка рекурсивного удаления %s, функция %s, ошибка %s',
                path,
                function.__name__,
                excinfo,
            )

        if os.path.isfile(filepath) or os.path.islink(filepath):
            os.remove(filepath)
        else:
            shutil.rmtree(
                filepath,
                ignore_errors=False,
                onerror=onerror,
            )
