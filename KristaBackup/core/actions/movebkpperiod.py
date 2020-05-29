# -*- coding: UTF-8 -*-

import os
import shutil
import functools
import re

from lib.crontex import CronExpression
from common.YamlConfig import AppConfig

from .action import Action
from .decorators import side_effecting
from .mixins import WalkAppierMixin


class MoveBkpPeriod(Action, WalkAppierMixin):
    """Выполняет перенос файлов по basename.

    Attributes:
        periods (dict): Содержит конфигурацию периодов.
        Пример структуры:
        {
        'weekly': {'cron': '* * * * 0'},
        'yearly': {'path': 'annual'}
        }

        action_list (list): Содержит список basename.

        files_to_move (list): Содержит список файлов для копирования.

    """

    def __init__(self, name):
        super().__init__(name)
        self.files_to_move = []
        self.action_list = []
        self.periods = {}

    def start(self):
        error_caught = False
        self.fill_files_to_move()
        if self.files_to_move:
            for period_name in self.periods:
                period = self.periods.get(period_name)
                if self.validate_time(period_name, period):
                    error_caught |= self.move_backups(period_name, period)

        return not error_caught or self.continue_on_error

    def validate_time(self, period_name, period):
        cron_expr = period.get('cron')
        if not cron_expr:
            self.logger.error(
                'Отсутствует cron выражение для периода %s',
                period_name,
            )
            return False
        try:
            job = CronExpression(cron_expr)
            time_tuple = AppConfig.get_starttime().timetuple()[:5]
            return job.check_trigger(time_tuple)
        except Exception as e:
            self.logger.error(
                'Ошибка при проверке на совпадение времени cron выражению %s, %s',
                cron_expr,
                str(e),
            )
            return False

    def fill_files_to_move(self):
        """Ищет и добавляет файлы для перемещения.

        1. Группирует все файлы с одинаковым basename
        2. Ищет самую новую временную метку в группе
        3. Ищет файлы по паттерну {basename}-{временная метка}*

        """
        for action in self.action_list:
            files = self._fill_files_by_action(action)
            min_date = None
            oldest_files = []

            for signature, group_files in files.items():
                for filepath in group_files:
                    date = action.scheme.retrieve_time_from_name(
                        os.path.basename(filepath),
                        signature[1],
                    )
                    if not date:
                        continue
                    if not min_date or date < min_date:
                        min_date = min(date, min_date or date)
                        oldest_files = [filepath]
                    elif date == min_date:
                        oldest_files.append(filepath)

            if min_date:
                if len(oldest_files) != len(files):
                    self.logger.warning(
                        'Количество групп не соответствует количеству найденных файлов!',
                    )
            else:
                for signature, group_files in files.items():
                    if len(group_files) != 1:
                        self.logger.debug(
                            'Невозможно выбрать файлы для переноса для действия %s',
                            action
                        )
                        break
                else:
                    self.logger.debug(
                        'В каждой группе действия %s по одному файлу',
                        action,
                    )
                    oldest_files = [
                        filepath for _, group_files in files.items()
                        for filepath in group_files
                    ]

            self.files_to_move.extend(oldest_files)

        self.logger.info(
            'Найденные файлы для перемещения: %s', self.files_to_move,
        )

    def move_backups(self, period_name, period):
        """Перемещает бэкапы для определённого периода.

        Перемещение конкретных файлов выполняет метод
        self._move_backup.

        Args:
            period_name (str): название периода
            period (dict): конфигурация периода

        Returns:
            True, если возникла ошибка
        """
        sub_path = period.get('path', period_name)
        files_dest_path = os.path.join(self.dest_path, sub_path)

        self.logger.debug(
            'Каталог назначения для %s: %s',
            period_name,
            files_dest_path,
        )

        if not os.path.exists(files_dest_path):
            self.logger.debug(
                'Каталог %s не существует, попытка создать',
                files_dest_path,
            )
            if not self.dry:
                try:
                    os.makedirs(files_dest_path)
                except Exception as exc:
                    self.logger.error(
                        'Невозможно создать каталог по следующему пути: %s, %s',
                        files_dest_path,
                        exc,
                    )
                    return True
            self.logger.debug(
                'Каталог %s создан',
                files_dest_path,
            )

        for moving_file in self.files_to_move:
            self.logger.debug(
                '[%s, %s]: копирование %s',
                period_name,
                files_dest_path,
                moving_file,
            )
            try:
                self._move_backup(moving_file, files_dest_path)
            except Exception as exc:
                self.logger.error(
                    'Проблема во время копирования файла %s, %s',
                    moving_file,
                    exc,
                )

        return False

    @side_effecting
    def _move_backup(self, moving_file, files_dest_path):
        shutil.copy2(moving_file, files_dest_path)

    def _fill_files_by_action(self, action):
        path = action.generate_dirname()
        files = {}
        patterns = action.get_patterns()
        apply = functools.partial(
            _match_and_add,
            patterns=patterns,
            files=files,
            path=path,
        )
        try:
            self.walk_apply(path, apply, recursive=False, apply_dirs=True)
        except AttributeError:
            self.logger.info('Указаный путь не существует')

        return files


def _match_and_add(filename, path, patterns, files):
    _, file_extension = os.path.splitext(filename)
    file_extension = file_extension or ' '

    for pattern in patterns:
        match = re.match(pattern, filename)
        if not match:
            continue
        if 'ext' in match.groupdict():
            file_extension = match.group('ext')

        signature = (file_extension, pattern)
        filepath = os.path.join(path, filename)
        files.setdefault(signature, []).append(filepath)
        break
