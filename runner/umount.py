# -*- coding: UTF-8 -*-

import subprocess
from threading import Thread

from .action import Action


class Umount(Action):
    """
        Оболочка над umount.
    """

    mnt_point = ""      # точка монтирования, которую требуется отмонтировать
    flags = ""          # дополнительные флаги для вызова

    def __init__(self, name):
        Action.__init__(self, name)

    def start(self):
        if not self.mnt_point:
            self.logger.warning(u"Ошибка при выполнении umount: %s" %
                                "не указан mnt_point")
            return self.continue_on_error

        cmdline = 'umount {flags} {mnt_point}'.format(flags=self.flags,
                                                      mnt_point=self.mnt_point)

        try:
            self.logger.info(u"Выполняется %s" % cmdline)
            mount = subprocess.Popen(cmdline, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     universal_newlines=True, shell=True)
            stdo = Thread(target=self.stream_watcher,
                          name='stdout-watcher', args=(mount.stdout, False))
            stdo.start()
            stde = Thread(target=self.stream_watcher,
                          name='stderr-watcher', args=(mount.stderr, True))
            stde.start()
            mount.wait()
            stdo.join()
            stde.join()
        except Exception as e:
            self.logger.warning(u"Ошибка при выполнении umount: %s" % str(e))
            return self.continue_on_error
        return True
