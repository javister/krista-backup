# -*- coding: UTF-8 -*-

import datetime
import fnmatch
import os
import re
import shutil

from model.YamlConfig import AppConfig

from .action import Action
from .pgdump import PgDump


class Cleaner(Action):
    """Класс действия для удаления файлов.

    Основные атрибуты:
        basename: Строка с базовым именем
        patterns: Список паттернов
        use_re_in_patterns: Логическое значение, если True, то паттерны regexp, иначе shell
        dest_path: Строка с путём, содержащим удаляемые файлы
        days: Число, максимальное количество дней файлов в группе
        max_files: Число, максимальное количество файлов в группе
        parent_type: Строка с типом родительского действия

    Список файлов для удаления определяется явными ограничениями и неявными.
    Явными ограничениями являются days, max_files и patterns. Пример неявных:
    при обработке чистильщика-наследника pgdump будут наследованы имена баз данных,
    а по ним будут построены паттерны.


    По паттернам строится список файлов для удаления с учетом пути dest_path, включая подкаталоги.

    Список файлов - словарь, который содержит ключи (расширение файла, паттерн).

    """

    max_files = None
    """int: значение максимального количества файлов"""

    days = None
    """int: значение максимального количества дней"""

    use_re_in_patterns = False
    """bool: если True, то паттерны regexp, иначе shell"""

    patterns = []  # необработанные паттерны
    prepared_patterns = []  # лист с готовыми к работе паттернами

    full_files_list = {}

    level = -1
    parent_type = None  # тип предка для специальной обработки

    # список баз данных от pgdump
    # определение нужно для автоматической типизации
    # при очистке бэкапов бд

    databases = []

    def __init__(self, name):
        super().__init__(name)
        self._filename_dateformat = AppConfig.get_filename_dateformat()
        self.files_to_remove = []

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
            self.logger.debug(
                'Добавлена группа для удаления (re): %s',
                pattern,
            )

    def add_sh_pattern(self, pattern):
        """Добавление shell паттерна в список паттернов."""
        pattern = r'{0}*'.format(pattern)
        self.prepared_patterns.append(pattern)
        self.logger.debug(
            'Добавлена группа для удаления (sh): %s',
            pattern,
        )

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
            databases = self.databases
        else:
            try:
                databases = PgDump.get_database_list(
                    self.user,
                    self.host,
                    self.port,
                )
            except AttributeError:
                databases = PgDump.get_database_list()
        for db in databases:
            dbname = db.strip()
            if dbname:
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
                    try:
                        compiled_pattern = re.compile(pattern)
                    except Exception as exc:
                        self.logger.warning(
                            'Ошибка в регулярном выражении %s, %s',
                            pattern,
                            exc,
                        )
                    else:
                        self.prepared_patterns.append(compiled_pattern)
                        self.logger.debug(
                            'Добавлена группа для удаления (re): %s',
                            pattern,
                        )
        else:
            for basename_group in groups:
                self.add_sh_pattern(basename_group)

            for pattern in self.patterns:
                self.prepared_patterns.append(pattern)
                self.logger.debug(
                    'Добавлено имя для удаления истории (sh): %s',
                    pattern,
                )

    def remove_matched_files(self):
        """Удаляет файлы из self.files_to_remove."""
        def onerror(function, path, excinfo):
            self.logger.warning(
                'Ошибка рекурсивного удаления %s, функция %s, ошибка %s',
                path,
                function.__name__,
                excinfo,
            )

        for filepath in self.files_to_remove:
            if os.path.exists(filepath):
                try:
                    if os.path.isfile(filepath) or os.path.islink(filepath):
                        os.remove(filepath)
                    else:
                        shutil.rmtree(
                            filepath,
                            ignore_errors=False,
                            onerror=onerror,
                        )
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

    def clear_state(self):
        """Очистка состояния.

        TODO неизвестно, требуется ли она сейчас или нет
        """
        self.files_to_remove.clear()
        self.full_files_list.clear()
        self.patterns.clear()
        self.prepared_patterns.clear()
        self.databases.clear()

    def fill_filelist(self, path=None):
        """Заполняет self.full_files_list файлами из директории path.

        Если path не указан, то файлы берутся из self.dest_path.
        """
        if self.use_re_in_patterns:
            match_pattern = re.match
        else:
            match_pattern = fnmatch.fnmatch

        def make_full_filelist(path, rec=10):
            self.logger.debug(path)
            if rec <= 0:
                self.logger.warning(
                    'Достигнут максимальный уровень глубины при заполнении списка файлов!',
                )
                return
            for dirpath, dirnames, filenames in os.walk(path):
                for dirname in dirnames:
                    make_full_filelist(
                        os.path.join(dirpath, dirname),
                        rec - 1,
                    )
                for file in filenames:
                    filename = os.path.splitext(file)

                    if filename[1]:  # если расширение файла не пустое
                        file_extension = filename[1]
                    else:
                        file_extension = ' '

                    # Поиск и соотнесение соответствующему паттерну
                    for pattern in self.prepared_patterns:
                        if match_pattern(file, pattern):
                            file_key = (file_extension, pattern)
                            filepath = os.path.join(dirpath, file)
                            if file_key in self.full_files_list.keys():
                                self.full_files_list[file_key].append(filepath)
                            else:
                                fl = [filepath]
                                self.full_files_list[file_key] = fl
                            break

        if not path:
            path = self.dest_path

        if self.level >= 0:
            make_full_filelist(os.path.join(path, str(self.level)))
        else:
            make_full_filelist(path)

    def retrieve_time_from_name(self, filepath):
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
        self.logger.error('Date mark not found in %s', filepath)

    def fill_files_to_remove(self, path=None, days=None, max_files=None):
        self.fill_filelist(path)

        if self.full_files_list.keys():
            self.logger.debug(
                'Файлы для обработки:%s',
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

        if self.prepared_patterns:
            self.fill_files_to_remove(max_files=self.max_files, days=self.days)
        else:
            self.logger.warning('Не заданы паттерны')

        try:
            self.remove_matched_files()
            self.clear_state()
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
            """
            Если во время обработки одного из периодов произошла ошибка,
            то error_caught её записывает и, после завершения обработки
            всех периодов, происходит её обработка.
            """

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

            self.clear_state()
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
            finally:
                self.clear_state()

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
                    file_mtime = self.retrieve_time_from_name(file)
                    if (now_date - file_mtime).days >= days:
                        self.files_to_remove.append(file)
