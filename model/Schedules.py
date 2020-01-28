#  -*- coding: UTF-8 -*-

import os

# Если это потребуется - добавить импорт в соответствующий метод
# from flask import logging

from lib.crontab import CronSlices, CronTab
from model.Logging import get_trigger_filepath
from model.YamlConfig import AppConfig, ConfigError

"""
   Работа с CRON
"""

DEFAULT_CRON_USER = 'root'

def get_cron_filename(name):
    return os.path.join(AppConfig.conf().cron.get('cron_path', '/etc/cron.d'),
                        name)


def is_active(name):
    user = AppConfig.conf().cron.get('cron_user', 'root')
    try:
        cron = CronTab(user)
        for job in cron:
            if job.comment == name:
                return True
    except OSError as e:
        raise ConfigError('В системе отсутствует пользователь %s или не задан crontab для этого пользователя' % (user))
    return False


def deactivate_schedule(name):
    if name == 'all':
        schedules = get_schedules()
    else:
        schedules = {name: ''}
    for name, _ in schedules.items():
        try:
            cron = CronTab(user=AppConfig.conf().cron.get('cron_user', DEFAULT_CRON_USER))
        except Exception:
            cron = CronTab(user=DEFAULT_CRON_USER)
        for job in cron:
            if job.comment == name:
                cron.remove(job)
                cron.write()


def activate_schedule(name, entrypoint):
    """Позволяет активировать расписание/расписания.
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

        # [путь к интерпретатору] [путь к файлу запуска] [run] [имя расписания]
        exec_list.append(
            'python3 {0} run {1} 2>&1'
            .format(entrypoint, name))

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
        schedules = get_schedules()
    else:
        schedule = get_schedule(name)
        if schedule is None:
            raise ConfigError(
                'Ошибка при добавлении задания в cron: нет задания с именем {0}'
                .format(name),
            )
        schedules = {name: schedule}

    for name, schedule in schedules.items():
        try:
            crontab = CronTab(user=AppConfig.conf().cron.get('cron_user', DEFAULT_CRON_USER))
        except Exception:
            crontab = CronTab(user=DEFAULT_CRON_USER)

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


"""
   Работа с заданиями
"""


def get_schedules():
    schedules = {}
    for s_name in sorted(AppConfig.conf().schedule.keys()):
        schedule_conf = AppConfig.conf().schedule[s_name]
        schedule_conf['active'] = is_active(s_name)
        schedules[s_name] = schedule_conf
    return schedules


def get_schedule(name):
    return AppConfig.conf().schedule.get(name, None)


def update_schedule(name, cron, descr, actions):
    ac = []
    for action in actions.split(','):
        ac.append(action.strip())
    AppConfig.conf().schedule[name] = {'descr': descr, 'cron': cron, 'actions': ac}
    AppConfig._config.storeAll()
    if is_active(name):
        activate_schedule(name)


def delete_schedule(name):
    deactivate_schedule(name)
    AppConfig.conf().schedule.pop(name, None)
    AppConfig._config.storeAll()


def get_schedule_actions(schedule):
    if AppConfig.conf().actions is None or len(AppConfig.conf().actions) <= 0:
        raise ConfigError('Отсутствует описания actions в конфигурации задачи.')
    res = []
    actionslist = AppConfig.conf().schedule.get('actions', [])
    for action in actionslist:
        if action in AppConfig.conf().jobs.keys():
            res.append(AppConfig.conf().jobs[action])
        else:
            raise ConfigError(
                'Отсутствует описание action {} из задания {}.'.format(
                    action,
                    schedule,
                )
            )
    return res
