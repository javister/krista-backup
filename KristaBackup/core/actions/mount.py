# -*- coding: UTF-8 -*-

import os
import subprocess
from threading import Thread
import logging

from common import sysutil

from .action import Action
from .decorators import side_effecting


class Mount(Action):
    """Оболочка над mount."""

    mnt_dev = ''  # монтироемое устройство
    mnt_point = ''  # точка монтирования
    fs_type = ''  # тип подключаемой файловой системы
    flags = ''    # дополнительные флаги для вызова

    def __init__(self, name):
        super().__init__(name)

    def generate_fs_args(self):
        """Возвращает строку для выбора типа файловой системы."""
        if self.fs_type:
            return '-t {0}'.format(self.fs_type)
        return ''

    def generate_cmdline(self):
        """Возвращает полную команду для подключения устройства."""
        return 'mount {flags} {fs} {mnt_dev} {mnt_point}'.format(
            flags=self.flags,
            fs=self.generate_fs_args(),
            mnt_dev=self.mnt_dev,
            mnt_point=self.mnt_point,
        )

    @side_effecting
    def exececute_cmdline(self, cmdline):
        """Выполняет командную строку.

        Args:
            cmdline (str): командная строка для выполнения

        """
        rsync = subprocess.Popen(
            cmdline,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        )

        stdo = Thread(
            target=self.stream_watcher_filtered,
            name='stdout-watcher',
            kwargs={
                'stream': rsync.stdout,
                'default_level': logging.INFO,
            },
        )
        stdo.start()

        stde = Thread(
            target=self.stream_watcher_filtered,
            name='stderr-watcher',
            kwargs={
                'stream': rsync.stderr,
                'default_level': logging.ERROR,
            },
        )
        stde.start()

        rsync.wait()
        stdo.join()
        stde.join()

    def start(self):
        if not self.mnt_dev or not self.mnt_point:
            self.logger.error(
                'Ошибка при выполнении mount: не указан mnt_dev и/или mnt_point',
            )
            return self.continue_on_error

        if os.path.ismount(self.mnt_point):
            # проверка доступности монтирования
            self.logger.info(
                'Точка монтирования %s уже используется',
                self.mnt_point,
            )
            current_mount_dev = sysutil.get_mount_dev(self.mnt_point)
            if current_mount_dev == self.mnt_dev:
                # если требуемое устройство смонтировано в требуемую точку
                self.logger.info(
                    'Требуемое устройство %s уже смонтировано',
                    self.mnt_dev,
                )
                return True
            self.logger.error(
                'Смонтировано устройство %s, вместо требуемого %s',
                current_mount_dev,
                self.mnt_dev,
            )
            return self.continue_on_error

        # создать точку монтирования, если она не существует
        if not os.path.isdir(self.mnt_point):
            os.makedirs(self.mnt_point)

        cmdline = self.generate_cmdline()
        self.logger.info('Выполняется %s', cmdline)

        try:
            self.exececute_cmdline(cmdline)
        except Exception as exc:
            self.logger.error('Ошибка при выполнении mount: %s', exc)
            return self.continue_on_error

        return True
