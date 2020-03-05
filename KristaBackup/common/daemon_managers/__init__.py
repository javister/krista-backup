# -*- encoding: utf-8 -*-

import os
import sys

from ..YamlConfig import AppConfig
from common import procutil

try:
    CURRENT_USER = os.getlogin()
except OSError:
    CURRENT_USER = 'root'


def generate_command_line(task):
    """Генерирует командную строку для запуска приложения.

    Формат: {интерпретатор} {полный путь к исп. файлу} run {задание}
    """
    return '{interpreter} {executable} run {task_to_run}'.format(
        interpreter=sys.executable,
        executable=procutil.get_entrypoint_path(),
        task_to_run=task,
    )
