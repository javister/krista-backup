# -*- coding: UTF-8 -*-

import os
import re

import __main__


class CapturedProcess(object):
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


def check_process(executable_filename, name=''):
    pid = os.getpid()
    occurrence_pattern = '{0} run {1}\\s'.format(
        executable_filename,
        name,
    )
    for process in process_iter():
        if pid != process.pid and re.search(
            occurrence_pattern,
            process.cmdline,
        ):
            return process.pid
    return None


def get_entrypoint_path():
    """Возвращает путь к исполняемому файлу."""
    from .YamlConfig import AppConfig
    dirpath = os.path.realpath(__main__.__file__)
    if AppConfig.is_packed:
        dirpath = os.path.dirname(dirpath)
    return dirpath


def get_executable_filename():
    return os.path.basename(get_entrypoint_path())
