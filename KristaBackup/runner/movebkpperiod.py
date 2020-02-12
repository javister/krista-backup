# -*- coding: UTF-8 -*-

import datetime
import glob
import os
import shutil

from lib.crontex import CronExpression
from model.YamlConfig import AppConfig

from .action import Action


class MoveBkpPeriod(Action):
    """Выполняет перенос файлов по basename.

    Attributes:
        periods (dict): Содержит конфигурацию периодов.
        Пример структуры:
        {
        'weekly': {'cron': '* * * * 0'},
        'yearly': {'path': 'annual'}
        }

        basename_list (list): Содержит список basename.

        files_to_move (list): Содержит список файлов для копирования.

    """

    basename_list = None
    periods = {}
    files_to_move = None

    def __init__(self, name):
        super().__init__(name)

    def start(self):
        for period_name in self.periods:
            period = self.periods[period_name]
            if self.validate_time(period_name, period):
                self.move_backups(period_name, period)

        return True

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

    def retrieve_time_from_filepath(self, filepath):
        filename = os.path.basename(filepath)

        if '.' in filename:
            dot_index = filename.index('.')
            filepath_noext = filepath[:dot_index - len(filename)]
        else:
            filepath_noext = filepath

        splitted = filepath_noext.split("-")
        for part in reversed(splitted):
            try:
                if datetime.datetime.strptime(part, AppConfig.get_filename_dateformat()):
                    return part
            except Exception:
                pass

        self.logger.error('Date mark not found in %s', filepath)

    def get_files_to_move(self):
        """
        Если files_to_move не None, то возвращает его значение.

        В противном случае вызывает собирает файлы и добавляет их
        в files_to_move.

        """

        def select_files():
            """
            Собирает все файлы с basename, ищет самую старую временную метку в
            найденных названиях, и ищет файлы по паттерну {basename}-{временная метка}*

            """
            for basename in self.basename_list:
                files = glob.glob(os.path.join(self.src_path, basename) + '*')
                time_stamps = [
                    self.retrieve_time_from_filepath(current_file) for current_file in files
                ]
                time_stamps = sorted(time_stamps)

                path_with_basename = os.path.join(self.src_path, basename)
                file_pattern = '{}*'.format(
                    '-'.join([path_with_basename, time_stamps[-1]]),
                )
                result_files = glob.glob(file_pattern)

                self.files_to_move.extend(result_files)
            self.logger.debug(
                'Найденные файлы для перемещения: %s', self.files_to_move,
            )

        if self.files_to_move is None:
            self.files_to_move = []
            select_files()

        return self.files_to_move

    def move_backups(self, period_name, period):
        files_to_move = self.get_files_to_move()

        sub_path = period.get('path', period_name)

        files_dest_path = os.path.join(self.dest_path, sub_path)

        self.logger.debug(
            'Папка назначения для %s: %s',
            period_name,
            files_dest_path,
        )

        if not os.path.exists(files_dest_path):
            self.logger.debug(
                'Папка %s не существует, попытка создать',
                files_dest_path,
            )
            try:
                os.makedirs(files_dest_path)
            except Exception as e:
                self.logger.error(
                    'Невозможно создать папку по следующему пути: %s, %s',
                    files_dest_path,
                    e,
                )

        for moving_file in files_to_move:
            self.logger.debug('Копирование файла %s', moving_file)
            try:
                shutil.copy(moving_file, files_dest_path)
            except Exception as e:
                self.logger.error(
                    'Проблема во время копирования файла %s, %s',
                    moving_file,
                    e
                )
