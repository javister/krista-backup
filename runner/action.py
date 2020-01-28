# -*- coding: UTF-8 -*-
import logging
import os
import re
from model.YamlConfig import AppConfig


class Action:

    # атрибуты, которые должны быть обязательно заданы в конфиге
    required_attrs = ['name']

    logger = None
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

    def start(self):
        """
        Абстрактный метод, в котором делается вся работа.
        :return: возвращает False, если нужно прервать цепочку обработки
        """
        raise NotImplementedError("Should have implemented this")
        return False
