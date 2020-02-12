# -*- coding: UTF-8 -*-

import logging
import os
import signal

from model.ProcUtil import check_process
from model.YamlConfig import AppConfig


class AppRunner():

    name = 'foo'

    """
        Абстрактный метод, должен быть переопределен в потомке
    """

    def run_app(self):
        raise NotImplementedError('Should have implemented this')
        return False

    def run(self):

        if check_process(AppConfig.excecutable_filename, self.name):
            logging.warning(
                'Процесс %s %s уже запущен!',
                AppConfig.excecutable_filename,
                self.name,
            )
            return

        pid = os.fork()
        if pid == 0:
            logging.debug(
                'In the child process that has the PID {}'.format(os.getpid()))
            self.run_app()

    def stop(self):
        pid = check_process(AppConfig.excecutable_filename, self.name)
        if pid:
            os.kill(pid, signal.SIGINT)
