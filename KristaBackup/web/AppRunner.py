# -*- coding: UTF-8 -*-

import logging
import os
import signal

from common.procutil import check_process, get_executable_filename
from common.arguments import constants


class AppRunner():

    name = 'foo'

    """
        Абстрактный метод, должен быть переопределен в потомке
    """

    def run_app(self):
        raise NotImplementedError('Should have implemented this')
        return False

    @property
    def keywords(self):
        exe_filename = get_executable_filename()
        return [self.name, constants.START_OPT_NAME, exe_filename]

    def run(self):
        pid = check_process(self.keywords)
        if pid:
            logging.warning(
                'Процесс %s уже запущен! PID: %s',
                self.name,
                pid,
            )
            return

        self.run_app()

    def stop(self):
        pid = check_process(self.keywords)
        if pid:
            os.kill(pid, signal.SIGINT)
