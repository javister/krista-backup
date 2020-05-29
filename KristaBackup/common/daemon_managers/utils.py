import sys

from common import procutil
from common.arguments.constants import RUN_OPT_NAME


def generate_command_line(task):
    """Генерирует командную строку для запуска приложения.

    Формат: {интерпретатор} {полный путь к исп. файлу} {команда запуска} {задание}
    Например: /usr/bin/python3 /opt/KristaBackup/KristaBackup.py run task

    Args:
        task: Строка, имя задания.

    Returns:
        str, команда для зпуска

    """
    if getattr(sys, 'frozen', False):
        pattern = '{interpreter} {run} {task_to_run}'
    else:
        pattern = '{interpreter} {executable} {run} {task_to_run}'
    return pattern.format(
        interpreter=sys.executable,
        executable=procutil.get_entrypoint_path(),
        run=RUN_OPT_NAME,
        task_to_run=task,
    )
