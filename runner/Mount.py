# -*- coding: UTF-8 -*-
import subprocess
import os
from threading import Thread
from runner.Action import Action


class Mount(Action):
    """
        Оболочка над mount.
    """

    mnt_dev = ""             # монтироемое устройство
    mnt_point = ""           # точка монтирования
    fs_type = ""             # тип подключаемой файловой системы
    cred_file = ""           # файл с данными для подключения
    flags = ""               # дополнительные флаги для вызова

    def __init__(self, name):
        Action.__init__(self, name)

    def generate_fs_args(self):
        if self.fs_type:
            return "-t {}".format(self.fs_type)
        return ""

    # поддерживает только cred_file
    # на данный момент остальные не требуются
    def generate_options(self):
        opts = [self.cred_file]
        checked_opts = [arg for arg in opts if arg]
        # если опции отсутствуют, то вернуть пустую строку
        if checked_opts:
            return "-o {}".format(",".join(opts))
        return ""

    def start(self):
        if not self.mnt_dev or not self.mnt_point:
            self.logger(
                'Ошибка при выполнении mount: не указан mnt_dev и/или mnt_point'
            )
            return self.continue_on_error

        cmdline = 'mount {flags} {fs} {mnt_dev} {mnt_point} {options}'.format(
            flags=self.flags,
            fs=self.generate_fs_args(),
            mnt_dev=self.mnt_dev,
            mnt_point=self.mnt_point,
            options=self.generate_options()
        )
        # создать точку монтирования, если она не существует
        if not os.path.isdir(self.mnt_point):
            os.makedirs(self.mnt_point)

        try:
            self.logger.info('Выполняется %s', cmdline)
            mount = subprocess.Popen(
                cmdline, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True, shell=True
            )
            stdo = Thread(
                target=self.stream_watcher,
                name='stdout-watcher', args=(mount.stdout, False)
            )
            stdo.start()
            stde = Thread(
                target=self.stream_watcher,
                name='stderr-watcher', args=(mount.stderr, True)
            )
            stde.start()
            mount.wait()
            stdo.join()
            stde.join()
        except Exception as exc:
            self.logger.error('Ошибка при выполнении mount: %s', exc)
            return self.continue_on_error
        return True
