#  -*- coding: UTF-8 -*-

import sys

from common import Logging, arguments
from common.procutil import check_process, get_executable_filename
from common.YamlConfig import AppConfig

from .actions import action_types


class Runner:

    def __init__(self, unit_name, verbose, dry):
        self.logger = Logging.configure_logger(unit_name, verbose)
        self.actions = []

        self.load(unit_name, dry)
        self.create_actions()

    def load(self, unit_name, dry):
        """Загружает требуемое задание или действие.

        Проверяет наличие задания с именем unit_name.
        Если находит: читает его действия и создаёт их.
        Если нет: ищет действие с именем unit_name и создаёт его.

        Args:
            unit_name (str): имя требуемого задания/действия

        """
        task_record = AppConfig.conf().setdefault('schedule', {}).get(unit_name)

        if task_record is not None and not dry:
            self.action_records = task_record.get('actions')
            if not self.action_records:
                self.logger.error(
                    'Отсутствуют действия для исполнения в задании %s',
                    unit_name,
                )
                sys.exit(-1)
        elif unit_name in AppConfig.conf().get('actions', {}):
            action_record = [unit_name]
            if dry:
                action_record.append('--dry')
            self.action_records = [action_record]
        elif dry:
            self.logger.error(
                'Отсутствует требуемое действие %s',
                unit_name,
            )
            sys.exit(-1)
        else:
            self.logger.error(
                'Отсутствует требуемое задание/действие %s',
                unit_name,
            )
            sys.exit(-1)

    def create_actions(self):
        """Создаёт действия по описанию из self.action_records.

        Вызывает self._create_action для всех записей из self.action_records
        и делает дополнительную обработку (добавляет флаг --dry).

        """
        for action_record in self.action_records:
            dry = False

            if isinstance(action_record, list):
                args = arguments.parse_action_record(action_record)
                action_record = args.action_name
                dry = args.dry

            try:
                action = self._create_action(action_record)
            except Exception as exc:
                self.logger.error(
                    'Ошибка при создании действия %s: %s',
                    action_record,
                    exc,
                )
            else:
                if action is not None:
                    if dry:
                        action.dry = dry
                        self.logger.debug('Добавлен флаг dry')
                    self.actions.append(action)
                    self.logger.debug('Действие добавлено')

    def _create_action(self, action_name):
        """Создает и конфигурирует действие.

        Arguments:
            action_name (str): имя действия
        Returns:
            Action или None, если не удалось создать/сконфигурировать
            действие

        """
        action_records = AppConfig.conf().setdefault('actions', {})
        action_conf = action_records.get(action_name)

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
            ancestor = action_records.get(ancestor_name, None)

            if ancestor is None:
                self.logger.error(
                    'Отсутствует предок %s для action %s, действие выполнено не будет',
                    ancestor_name,
                    action_name,
                )
                return None

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
        atypes = dict(action_types)

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
        self.logger.debug('Конфигурирование действия %s', action_name)

        if action_conf['type'] in {'cleaner'}:
            source = action_records.get(action_conf['source'], None)
            if source:
                action_conf['parent_type'] = source.get('type', None)
                if not action_conf['parent_type']:
                    self.logger.info(
                        'У предка %s не указан тип, поэтому чистка будет выполняться по basename.',
                        action,
                    )

        for known_type in atypes.keys():
            if isinstance(action, atypes.get(known_type)):
                if not self.configure_action(atypes[known_type], action, action_conf):
                    return None

        self.logger.info(
            'Сконфигурировано действие %s:\n%s',
            action_name,
            action,
        )

        return action

    def configure_action(self, cls, obj, conf=None):
        """Устанавливает значение объекту actions из конфига."""
        attributes_names = conf.keys()
        warnings = []

        # Проверяем наличие обязательных атрибутов в конфиге
        for req in obj.required_attrs:
            if req not in attributes_names:
                warnings.append(req)
        if warnings:
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

        return True

    def start_task(self):
        """Запускает последовательное выполнение сформированных действий.

        Если в конфигурации параметр allow_parallel имеет значение
        False, то перед запуском сначала происходит проверка отсутствия
        параллельных процессов выполнения заданий и только потом запуск.
        """
        if not AppConfig.conf().get('allow_parallel', True):
            process = check_process(get_executable_filename())
            if process:
                self.logger.error(
                    'Другое задание уже запущено: PID: %s, Задание: %s',
                    process.pid,
                    process.cmdline.split()[-1],
                )

        for action in self.actions:
            self.logger.info('Запускается действие %s', action.name)
            try:
                success = action.start()
            except KeyboardInterrupt:
                self.logger.warning('Выполнение прервано нажатием Ctrl+C')
                break

            if success:
                self.logger.info('Выполнено действие %s', action.name)
            else:
                self.logger.error(
                    'Ошибка при выполнении действия %s, выполнение задания прервано',
                    action.name,
                )
                sys.exit(-1)
