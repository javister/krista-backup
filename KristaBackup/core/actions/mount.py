# -*- coding: UTF-8 -*-

import logging
import os

from common import sysutil

from .action import Action


class Mount(Action):
    """Оболочка над mount."""

    def __init__(self, name):
        super().__init__(name)
        self.mnt_dev = ''  # монтироемое устройство
        self.mnt_point = ''  # точка монтирования
        self.fs_type = ''  # тип подключаемой файловой системы
        self.flags = ''    # дополнительные флаги для вызова

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

    def process_busy_mnt_point(self):
        """Обработка случая, когда точка уже смонтирована.

        Returns:
            True, если используется требуемое устройство.

        """
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
        return False

    def start(self):
        if not self.mnt_dev:
            self.logger.error(
                'Ошибка при выполнении mount: не указан mnt_dev',
            )
            return self.continue_on_error

        if not self.mnt_point:
            self.logger.error(
                'Ошибка при выполнении mount: не указан mnt_point',
            )
            return self.continue_on_error

        if os.path.ismount(self.mnt_point):
            return self.process_busy_mnt_point() or self.continue_on_error

        # создать точку монтирования, если она не существует
        if not os.path.isdir(self.mnt_point):
            self.logger.debug(
                'Создаю отсутствующую точку монтирования %s',
                self.mnt_point,
            )
            if not self.dry:
                os.makedirs(self.mnt_point)
            self.logger.debug('Точка монтирования успешно создана.')

        cmdline = self.generate_cmdline()
        stdout_params = {
            'logger': self.logger,
            'default_level': logging.INFO,
        }
        stderr_params = {
            'logger': self.logger,
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
            self.logger.error('Ошибка при выполнении mount: %s', exc)
            return self.continue_on_error

        return True
