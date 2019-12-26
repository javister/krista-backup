# -*- coding: UTF-8 -*-
import os
import re
import subprocess
import datetime
import logging

from runner.Action import Action
from model.YamlConfig import AppConfig
from model.Logging import get_log_path


class CheckLastBackup(Action):
    """
        Выполняется поиск лог файла с последнего процесса бэкапа.

        Порядок выполнения:
        1. Поиск последнего лога, который содержит подстроку конфигурирования действия создания бэкапа.
        2. Анализ лог файла на уведомления/ошибки.
        3. Проверка существования бэкапа и для .tar.gz проверить его целостность (для дампа базы данных просто проверить существование).
    """

    BACKUP_CONFIGURE_PATTERN = (
        r".*Конфигурирование объекта <runner.TarArchiver.TarArchiver.*")
    TAR_GZ_ARCHIVE_MATCHING_PATTERN = r".* ((?:\/.+)+\.tar\.gz),.*"
    PGDUMP_ARCHIVE_MATCHING_PATTERN = r".* ((?:\/.+)+\.pg_dump)"
    TASK_START_PATTERN = r".*Запускается действие.*"
    SUCCESS_END_PATTERN = r".*Выполнено действие.*"

    gz_backup_paths = []
    pgdump_backup_paths = []

    def __init__(self, name):
        Action.__init__(self, name)
        self._filename_dateformat = AppConfig.get_filename_dateformat()

    def retrieve_time_from_log_filename(self, filename):
        date_mark = filename.split("-")[-2]
        return datetime.datetime.strptime(date_mark, self._filename_dateformat)

    def check_log_for_tarjob_task(self, filename):
        with open(filename, "r") as log_file:
            for line in log_file:
                # Определение формирования действия бэкапа
                if re.match(self.BACKUP_CONFIGURE_PATTERN, line):
                    return True

                # Определение начала выполнения действий
                if re.match(self.TASK_START_PATTERN, line):
                    return False
        return False

    def get_last_backup_log(self):
        log_path = get_log_path()
        log_path_debug = os.path.join(log_path, "debug")
        if not os.path.exists(log_path_debug):
            return None
        log_files = [
            os.path.join(log_path_debug, filename)
            for filename in os.listdir(log_path_debug)
        ]
        log_files = [
            filename for filename in log_files if os.path.isfile(filename)
        ]
        log_files = sorted(
            log_files,
            key=lambda file: self.retrieve_time_from_log_filename(file),
            reverse=True,
        )
        for log_file in log_files:
            if self.check_log_for_tarjob_task(log_file):
                return log_file
        return None

    def analyze_log(self, filename, currently_used=False):
        log_file_lines = open(filename, "r").readlines()

        task_started = False

        for line in log_file_lines:

            splitted_line = line.split()
            state = splitted_line[1]
            message = " ".join(splitted_line[3:])

            if state == "WARNING":
                self.logger.warn("Найдено предупреждение: {}".format(message))
            elif state == "ERROR":
                self.logger.error("Найдена ошибка: {}".format(message))

            # Проверка на сохранение архива
            result = re.match(self.TAR_GZ_ARCHIVE_MATCHING_PATTERN, message)
            if result:
                self.gz_backup_paths.append(result.group(1))

            result = re.match(self.PGDUMP_ARCHIVE_MATCHING_PATTERN, message)
            if result:
                self.pgdump_backup_paths.append(result.group(1))

        # Если последнее выполняемое действие не было завершено,
        # а ранее не были найдены признаки одновременного выполнения
        # нескольких заданий, то скорее всего задание было прервано

        if (not currently_used and
                not re.match(self.SUCCESS_END_PATTERN, log_file_lines[-1]) and
                task_started):
            self.logger.error('Выполнение задания было прервано')
            self.logger.error('Возможно, что не все архивы сформированы')

    def start(self):
        log_file = self.get_last_backup_log()
        files_from_logger = [
            handler.baseFilename for handler in logging.getLogger().handlers
        ]

        if not log_file:
            self.logger.warn("Лог файл предыдущего бэкапа не был найден")
            return True

        self.logger.info(
            "Найден лог файл предыдущего бэкапа: {}".format(log_file))

        if log_file in files_from_logger:
            self.analyze_log(log_file, True)
        else:
            self.analyze_log(log_file)

        self.logger.debug("Найденные архивы с бэкапом: {}".format(
            self.gz_backup_paths))
        self.logger.debug("Найденные pgdump с бэкапом: {}".format(
            self.pgdump_backup_paths))

        for gzip_backup in self.gz_backup_paths:
            if self.check_gz_integrity(gzip_backup):
                self.logger.debug(
                    "Целостность бэкапа не нарушена: {}".format(gzip_backup))

        return True

    def check_gz_integrity(self, path):
        command = "gzip"
        flags = "-t"
        query = [command, flags, path]

        try:
            subprocess.check_output(query)
        except subprocess.CalledProcessError as e:
            self.logger.error(
                "Найден повреждённый архив с бэкапом: {}\n{}".format(
                    path, e.output))
            return False

        return True
