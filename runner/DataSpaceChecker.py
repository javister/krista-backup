# -*- coding: UTF-8 -*-
import subprocess
from runner.Action import Action


class DataSpaceChecker(Action):
    """
    Выводит объем свободного места по разделам в лог.

    """

    def __init__(self, name):
        Action.__init__(self, name)

    def start(self):
        try:
            self.logger.info('Выполняется df -h')
            res = subprocess.Popen('df -h',
                                   stdout=subprocess.PIPE, universal_newlines=True, shell=True).stdout.readlines()
            l = 'Использование разделов сервера:\n'
            for line in res:
                l += line
            self.logger.info(l[:-1])
        except Exception as exc:
            self.logger.error('Ошибка при выполнении: %s', exc)
        return True
