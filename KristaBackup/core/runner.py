#  -*- coding: UTF-8 -*-

import logging
import sys

from common import arguments
from common.procutil import check_process, get_executable_filename
from common.YamlConfig import AppConfig
from core.action_builder import ActionBuilder
from common.arguments import constants


class Runner:

    def __init__(self, unit_name, dry):
        """

        Args:
            unit_name: Строка, имя запускаемого юнита (задания или действия).
            dry: Логическое значение, включает тестовый режим.
                Только для действий.

        """
        self.logger = logging.getLogger()
        self.actions = []

        self.load(unit_name, dry)
        self.create_actions()

    def load(self, unit_name, dry):
        """Загружает действия из требуемого задания.

        Если нет, то:
        1) Проверяет наличие задания с именем unit_name.
        2) Если находит: читает его действия и создаёт их.
        Если нет: ищет действие с именем unit_name и создаёт его.

        Args:
            unit_name: Строка, имя требуемого юнита. Если передано действие,
                то оно превращается в задание с одним действием.
            dry: Логическое значение, включает тестовый режим.
                Если True, тоюнит автоматически интерпретируется как действие.

        Raises:
            SystemExit, если не удалось найти необходимый юнит.

        """
        appconf = AppConfig.conf()
        task_record = appconf.setdefault('schedule', {}).get(unit_name)

        if task_record is not None and not dry:
            self.action_records = task_record.get('actions')
            if not self.action_records:
                self.logger.error(
                    'Список действий в задании %s пуст',
                    unit_name,
                )
                sys.exit(-1)
        elif unit_name in appconf.get('actions', {}):
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
        all_actions_records = AppConfig.conf().setdefault('actions', {})
        action_builder = ActionBuilder(all_actions_records)

        for action_record in self.action_records:
            dry = False

            if isinstance(action_record, list):
                args = arguments.parse_action_record(action_record)
                action_record = args.action_name
                dry = args.dry

            try:
                action = action_builder(action_record)
            except Exception as exc:
                self.logger.error(
                    'Ошибка при создании действия %s: %s',
                    action_record,
                    exc,
                )
                sys.exit(-1)

            if action is not None:
                if dry:
                    action.dry = dry
                    self.logger.debug('Добавлен флаг dry')
                self.actions.append(action)
                self.logger.debug('Действие добавлено')

    def start_task(self):
        """Запускает последовательное выполнение сформированных действий.

        Если в конфигурации параметр allow_parallel имеет значение
        False, то перед запуском сначала происходит проверка отсутствия
        параллельных процессов выполнения заданий и только потом запуск.
        """
        if not AppConfig.conf().get('allow_parallel', True):
            keywords = [get_executable_filename(), constants.RUN_OPT_NAME]
            pid = check_process(keywords)
            if pid:
                self.logger.error(
                    'Другое задание уже запущено: PID: %s',
                    pid,
                )
                sys.exit(-1)

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
                    'Действие %s выполнено неудачно, выполнение остановлено',
                    action.name,
                )
                break
