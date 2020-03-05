# -*- coding: UTF-8 -*-

import subprocess
from threading import Thread

import logging

from .action import Action

stderr_filters = {
    logging.WARNING: {
        '.* target is busy',
    },
    logging.DEBUG: {
        '\(In some cases useful.*',
        'use the device is found.*',
    },
}


class Umount(Action):
    """Оболочка над umount."""

    mnt_point = ''  # точка монтирования, которую требуется отмонтировать
    flags = ''  # дополнительные флаги для вызова

    def __init__(self, name):
        super().__init__(name)

    def start(self):
        if not self.mnt_point:
            self.logger.warning(
                'Ошибка при выполнении umount: не указан mnt_point',
            )
            return self.continue_on_error

        cmdline = 'umount {flags} {mnt_point}'.format(
            flags=self.flags,
            mnt_point=self.mnt_point,
        )

        self.logger.info('Выполняется %s', cmdline)
        try:
            proc = subprocess.Popen(
                cmdline,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                shell=True,
            )
            stdo = Thread(
                target=self.stream_watcher_filtered,
                name='stdout-watcher',
                kwargs={'stream': proc.stdout, 'default_level': logging.INFO},
            )
            stdo.start()
            stde = Thread(
                target=self.stream_watcher_filtered,
                name='stderr-watcher',
                kwargs={
                    'stream': proc.stderr,
                    'filters': stderr_filters,
                    'default_level': logging.ERROR,
                },
            )
            stde.start()
            proc.wait()

            stdo.join()
            stde.join()
        except Exception as e:
            self.logger.warning('Ошибка при выполнении umount: %s', e)
            return self.continue_on_error
        return True
