import sys

from common import procutil
from common.arguments.constants import RUN_OPTS


def generate_command_line(task):
    """Генерирует командную строку для запуска приложения.

    Формат: {интерпретатор} {полный путь к исп. файлу} {команда запуска} {задание}
    Например: /usr/bin/python3 /opt/KristaBackup/KristaBackup.py run task

    Args:
        task: Строка, имя задания.

    Returns:
        str, команда для зпуска

    """
    return '{interpreter} {executable} {run} {task_to_run}'.format(
        interpreter=sys.executable,
        executable=procutil.get_entrypoint_path(),
        run=next(iter(RUN_OPTS)),
        task_to_run=task,
    )
