# -*- coding: UTF-8 -*-
import os
import re
import datetime
import shutil
import fnmatch

from runner.TarArchiver import TarArchiver
from model.YamlConfig import AppConfig
from runner.PgDump import PgDump


class Cleaner(TarArchiver):
    """
    Принцип работы чистильщиков одинаков, отличия только в принципе формирования списка файлов для удаления.

    Свойства, одинаковые для всех чистильщиков:
    - basename
    - patterns
    - use_re_in_patterns
    - dest_path

    Список файлов для удаления может быть определен 2мя способами: через basename и через patterns.
    basename удобно использовать при наследовании от TarArchive или PgDump, patterns - если нужно чистить логи
    или какой-нибудь аудит; можно использовать одновременно и то и другое.

    Параметр use_re_in_patterns определяет, как будут интерпретироваться basename или patterns - как паттерны shell
    или как регулярные выражения.

    По паттернам строится список файлов для удаления с учетом пути dest_path, включая подкаталоги.

    """

    # Начало имени файла для ротации. Файлы различаются по расширениями, то есть для .tar.gz, .list, .pg_dump ротация будет
    # применяться по-отдельности, например, при настройке 10 файлов будет сохранено 10 файлов .tar.gz, 10 .list и т.п.
    # наследуется от Action
    # basename='archive'

    # dest_path              # наследуется от Аction, каталог, в котором происходит чистка

    max_files = None
    """int: значение максимального количества файлов"""

    days = None
    """int: значение максимального количества дней"""

    # Еще один способ определить файлы для ротации - паттерны, через паттерны можно определить каталоги и т.п.
    # basename имеет приоритет над паттернами, то есть если basename указан, то паттерны не рассматриваются
    patterns = []

    # Если включить этот параметр, то паттерны будут рассматриваться как regexp, иначе как паттерны sh
    use_re_in_patterns = False
    re_pat = []

    full_files_list = {}

    level = -1
    parent_type = None  # тип предка для очистки

    databases = []  # для автоматической типизации при очистке бэкапов бд

    def __init__(self, name):
        TarArchiver.__init__(self, name)
        self._filename_dateformat = AppConfig.get_filename_dateformat()
        self.files_to_remove = []

    def add_re_pattern(self, basename):
        try:
            pat = basename + r"\S*"
            self.re_pat.append(re.compile(re_pat))
            self.logger.debug(
                u"Добавлена группа для удаления (basename re): %s", pat)
        except:
            self.logger.warning(u"Ошибка в регулярном выражении %s (basename).",
                                pat)

    def add_sh_pattern(self, basename):
        pat = basename + "*"
        self.re_pat.append(pat)
        self.logger.debug(u"Добавлена группа для удаления (basename sh): %s" %
                          pat)

    def retrieve_groups_from_pgdump(self):
        retrieved_groups = []
        if self.mode == "all":
            if self.user and self.password:
                os.putenv("PGPASSWORD", self.password)
            databases = PgDump.get_database_list(self.user, self.host,
                                                 self.port)
        else:
            databases = self.databases
        for db in databases:
            if db.strip():
                retrieved_groups.append("-".join([self.basename, db.strip()]))
        return retrieved_groups

    def parsePatterns(self, groups=None):
        if groups is None:
            groups = []
            if self.basename.strip():
                groups.append(self.basename)

        for basename_group in groups:
            if self.use_re_in_patterns:
                self.add_re_pattern(basename_group)
            else:
                self.add_sh_pattern(basename_group)

        for pat in self.patterns:
            if self.use_re_in_patterns:
                try:
                    if pat and len(pat.strip()):
                        self.re_pat.append(re.compile(pat))
                        self.logger.debug(
                            u"Добавлено имя для удаления истории (re): %s" %
                            pat)
                except:
                    self.logger.warning(
                        u"Ошибка в регулярном выражении %s в excludes." % pat)
            else:
                self.re_pat.append(pat)
                self.logger.debug(
                    u"Добавлено имя для удаления истории (sh): %s" % pat)

    def remove_matched_files(self):

        def onerror(function, path, excinfo):
            self.logger.warning(
                u"Ошибка рекурсивного удаления %s, функция %s, ошибка %s" %
                (path, function.__name__, str(excinfo)))

        for file in self.files_to_remove:
            if os.path.exists(file):
                try:
                    if os.path.isfile(file) or os.path.islink(file):
                        os.remove(file)
                    else:
                        shutil.rmtree(
                            file,
                            ignore_errors=False,
                            onerror=onerror,
                        )
                except FileNotFoundError as exc:
                    self.logger.info(
                        'Файл уже удалён %s, %s',
                        file,
                        exc,
                    )
                except Exception as exc:
                    self.logger.error(
                        'Ошибка при удалении файла %s, %s',
                        file,
                        exc,
                    )
                self.logger.debug("del %s" % file)

    def clear_state(self):
        self.files_to_remove.clear()
        self.full_files_list.clear()
        self.patterns.clear()
        self.re_pat.clear()
        self.databases.clear()

    def fillFilelist(self, path=None):
        """ Заполняет self.full_files_list файлами из
        директории path.

        Если path не указан, то файлы берутся из self.dest_path.
        """

        def makeFullFileList(path, rec=0):
            self.logger.debug(path)
            rec -= 1
            if rec <= 0:
                return
            for dirpath, dirnames, filenames in os.walk(path):
                for file in dirnames:
                    makeFullFileList(os.path.join(dirpath, file), rec)
                for file in filenames:
                    filename = os.path.splitext(file)

                    if len(filename) > 1:
                        ext = filename[1]
                    else:
                        ext = " "

                    if self.use_re_in_patterns:
                        match_pattern = re.match
                    else:
                        match_pattern = fnmatch.fnmatch

                    # Поиск и соотнесение соответствующему паттерну
                    for pattern in self.re_pat + self.patterns:
                        if match_pattern(file, pattern):
                            file_key = (ext, pattern)
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
            makeFullFileList(os.path.join(path, str(self.level)), 10)
        else:
            makeFullFileList(path, 10)

    def retrieveTimeFromName(self, filepath):
        filename = os.path.basename(filepath)

        if "." in filename:
            dot_index = filename.index(".")
            filepath_noext = filepath[:dot_index - len(filename)]
        else:
            filepath_noext = filepath

        splitted = filepath_noext.split("-")
        for part in reversed(splitted):
            try:
                return datetime.datetime.strptime(part,
                                                  self._filename_dateformat)
            except:
                pass
        self.logger.error("Date mark not found in %s", filepath)

    def fill_files_to_remove(self, path=None, days=None, max_files=None):
        self.fillFilelist(path)

        if self.full_files_list.keys():
            self.logger.debug('Файлы для обработки:%s',
                              str(self.full_files_list))

            if not days is None:
                self.filter_files_to_remove_by_days(days=days)

            if not max_files is None:
                self.filter_files_to_remove_by_amount(max_files=max_files)

            if self.files_to_remove:
                self.logger.debug('Файлы для удаления: %s',
                                  str(self.files_to_remove))
            else:
                self.logger.info('Нет файлов для удаления.')

        else:
            self.logger.info('Нет файлов для обработки.')

    def process_pgdump(self):
        """ 
        Выполнение ротации PgDump.
        В этой ветке выполняется следующий алгоритм:

        1. сбор паттернов для выделения групп баз данных
        2. подготовка всех паттернов
        3. поиск файлов попадающих под критерии
        4. удаление файлов
        """
        try:
            retrieved_groups = self.retrieve_groups_from_pgdump()
        except Exception as e:
            self.logger.warn(
                "Корректных данных для подключения к базе не предоставлено")
            self.logger.warn(e)
            retrieved_groups = []
        finally:
            self.parsePatterns(groups=retrieved_groups)

        if self.re_pat:
            self.fill_files_to_remove(max_files=self.max_files, days=self.days)
        else:
            self.logger.warning(u"Не заданы паттерны.")

        try:
            self.remove_matched_files()
            self.clear_state()
        except Exception as exc:
            self.logger('Ошибка при выполнении очистки: %s', exc)
            return self.continue_on_error

        return True

    def process_move_bkp_period(self):
        """
        Выполнение ротации MoveBkpPeriod.
        В этой ветке выполняется следующий алгоритм:

        1. подготовка всех паттернов
        2. обработка периодов в цикле
        2.1 сбор файлов для данного периода
        2.2 удаление файлов
        """
        if not self.basename_list:
            self.basename_list = []
        self.parsePatterns(groups=self.basename_list)
        if self.re_pat:
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
                self.fill_files_to_remove(path=period_path,
                                          max_files=max_files,
                                          days=days)
                try:
                    self.remove_matched_files()
                except Exception as exc:
                    self.logger('Ошибка при выполнении очистки: %s', exc)
            if error_caught:
                return self.continue_on_error
        else:
            self.logger.warning(u"Не заданы паттерны.")

        return True

    def start(self):
        """
        Содержит вызов веток выполнения для
        pgdump, move_bkp_period и остальных actions.

        Ветка выбирается проверкой типа родительского action
        через self.parent_type.

        """
        if self.parent_type == 'pgdump':
            self.logger.debug('Начало очистки pgdump')
            return self.process_pgdump()
        elif self.parent_type == 'move_bkp_period':
            self.logger.info('Начало очистки MoveBkpPeriod')
            return self.process_move_bkp_period()
        else:
            self.logger.info('Начало обычной очистки')
            self.parsePatterns()
            if self.re_pat:
                self.fill_files_to_remove(max_files=self.max_files,
                                          days=self.days)
            else:
                self.logger.warning('Не заданы паттерны.')
        try:
            self.remove_matched_files()
            self.clear_state()
        except Exception as exc:
            self.logger('Ошибка при выполнении очистки: %s', e)
            return self.continue_on_error
        return True

    def filter_files_to_remove_by_amount(self, max_files):
        for key in self.full_files_list.keys():
            key_list = sorted(
                self.full_files_list[key],
                key=lambda file: self.retrieveTimeFromName(file),
                reverse=True,
            )
            while len(key_list) > max_files and len(key_list):
                file_to_remove = key_list.pop()
                self.files_to_remove.append(file_to_remove)

    def filter_files_to_remove_by_days(self, days):
        now_date = datetime.datetime.now()
        for key in self.full_files_list.keys():
            for file in sorted(self.full_files_list[key]):
                if os.path.isfile(file):
                    file_mtime = self.retrieveTimeFromName(file)
                    if (now_date - file_mtime).days >= days:
                        self.files_to_remove.append(file)
