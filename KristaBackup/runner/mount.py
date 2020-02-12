# -*- coding: UTF-8 -*-

import os
import subprocess
from threading import Thread

from .action import Action


class Mount(Action):
    """Оболочка над mount."""

    mnt_dev = ''  # монтироемое устройство
    mnt_point = ''  # точка монтирования
    fs_type = ''  # тип подключаемой файловой системы
    cred_file = ''  # файл с данными для подключения
    flags = ''    # дополнительные флаги для вызова

    def __init__(self, name):
        super().__init__(self, name)

    def generate_fs_args(self):
        """Возвращает строку для выбора типа файловой системы."""
        if self.fs_type:
            return '-t {0}'.format(self.fs_type)
        return ''

    def generate_options(self):
        """Возвращает опции для подключения.

        На данный момент подерживает только cred_file.
        """
        opts = [self.cred_file]
        checked_opts = [arg for arg in opts if arg]
        # если опции отсутствуют, то вернуть пустую строку
        if checked_opts:
            return '-o {0}'.format(','.join(opts))
        return ''

    def start(self):
        if not self.mnt_dev or not self.mnt_point:
            self.logger(
                'Ошибка при выполнении mount: не указан mnt_dev и/или mnt_point',
            )
            return self.continue_on_error

        cmdline = 'mount {flags} {fs} {mnt_dev} {mnt_point} {options}'.format(
            flags=self.flags,
            fs=self.generate_fs_args(),
            mnt_dev=self.mnt_dev,
            mnt_point=self.mnt_point,
            options=self.generate_options(),
        )

        # создать точку монтирования, если она не существует
        if not os.path.isdir(self.mnt_point):
            os.makedirs(self.mnt_point)

        self.logger.info('Выполняется %s', cmdline)
        try:
            mount = subprocess.Popen(
                cmdline, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True, shell=True,
            )
            stdo = Thread(
                target=self.stream_watcher,
                name='stdout-watcher',
                args=(mount.stdout, False),
            )
            stdo.start()
            stde = Thread(
                target=self.stream_watcher,
                name='stderr-watcher',
                args=(mount.stderr, True),
            )
            stde.start()
            mount.wait()
            stdo.join()
            stde.join()
        except Exception as exc:
            self.logger.error('Ошибка при выполнении mount: %s', exc)
            return self.continue_on_error
        return True
