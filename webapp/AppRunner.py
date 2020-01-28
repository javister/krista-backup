# -*- coding: UTF-8 -*-

import logging
import os
import signal
import time

from model.ProcUtil import process_iter


class AppRunner():

    name = 'foo'

    def check_process(self):
        pid = os.getpid()
        for process in process_iter():
            if pid != process.pid and ('KristaBackup.py run %s' % self.name) in process.cmdline:
                return process.pid
        return None

    """
        Абстрактный метод, должен быть переопределен в потомке
    """
    def run_app(self):
        raise NotImplementedError("Should have implemented this")
        return False

    def run(self):

        if self.check_process():
            logging.warning('KristaBackup.py %s уже запущена!' % self.name)
            return

        pid = os.fork()
        if pid == 0:
            logging.debug("In the child process that has the PID {}".format(os.getpid()))
            self.run_app()

    def stop(self):
        pid = self.check_process()
        if pid:
            os.kill(pid, signal.SIGINT)
