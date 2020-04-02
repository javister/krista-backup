# -*- coding: UTF-8 -*-

import logging
import os
import re

from .action import Action


class Rsync(Action):
    """Обёртка над rsync.

    Синхронизирует файлы между src_path и dest_path
    При желании, в конфиге можно переопределить опции, установить лимит
    скорости и добавить исключения
    """

    # src_path              # наследуется от Аction, каталог, откуда копировать
    # dest_path              # наследуется от Аction, каталог, куда копировать

    # опции по-умолчанию
    opts = ''
    # не сжимать!
    skip_compress = ['zip', '7z', 'tgz', 'gz', 'bz2', 'rar']
    # исключения в формате rsync
    exclusions = []
    # макс. скорость передачи, если 0 или меньше - неограничено
    bwlimit = ''
    # дополнительные опции
    other_opts = '-a -h -d -v'
    # путь к исполняемому файлу
    command_path = 'rsync'

    def __init__(self, name):
        super().__init__(name)

    def get_filelist(self):
        """Возвращает dict с файлами и директориями из указанного источника."""
        cmdline = ' '.join(['rsync', self.opts, '--list-only', self.src_path])

        listing = self.unsafe_execute_cmdline(
            cmdline,
            return_stdout=True,
        ).split('\n')

        file_listing = list(
            filter(lambda string: re.findall(r'[wr\-x]{10}', string), listing),
        )
        dir_listing = list(
            filter(lambda string: re.findall(r'd[wr\-x]{9}', string), listing),
        )

        name_start_index = 46

        # парсинг имён
        file_listing = list(
            map(lambda string: string[name_start_index:].strip(
            ), file_listing),
        )
        dir_listing = list(
            map(lambda string: string[name_start_index:].strip(), dir_listing),
        )

        if dir_listing:
            dir_listing.pop(0)  # Удаление директории с именем '.'

        return {'files': file_listing, 'dirs': dir_listing}

    def start_moving(self, includes):
        """Генерирует команду для переноса и начинает его."""
        compress = '--skip-compress={0}'.format('/'.join(self.skip_compress))

        exclude = ' '.join(
            map(lambda x: '='.join(['--exclude', x]), self.exclusions),
        )
        include = ' '.join(
            map(lambda x: '='.join(['--include', x]), includes),
        )

        if self.bwlimit:
            bwl = '--bwlimit={0}'.format(self.bwlimit)
        else:
            bwl = ''

        cmdline = ' '.join(
            [
                'rsync',
                self.opts,
                self.other_opts,
                bwl,
                compress,
                include,
                exclude,
                self.src_path,
                self.dest_path,
            ],
        )

        if self.dry:
            self.logger.info('Сгенерирована команда для запуска %s', cmdline)

        stdout_params = {
            'logger': self.logger,
            'default_level': logging.DEBUG,
        }
        stderr_params = {
            'logger': self.logger,
            'default_level': logging.ERROR,
        }

        self.execute_cmdline(
            cmdline,
            stdout_params=stdout_params,
            stderr_params=stderr_params,
        )

    def start(self):
        if not os.path.isdir(self.dest_path):
            os.makedirs(self.dest_path)

        if os.path.isdir(self.src_path):
            os.chdir(self.src_path)

        try:
            files = self.get_filelist()
        except Exception as exception:
            self.logger.error(
                'Ошибка при получении списка файлов: %s',
                exception,
            )
            return self.continue_on_error

        try:
            self.start_moving(files['dirs'] + files['files'])
        except Exception as exception:
            self.logger.error(
                'Ошибка при выполнении rsync: %s',
                exception,
            )
            return self.continue_on_error
        return True
