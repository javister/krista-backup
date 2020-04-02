# -*- coding: UTF-8 -*-


import logging

from .action import Action

stderr_filters = {
    logging.WARNING: {
        '.* target is busy',
    },
    logging.DEBUG: {
        r'\(In some cases useful.*',
        'use the device is found.*',
    },
}


class Umount(Action):
    """Оболочка над umount."""

    def __init__(self, name):
        super().__init__(name)
        self.mnt_point = ''  # точка монтирования
        self.flags = ''  # дополнительные флаги для вызова

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

        stdout_params = {
            'logger': self.logger,
            'default_level': logging.INFO,
        }
        stderr_params = {
            'logger': self.logger,
            'filters': stderr_filters,
            'default_level': logging.ERROR,
        }

        self.logger.info('Выполняется %s', cmdline)
        try:
            self.execute_cmdline(
                cmdline,
                stdout_params=stdout_params,
                stderr_params=stderr_params,
            )
        except Exception as exc:
            self.logger.warning('Ошибка при выполнении umount: %s', exc)
            return self.continue_on_error
        return True
