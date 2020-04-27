#  -*- coding: UTF-8 -*-

"""Модуль для работы с crontab.

Данный модуль содержит методы для добавления и удаления
заданий в crontab.
"""

import os

from common import Logging
from common.YamlConfig import AppConfig, ConfigError
from lib.crontab import CronSlices, CronTab

from . import CURRENT_USER
from .utils import generate_command_line

CRONTAB_ERRORLOG_FILENAME = 'crontab_errorlog.log'

class CrontabManager:
    """Класс-адаптер для работы с crontab."""

    def is_active(self, name):
        """Проверяет активно ли текущее задание.

        Args:
            name: Строка, имя задания

        Returns:
            bool, активно или нет

        Raises:
            OSError: нет доступа к crontab необходимого пользователя

        """
        user = AppConfig.conf().get('cron', {}).get('cron_user', CURRENT_USER)
        try:
            cron = CronTab(user)
        except OSError as exc:
            exc = OSError(exc)
            exc.__cause__ = None
            raise exc

        for job in cron:
            if job.comment == name:
                return True
        return False

    def deactivate_task(self, name):
        if name == 'all':
            schedules = self.get_tasks_with_info()
        else:
            schedules = {name: ''}
        for name, _ in schedules.items():
            cron = CronTab(
                user=AppConfig.conf().get('cron').get(
                    'cron_user',
                    CURRENT_USER,
                ),
            )
            for job in cron:
                if job.comment == name:
                    cron.remove(job)
                    cron.write()

    def activate_task(self, name):
        """Позволяет активировать одно или все задания.

        Args:
            name (str): имя задания, если имеет значение "all", то
                будут задействованы все задания.

        Raises:
            ConfigErorr: Если отсутствует задание с данным именем.

        """
        if name == 'all':
            schedules = self.get_tasks_with_info()
        else:
            schedule = self.get_task(name)
            if schedule is None:
                raise ConfigError(
                    'Задания с именем {0} отсутствует'.format(name),
                )
            schedules = {name: schedule}

        for name, schedule in schedules.items():
            crontab = CronTab(
                user=AppConfig.conf().get('cron').get(
                    'cron_user',
                    CURRENT_USER,
                ),
            )
            self._clean_crontab_by_comment(crontab, name)

            cron_time = schedule.get('cron', None)
            if cron_time and not CronSlices.is_valid(cron_time):
                raise ConfigError(
                    'Неверно указано время в задании {0}'.format(name),
                )

            if schedule.get('all_fields_match', None):
                cron_time = cron_time.split()
                job = crontab.new(
                    command=self._generate_command(
                        name=name,
                        wdays=self._parse_cron_wday_field(cron_time[-1]),
                    ),
                    comment=name,
                )
                cron_time[-1] = '*'
                cron_time = ' '.join(cron_time)
            else:
                job = crontab.new(
                    command=self._generate_command(name),
                    comment=name,
                )

            if (cron_time):
                job.setall(cron_time)
            crontab.write()

    def get_tasks_with_info(self):
        """Возвращает словарь с заданиями и информацией о них.

        Returns:
            tasks (dict) с записями вида
                task_name : {'is_active' : bool, \*\*task_configuration}

        """
        tasks = {}
        for taskname in sorted(AppConfig.conf().get('schedule').keys()):
            task_configuration = self.get_task(taskname)
            try:
                task_configuration['active'] = self.is_active(taskname)
            except OSError:
                task_configuration['active'] = None
            tasks[taskname] = task_configuration
        return tasks

    def get_task(self, name):
        """Возвращает описание задания из конфигурации.

        Args:
            name: Строка, имя задания.

        Returns:
            dict

        """
        return AppConfig.conf().get('schedule').get(name, None)

    def update_task(self, name, cron, descr, actions):
        actions = [action.strip() for action in actions.split(',')]

        AppConfig.conf().get('schedule')[name] = {
            'descr': descr,
            'cron': cron,
            'actions': actions,
        }
        AppConfig._config.storeAll()
        if self.is_active(name):
            self.activate_task(name)

    def delete_task(self, name):
        self.deactivate_task(name)
        AppConfig.conf().get('schedule').pop(name, None)
        AppConfig._config.storeAll()

    def _clean_crontab_by_comment(self, crontab, comment):
        for job in crontab:
            if job.comment == comment:
                crontab.remove(job)
                crontab.write()

    def _generate_command(self, name, wdays=None):
        """Генерирует полную команду для запуска.

        Также добавляет проверку дня недели.

        Если в конфигурации указан триггер, то на него будет
        добавлен конвейер для ловли ошибок.

        Args:
            name: Строка, имя задания.
            wdays: Лист с днями для запуска.

        Returns:
            Строка запуска.

        """
        exec_list = []
        if wdays:
            conditions = list(
                map(
                    # f(x) = (x - 7) % 7:
                    # приводит 7 день недели к 0,
                    # остальные дни не меняет
                    lambda day:
                        r'$(date "+\%u") -eq {0}'.format((day - 7) % 7),
                        wdays,
                ),
            )
            wday_checker = '/usr/bin/test {0}'.format(' -o '.join(conditions))
            exec_list.append(wday_checker)

        exec_list.append(
            '{cmd} 2>&1'.format(
                cmd=generate_command_line(name),
            ),
        )
        # добавление строки запуска с редиректом stderr в stdout

        command = ' && '.join(exec_list)

        errorlog_filepath = os.path.join(
            Logging.get_log_dirpath(),
            CRONTAB_ERRORLOG_FILENAME,
        )

        command = '{0} | /usr/bin/tee {1}'.format(command, errorlog_filepath)

        trigger_filepath = Logging.get_trigger_filepath()
        if trigger_filepath:
            # Если установлен путь к zabbix триггеру
            trigger_handling = 'xargs -r -0 sh -c "echo ERROR > {0}"'.format(
                trigger_filepath,
            )
            command = '{0} | {1}'.format(command, trigger_handling)
        return command

    def _parse_cron_wday_field(self, field):
        if field == '*':
            return list(range(7))
        elif '/' in field:
            raise ConfigError(
                'Ошибка при добавлении расписания в crontab:'
                'оператор "/" не поддерживается',
            )

        ranges = [
            list(map(int, range_.split('-'))) for range_ in field.split(',')
        ]
        # вытаскивает границы промежутков (например, '0-3' => [0, 3])

        return [
            day_number for range_ in ranges
            for day_number in range(range_[0], range_[-1] + 1)
        ]  # конвертирует промежутки в числа и объединяет в один лист
