# -*- coding: UTF-8 -*-

import logging
import os
import signal

from common.procutil import check_process, get_executable_filename
from common.YamlConfig import AppConfig


class AppRunner():

    name = 'foo'

    """
        Абстрактный метод, должен быть переопределен в потомке
    """

    def run_app(self):
        raise NotImplementedError('Should have implemented this')
        return False

    def run(self):
        exe_filename = get_executable_filename()
        pid = check_process(exe_filename, self.name)
        if pid:
            logging.warning(
                'Процесс %s %s уже запущен! PID: %s',
                exe_filename,
                self.name,
                pid,
            )
            return

        pid = os.fork()
        if pid == 0:
            logging.debug(
                'In the child process that has the PID {}'.format(os.getpid()))
            self.run_app()

    def stop(self):
        exe_filename = get_executable_filename()
        pid = check_process(exe_filename, self.name)
        if pid:
            os.kill(pid, signal.SIGINT)
