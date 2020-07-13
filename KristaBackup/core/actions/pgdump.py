# -*- coding: UTF-8 -*-

import logging
import os
import re
import shutil

from .action import Action
from .decorators import use_exclusions
from .interfaces import NameGenerationInterface


@use_exclusions
class PgDump(Action, NameGenerationInterface):
    """
        Выполняется pg_dump с некоторым набором парамеров.
        Список баз, для которых нужно делать бекап формируется следующим образом:
        - с сервера по указанным пользователь вычитывается список баз.
        - из списка вычитаются имена, которые подходят под критерии параметра exclusions (список регулярных выражений)
        - для каждой базы создается 1 файл бекапа, имя определяется как basename-имя базы-датавремя.extension
     mode - режим работы, если all - то бекапяться все базы, если режим
            single, то бекапяться базы из списка databases
    """

    stderr_filters = {
        logging.DEBUG: {
            'reading .*', 'чтение .*',
            'last built-in .*', 'последний системный .*',
            'identifying .*', 'выявление .*',
            'finding .*', 'поиск .*',
            'flagging .*', 'пометка .*',
            'saving .*', 'сохранение .*',
            'dumping .*', 'выгрузка .*',
            'AC MODEL: .*', 'obtained maximum .*',
        },
    }

    def __init__(self, name):
        super().__init__(name)
        self.format = 'custom'  # формат бекапа

        self.command_path = 'pg_dump'  # путь к команде pg_dump
        self.opts = ''  # опции запуска pg_dump, могут переопределяться в настройках
        self.checksum_file = False

        self.host = None
        self.port = 5432
        self.user = None
        self.password = None
        self.databases = []
        self.mode = 'single'

    def backup_database(self, database):
        """Выполняет бэкап базы.

        Args:
            database: Строка, имя базы.

        Returns:
            True, если возникли ошибки.

        """
        filepath = self.generate_filepath(
            dbname=database,
        )

        if not os.path.exists(self.dest_path):
            self.logger.debug(
                'Выходная директория %s не существует.',
                self.dest_path,
            )
            if not self.dry:
                os.makedirs(self.dest_path)
            self.logger.debug('Директория создана.')

        if self.format == 'directory':
            if not self.dry:
                os.makedirs(filepath)
                shutil.chown(filepath, user=self.user)
            self.logger.debug('Директория %s создана.', filepath)

        cmdline = ' '.join(
            [
                self.command_path,
                self.opts,
                '--dbname',
                database,
                ' '.join(['--host', self.host]
                         ) if self.host and self.user else '',
                ' '.join(['--port', str(self.port)]) if self.port else '',
                ' '.join(['--username', self.user]) if self.user else '',
                '='.join(['--format', self.format]),
                '='.join(['--file', filepath]
                         ) if self.format == 'directory' else '',
            ],
        )

        if not self.user:
            # запуск команды под пользователем postgres, если user не указан
            cmdline = 'su postgres -c \'{0}\''.format(cmdline)
        if self.format == 'custom':
            cmdline += '> {0}'.format(filepath)

        stdout_params = {
            'logger': self.logger,
            'remove_header': True,
            'default_level': logging.DEBUG,
        }

        stderr_params = {
            'logger': self.logger,
            'filters': self.stderr_filters,
            'remove_header': True,
            'default_level': logging.ERROR,
        }

        self.logger.debug('Выполнение команды %s', cmdline)
        try:
            self.execute_cmdline(
                cmdline,
                stdout_params=stdout_params,
                stderr_params=stderr_params,
            )
        except Exception as exc:
            self.logger.error('Ошибка при выполнении: %s', exc)
            return True
        self.logger.info('Заархивирована база %s', database)

        if self.checksum_file:
            hash_filepath = self.generate_hash_filepath(dbname=database)
            self.create_checksum_file(filepath, hash_filepath)

    def is_exclusion(self, dbname):
        for ex in self.prepared_exclusions:
            if re.match(ex, dbname):
                return True
        return False

    @staticmethod
    def get_database_list(user=None, host=None, port=None, *, logger=None):
        """Подключается к postgresql и получает список баз.

        Требует наличия переменной PGPASSWORD в окружении.

        """
        cmdline = 'echo "select datname from pg_database" | {psql_cmdline}'
        psql_cmdline = 'psql {0} --tuples-only --dbname postgres'.format(
            ' '.join(
                [
                    ' '.join(['--user', user]) if user else '',
                    ' '.join(['--host', host]) if host and user else '',
                    ' '.join(['--port', str(port)]) if port else '',
                ]
            )
        )

        if not user:
            # запуск команды под пользователем postgres, если user не указан
            psql_cmdline = 'su postgres -c "{0}"'.format(psql_cmdline)

        cmdline = cmdline.format(psql_cmdline=psql_cmdline)
        if logger:
            logger.debug('Запускается команда %s', cmdline)

        database_list = Action.unsafe_execute_cmdline(
            cmdline,
            return_stdout=True,
        ).split()

        return [dbname.strip() for dbname in database_list if dbname.strip()]

    def _get_database_list(self):
        if self.user and self.password:
            os.putenv('PGPASSWORD', self.password)
        if self.mode == 'all':
            database_list = PgDump.get_database_list(
                self.user,
                self.host,
                self.port,
                logger=self.logger,
            )
        elif self.mode == 'single':
            database_list = [
                dbname.strip() for dbname in self.databases if dbname.strip()
            ]
        return database_list

    def start(self):
        failed = False
        self.format = self.format.strip().lower()
        database_list = self._get_database_list()
        if not database_list:
            self.logger.warning('Отсутствуют базы для бэкапа')
            return self.continue_on_error

        self.parse_exclusions()
        for dbname in database_list:
            if self.is_exclusion(dbname):
                self.logger.debug('- %s', dbname)
            else:
                error = self.backup_database(dbname)
                failed = error or failed
                self.logger.debug('+ %s', dbname)

        if failed:
            return self.continue_on_error

        return True

    def parse_exclusions(self):
        """Обработка переданных исключений."""
        for exclusion in self.exclusions:
            exclusion = self.prepare_pattern(exclusion)
            if not exclusion:
                continue
            try:
                exclusion = re.compile(exclusion)
            except Exception as exc:
                self.logger.warning(
                    'Ошибка в исключении %s: %s',
                    exclusion,
                    exc,
                )
            else:
                self.prepared_exclusions.append(exclusion)

        self.logger.debug(
            'Добавлены исключения: %s',
            [excl.pattern for excl in self.prepared_exclusions],
        )

    def generate_filename(self, *args, **kwargs):
        """Генерирует выходное имя файла."""
        return self.scheme.get_pgdump_name(self, **kwargs)

    def get_patterns(self, *args, **kwargs):
        patterns = []
        dblist = self._get_database_list()
        for dbname in dblist:
            pattern = self.scheme.get_pgdump_pattern(
                self,
                dbname=dbname,
            )
            patterns.append(pattern)
            if self.checksum_file:
                hash_p = self.scheme.get_pgdump_hashfile_pattern(
                    self, dbname=dbname)
                patterns.append(hash_p)
        return patterns

    def retrieve_groups_from_pgdump(self):
        """Получение списка групп по данным из родительского pgdump.

        Метод пытается узнать список баз данных по предоставленным
        данным из родительского действия pgdump.
        Если в родительском действии есть список баз, то используется он,
        если нет - попытка получить список баз напрямую через pg_dump.

        Returns:
            Список паттернов групп, который генерируются при помощи
                схемы именования.

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
            pattern = self.source.scheme.get_pgdump_pattern(
                self,
                dbname=dbname,
            )
            retrieved_groups.append(pattern)
        return retrieved_groups

    def generate_hash_filename(self, *args, **kwargs):
        """Генерирует выходное имя файла c чексуммой."""
        if kwargs.get('dbname'):
            return self.scheme.get_pgdump_hashfile_name(self, dbname=kwargs.get('dbname'))
        return self.scheme.get_pgdump_hashfile_name(self)
