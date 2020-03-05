#  -*- coding: UTF-8 -*-

"""Модуль для работы с crontab.

Данный модуль содержит методы для добавления и удаления
заданий в crontab.
"""

from lib.crontab import CronSlices, CronTab
from common.Logging import get_trigger_filepath
from common.YamlConfig import AppConfig, ConfigError

from . import CURRENT_USER, generate_command_line


def is_active(name):
    user = AppConfig.conf().get('cron', {}).get('cron_user', CURRENT_USER)

    try:
        cron = CronTab(user)
        for job in cron:
            if job.comment == name:
                return True
    except OSError as exc:
        raise ConfigError(exc)
    return False


def deactivate_task(name):
    if name == 'all':
        schedules = get_tasks_with_info()
    else:
        schedules = {name: ''}
    for name, _ in schedules.items():
        try:
            cron = CronTab(
                user=AppConfig.conf().get('cron').get(
                    'cron_user',
                    CURRENT_USER,
                ),
            )
        except Exception:
            cron = CronTab(user=CURRENT_USER)
        for job in cron:
            if job.comment == name:
                cron.remove(job)
                cron.write()


def activate_task(name):
    """Позволяет активировать одно или все задания.

    args:
        name (str): имя задания, если имеет значение "all", то
            будут задействованы все задания.

    """
    def generate_command(wdays=None):
        exec_list = []
        if wdays:
            conditions = list(
                map(
                    lambda day: '$(date "+\\%u") -eq {}'
                    # f(x) = (x - 7) % 7:
                    # приводит 7 день недели к 0,
                    # остальные дни не меняет
                    .format((day - 7) % 7),
                    wdays))
            wday_checker = '/usr/bin/test {}'.format(' -o '.join(conditions))
            exec_list.append(wday_checker)

        # строка для запуска расписания с редиректом stderr в stdout
        exec_list.append('{cmd} 2>&1'.format(cmd=generate_command_line(name)))

        command = ' && '.join(exec_list)
        trigger_filepath = get_trigger_filepath()

        if trigger_filepath:  # Если установлен путь к zabbix триггеру
            trigger_handling = 'xargs -r -0 sh -c "echo ERROR > {0}"'.format(
                trigger_filepath)
            command = '{0} | {1}'.format(command, trigger_handling)
        return command

    def clean_crontab_by_comment(comment):
        for job in crontab:
            if job.comment == comment:
                crontab.remove(job)
                crontab.write()

    def parse_cron_wday_field(field):
        if field == '*':
            return list(range(7))
        elif '/' in field:
            raise ConfigError(
                'Ошибка при добавлении расписания в cron: не поддерживается'
                'формат cron wday в расписании с именем {}'.format(name))
        # вытаскивает границы промежутков из строки fields
        ranges = [list(map(int, x.split('-'))) for x in field.split(',')]
        # создаёт промежутки и объединяет в один лист
        numbers = [value for a in ranges for value in range(a[0], a[-1] + 1)]

        return numbers

    if name == 'all':
        schedules = get_tasks_with_info()
    else:
        schedule = get_task(name)
        if schedule is None:
            raise ConfigError(
                'Ошибка при добавлении задания в cron: нет задания с именем {0}'
                .format(name),
            )
        schedules = {name: schedule}

    for name, schedule in schedules.items():
        try:
            crontab = CronTab(user=AppConfig.conf().get(
                'cron').get('cron_user', CURRENT_USER))
        except Exception:
            crontab = CronTab(user=CURRENT_USER)

        clean_crontab_by_comment(name)

        cron_time = schedule.get('cron', None)
        if cron_time and not CronSlices.is_valid(cron_time):
            raise ConfigError(
                'Ошибка при добавлении расписания в cron: нет указано/неверно'
                'указано время в расписании с именем {0}'.format(name)
            )

        if schedule.get('all_fields_match', None):
            cron_time = cron_time.split()
            job = crontab.new(
                command=generate_command(parse_cron_wday_field(cron_time[-1])),
                comment=name,
            )
            cron_time[-1] = '*'
            cron_time = ' '.join(cron_time)
        else:
            job = crontab.new(command=generate_command(), comment=name)

        if (cron_time):
            job.setall(cron_time)
        crontab.write()


def get_tasks_with_info():
    """Возвращает словарь с заданиями и информацией о них.

    Returns:
        tasks (dict): содержит записи вида
            task_name : {'is_active' : bool, **task_configuration}.

    """
    tasks = {}
    for taskname in sorted(AppConfig.conf().get('schedule').keys()):
        task_configuration = get_task(taskname)
        task_configuration['active'] = is_active(taskname)
        tasks[taskname] = task_configuration
    return tasks


def get_task(name):
    return AppConfig.conf().get('schedule').get(name, None)


def update_task(name, cron, descr, actions):
    actions = [action.strip() for action in actions.split(',')]

    AppConfig.conf().get('schedule')[name] = {
        'descr': descr,
        'cron': cron,
        'actions': actions,
    }
    AppConfig._config.storeAll()
    if is_active(name):
        activate_task(name)


def delete_task(name):
    deactivate_task(name)
    AppConfig.conf().get('schedule').pop(name, None)
    AppConfig._config.storeAll()
