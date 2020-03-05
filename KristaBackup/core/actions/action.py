# -*- coding: UTF-8 -*-

import logging
import os
import re

from common.YamlConfig import AppConfig


class Action:

    # атрибуты, которые должны быть обязательно заданы в конфиге
    required_attrs = ['name']

    # этот атрибут используется во всех наследниках, которые создают используются файлы-бекапы (tar, pg_dump, cleaners)
    basename = 'archive'
    # путь-источник, используется во многих потомках
    src_path = '.'
    # путь-получатель, используется во многих потомках
    dest_path = '.'
    # используется в потомках при формировании файлов
    time_suffix = AppConfig.get_starttime_str()

    # определяет стоит ли продолжать выполнение после провала текущего action
    continue_on_error = False

    error = False
    error_msg = 'Well done.'

    def makeFilename(self, name=None, time_suffix=None, ext=None):
        if not name is None:
            fname = "-".join([self.basename, name])
        else:
            fname = self.basename

        if not time_suffix:
            time_suffix = self.time_suffix

        if not ext:
            ext = self.extension

        try:
            elements = [fname, time_suffix, str(self.level)]
            levelpath = os.path.join(self.dest_path,
                                     self.level_folders[self.level])
        except:
            elements = [fname, time_suffix]
            levelpath = self.dest_path

        return '.'.join([os.path.join(levelpath, '-'.join(elements)), ext])

    def __init__(self, name):
        self.basename = AppConfig.get_server_name()
        self.name = name
        self.logger = logging.getLogger(self.name)
        self.dry = False

    # @DeprecationWarning
    def stream_watcher(self, stream, error=False, remove_head=False):
        for line in stream:
            line = line.strip()

            if remove_head and line.count(" ") > 1:
                line = " ".join(line.split()[1:])

            if line:
                if error:
                    self.logger.error(line)
                else:
                    self.logger.debug(line)
        if not stream.closed:
            stream.close()

    # @DeprecationWarning
    def stream_watcher_debug_filter(
        self,
        stream,
        filters,
        remove_head=False,
        debug=False,
    ):
        watcher_logger = logging.getLogger(
            '{}.watcher_logger'.format(self.logger.name),
        )
        watcher_logger.propagate = debug

        for line in stream:
            line = line.strip()
            if remove_head and line.count(' ') > 1:
                line = " ".join(line.split()[1:])

            if line:
                for pattern in filters:
                    if re.match(pattern, line):
                        watcher_logger.debug(line)
                        break
                else:
                    self.logger.error(line)

        if not stream.closed:
            stream.close()

    def stream_watcher_filtered(
        self,
        stream,
        filters=None,
        remove_header=False,
        default_level=None,
    ):
        """Наблюдатель за потоком данных.

        Args:
            stream: читаемый поток с данными
            filters (dict): словарь с фильтрами вида { log_level (int) : [pat1 (str), pat2 (str)], ... }
            remove_header (bool): удалять первое слово в строке
            default_level (int): стандартный уровень логгирования

        """
        if filters is not None:
            filter_tuples = [
                (pattern, status) for status, patterns in filters.items()
                for pattern in patterns
            ]
        else:
            filter_tuples = []

        for line in stream:
            line = line.strip()
            if remove_header and ' ' in line:
                # удаление первого слова из строки, если оно единственное
                words = line.split()[1:]
                line = ' '.join(words)

            if not line:
                break

            for pattern, log_level in filter_tuples:
                if re.match(pattern, line):
                    self.logger.log(level=log_level, msg=line)
                    break
            else:
                if default_level:
                    self.logger.log(level=default_level, msg=line)

        if not stream.closed:
            stream.close()

    def start(self):
        """
        Абстрактный метод, в котором делается вся работа.
        :return: возвращает False, если нужно прервать цепочку обработки
        """
        raise NotImplementedError('Should have implemented this')
        return False

    def __repr__(self):
        return '{name}: {attrs}'.format(
            name=self.__class__.__name__,
            attrs=self.__dict__,
        )
