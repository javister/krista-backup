from logging import NullHandler
import os
import time


class TriggerHandler(NullHandler):
    """
        Данный handler следит за уровнем записей в логе и при повышении максимального текущего
        меняет статус в соотвутствующем trigger файле.

        Атрибуты TriggerHandler:

        1. trigger_path - путь к флаг файлу
        2. current_state - наибольший приоритет записи в логе

        Варианты state:
            {0, 10, 20} - SUCCESS
            {30, 40} - WARNING
            {40, 50} - ERROR

    """

    STATES = {'SUCCESS': 20, 'WARNING': 30, 'ERROR': 40}

    TIME_DIFF = 5 * 60 * 60  # 5 часов

    def __init__(self, trigger_path):
        self.baseFilename = trigger_path
        self.current_run_state = 25
        self.refresh_trigger_state()
        if self.current_run_state >= self.state_trigger or (
                time.time() - self.mtime_trigger) >= self.TIME_DIFF:
            self.emit("SUCCESS")

    def handle(self, record):
        self.refresh_trigger_state()

        # обновить триггер, если у нового статуса выше приоритет,
        # либо предыдущий устарел
        if record.levelno > self.current_run_state:
            self.current_run_state = record.levelno

        if self.current_run_state >= self.state_trigger \
                or (time.time() - self.mtime_trigger) >= self.TIME_DIFF:
            self.current_state = record.levelno
            self.emit(record.levelname)

    def emit(self, state_name):
        with open(self.baseFilename, "w+") as trigger_file:
            trigger_file.write(state_name)

    def refresh_trigger_state(self):
        try:
            self.mtime_trigger = os.path.getmtime(self.baseFilename)
            state = open(self.baseFilename).read()
            self.state_trigger = self.STATES[state]
        except Exception as e:
            self.mtime_trigger = 0
            self.state_trigger = 20
