#  -*- coding: UTF-8 -*-

import os

from model import Logging, ProcUtil
from model.YamlConfig import AppConfig
from runner import (
    Action, CheckInProgressTicket, CheckLastBackup, Cleaner,
    DataSpaceChecker, Mount, MoveBkpPeriod, PgDump, Rsync,
    SetInProgressTicket, TarArchiver, Umount,
    UnsetInProgressTicket,
)


class ScheduleRunner:

    actions = []

    # Здесь регистрируем типы Action, при этом нужно учитывать порядок наследования, поэтому первым идет Action
    # Здесь используется не словарь, чтобы сохранить порядок наследования
    action_types = (
        ('action', Action),
        ('tar', TarArchiver),
        ('cleaner', Cleaner),
        ('rsync', Rsync),
        ('pgdump', PgDump),
        ('dschecker', DataSpaceChecker),
        ('check_backup', CheckLastBackup),
        ('mount', Mount),
        ('umount', Umount),
        ('move_bkp_period', MoveBkpPeriod),
        ('set_in_progress_ticket', SetInProgressTicket),
        ('unset_in_progress_ticket', UnsetInProgressTicket),
        ('check_in_progress_ticket', CheckInProgressTicket),
    )

    def __init__(self, schedule_name, verbose):
        self.logger = Logging.configure_task_logger(schedule_name, verbose)

        if not AppConfig.conf().schedule:
            self.logger.error('Отсутствует расписание в файле конфигурации')
            exit(-1)

        if not AppConfig.conf().schedule.get(schedule_name, {}):
            self.logger.error(
                'Отсутствует заданное задание %s',
                schedule_name,
            )
            exit(-1)

        self.action_configurations = AppConfig.conf(
        ).schedule[schedule_name].get('actions')

        if not self.action_configurations:
            self.logger.error(
                'Отсутствуют действия для исполнения %s',
                schedule_name,
            )
            exit(-1)

        # Пробегаемся по файлам конфигураций в job_configs и создаем действия
        for action_name in self.action_configurations:
            a = self.create_action(action_name)
            if not a is None:
                self.actions.append(a)

    def create_action(self, action_name):
        """
        Создаем и конфигурируем действие

        :param action_name: имя действия
        :return: Action или None, если не удалось создать/сконфигурировать действие
        """

        action_conf = AppConfig.conf().actions.get(action_name, None)
        if action_conf is None:
            self.logger.warning(
                'Отсутствует описание для действия %s',
                action_name,
            )
            return None

        # Проверяем унаследованные конфигурации

        # Максимальная глубина наследования
        # нужна для прерывания в случае цикличного наследования
        rec = 0

        ancestor = action_conf

        while 'source' in ancestor.keys() and rec < 10:
            ancestor_name = ancestor['source']
            ancestor = AppConfig.conf().actions.get(ancestor_name, None)

            if ancestor is None:
                self.logger.error(
                    'Отсутствует предок %s для action %s, конфиг не рассматривается',
                    ancestor_name,
                    action_name,
                )
                break

            # копируем атрибуты предка
            for attribute in ancestor.keys():
                if attribute not in action_conf.keys():
                    action_conf[attribute] = ancestor[attribute]
            rec += 1

        if rec == 9:
            self.logger.warn(
                'Замечено многократное наследование при формировании %s, возможны ошибки в наследовании',
                action_conf,
            )

        # Проверка существования данного типа действий
        if 'type' not in action_conf.keys():
            self.logger.error(
                'Отсутствует тип в конфигурации действия %s, конфиг не рассматривается',
                action_name,
            )
            return None

        action_conf['name'] = action_name

        # В зависимости от типа в конфиге создаем объект заданного типа
        atypes = dict(self.action_types)

        if action_conf['type'] in atypes.keys():
            action_conf['class'] = atypes[action_conf['type']]
        else:
            self.logger.error(
                'Неопознанный тип действия %s в конфигурации задания %s',
                action_conf['type'],
                action_name,
            )
            return None

        action = action_conf['class'](action_name)
        self.logger.debug('Конфигурирование объекта %s', action)

        if action_conf['type'] in {'cleaner'}:
            source = AppConfig.conf().actions.get(action_conf['source'], None)
            if source:
                action_conf['parent_type'] = source.get('type', None)
                if not action_conf['parent_type']:
                    self.logger.info(
                        'У предка %s не указан тип, поэтому чистка будет выполняться по basename.',
                        action)

        for known_type in atypes.keys():
            if isinstance(action, atypes.get(known_type)):
                if not self.configure_action(atypes[known_type], action, action_conf):
                    return None

        self.logger.info('Сконфигурирован объект %s', action)

        return action

    def configure_action(self, cls, obj, conf=None):
        """ Устанавливает значение объекту actions из конфига. """
        attributes_names = conf.keys()

        # Проверяем наличие обязательных атрибутов в конфиге
        if 'required_attrs' in cls.__dict__.keys():
            warnings = []
            for req in obj.required_attrs:
                if req not in attributes_names:
                    warnings.append(req)
            if len(warnings) > 0:
                for w in warnings:
                    self.logger.error(
                        'Отсутствует обязательный параметр %s в конфигурации [%s]',
                        w, obj.name)
                return False

        if cls != obj.__class__:
            return True

        # Пробегаемся по записям конфига и читаем атрибуты из него в объект
        for attribute_name in attributes_names:
            attr = getattr(obj, attribute_name, None)
            attr_value = None

            # Пробегаемся по записям конфига и читаем атрибуты из него в объект

            # Если атрибут класса имеет стандартный тип list,а значение
            # из конфигурации имеет тип не list, то строка будет разбита
            # на лист строк, которые прежде были разделены запятой
            if (isinstance(attr, list) and not isinstance(conf[attribute_name], list)):
                attr_value = [
                    a_value.strip()
                    for a_value in str(conf[attribute_name]).split(',')
                ]
            else:
                attr_value = conf[attribute_name]
            setattr(obj, attribute_name, attr_value)
            self.logger.debug(
                '%s %s %s',
                obj.name,
                attribute_name,
                attr_value,
            )

        return True

    def start_task(self):
        """Запускает последовательное выполнение сформированных действий.

        Если в конфигурации параметр allow_parallel имеет значение
        False, то перед запуском сначала происходит проверка отсутствия
        параллельных процессов выполнения заданий и только потом запуск.
        """
        def check_running_task(process):
            if ('python3' in process.cmdline
                    and 'KristaBackup' in process.cmdline
                    and 'web_module' not in process.cmdline):
                if pid > process.pid and 'run' in process.cmdline:
                    return True
            return False

        if ('allow_parallel' in AppConfig.conf().__dir__()
                and not AppConfig.conf().allow_parallel):
            pid = os.getpid()
            for process in ProcUtil.process_iter():
                if check_running_task(process):
                    self.logger.error(
                        'Другое задание уже запущено: PID: %s, Задание: %s',
                        process.pid,
                        process.cmdline.split()[-1],
                    )
                    exit(-1)

        for action in self.actions:
            self.logger.info('Запускается действие %s', action.name)
            if action.start():
                self.logger.info('Выполнено действие %s', action.name)
            else:
                self.logger.error(
                    'Ошибка при выполнении действия %s, выполнение задания прервано',
                    action.name,
                )
                exit(-1)
