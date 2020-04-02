# -*- coding: UTF-8 -*-

import logging
import os
import shutil

from .action import Action
from .decorators import use_exclusions, use_postgres


@use_exclusions
@use_postgres
class PgDump(Action):
    """
        Выполняется pg_dump с некоторым набором парамеров.
        Список баз, для которых нужно делать бекап формируется следующим образом:
        - с сервера по указанным пользователь вычитывается список баз.
        - из списка вычитаются имена, которые подходят под критерии параметра exclusions (список регулярных выражений)
        - для каждой базы создается 1 файл бекапа, имя определяется как basename-имя базы-датавремя.extension
    """

    # dest_path              # наследуется от Аction, каталог, куда складываются бекапы
    # basename               # основа для имени файла, наследуется от Action
    """
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
        },
    }

    def __init__(self, name):
        super().__init__(name)
        self.format = 'custom'  # формат бекапа

        self.extension = 'pg_dump'  # расширение для файла бекапа
        self.command_path = 'pg_dump'  # путь к команде pg_dump
        self.opts = ''  # опции запуска pg_dump, могут переопределяться в настройках
        self.pgdump_log_debug = False

    def backup_database(self, database):
        """Выполняет бэкап базы.

        Args:
            database: Строка, имя базы.

        Returns:
            True, если возникли ошибки.

        """
        filepath = self.generate_filepath(database, extension=self.extension)

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
                '-d',
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

        # запуск команды под postgres
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
        self.logger.info('Зархивирована база %s', database)

    def is_exclusion(self, dbname):
        matcher = self.get_pattern_matcher()
        for ex in self.prepared_exclusions:
            if matcher(ex, dbname):
                return True
        return False

    @staticmethod
    def get_database_list(user=None, host=None, port=None, *, logger=None):
        """Подключается к postgresql и получает список баз.

        Требует наличия переменной PGPASSWORD в окружении.

        """
        cmdline = 'echo "select datname from pg_database" | su postgres -c "psql {} -t -d postgres"'.format(
            ' '.join(
                [
                    ' '.join(['--user', user]) if user else '',
                    ' '.join(['--host', host]) if host and user else '',
                    ' '.join(['--port', str(port)]) if port else '',
                ]
            )
        )
        if logger:
            logger.debug('Запускается команда %s', cmdline)

        database_list = Action.unsafe_execute_cmdline(
            cmdline,
            return_stdout=True,
        ).split()

        return [dbname.strip() for dbname in database_list if dbname.strip()]

    def start(self):
        failed = False
        self.format = self.format.strip().lower()

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
        if self.use_re_in_patterns:
            for exclusion in self.exclusions:
                exclusion = exclusion.strip()
                if not exclusion:
                    continue
                exclusion = r'{ex}\S*'.format(
                    ex=exclusion,
                )
                self.prepared_exclusions.append(exclusion)

            self.logger.debug(
                'Добавлены исключения (re): %s',
                self.prepared_exclusions,
            )
        else:
            for exclusion in self.exclusions:
                exclusion = exclusion.strip()
                if not exclusion:
                    continue
                exclusion = r'{ex}'.format(
                    ex=exclusion,
                )
                self.prepared_exclusions.append(exclusion)

            self.logger.debug(
                'Добавлены исключения (sh): %s',
                self.prepared_exclusions,
            )
