# -*- coding: UTF-8 -*-

import os


class CapturedProcess:
    """Класс для хранения информации о записанном процессе."""

    def __init__(self, pid=None, name=None, cmdline=None):
        self.pid = pid
        self.name = name
        self.cmdline = cmdline


def process_iter():
    """Возвращает генератор с информацией о текущих процессах."""
    pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
    for pid in pids:
        try:
            with open(os.path.join('/proc', pid, 'cmdline'), 'rb') as p_info:
                cmdline = p_info.read().decode('utf-8').split('\0')
                process = CapturedProcess(
                    int(pid),
                    cmdline[0],
                    ' '.join(cmdline),
                )
                yield process
        except IOError:  # proc has already terminated
            pass
