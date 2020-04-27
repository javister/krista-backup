# -*- coding: UTF-8 -*-

import logging
import os

from .action import Action


class Command(Action):
    """Выполнение произвольной команды."""

    def __init__(self, name):
        super().__init__(name)
        self.cmd = ''   # команда
        self.continue_on_error = True

    def execute(self, cmdline):
        """Выполняет shell команду.

        Args:
            cmdline: Строка, shell команда.

        Returns:
            True, если команда выполнена успешно.

        """
        self.logger.info('Выполняется %s', cmdline)

        if not cmdline:
            self.logger.warning('Пустая команда %s', self.name)
            return self.continue_on_error

        stdout_params = {
            'logger': self.logger,
            'default_level': logging.INFO,
        }
        stderr_params = {
            'logger': self.logger,
            'default_level': logging.ERROR,
        }

        try:
            self.execute_cmdline(
                cmdline,
                stdout_params=stdout_params,
                stderr_params=stderr_params,
            )
        except Exception as exc:
            self.logger.warning('Ошибка при выполнении %s: %s', cmdline, exc)
            return False
        return True

    def start(self):
        current_path = os.getcwd()

        os.chdir(self.src_path)
        exec_result = self.execute(self.cmd)
        os.chdir(current_path)

        return exec_result or self.continue_on_error


class Script(Command):
    """Выполнение набора команд."""

    def __init__(self, name):
        super().__init__(name)
        self.cmds = []  # команды
        self.continue_on_error = True

    def start(self):
        exec_result = True
        current_path = os.getcwd()

        if isinstance(self.cmds, list):
            os.chdir(self.src_path)
            for command in self.cmds:
                exec_result &= self.execute(command.strip())
            os.chdir(current_path)
        else:
            self.logger.warning(
                'Неправильный тип в наборе команд, ожидается список: %s',
                self.cmds,
            )
        return exec_result or self.continue_on_error
