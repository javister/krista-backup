# -*- encoding: utf-8 -*-

from logging import NullHandler
import os
import time


class TriggerHandler(NullHandler):
    """
        Данный handler следит за уровнем записей в логе и при повышении
        актуального текущего меняет статус в соотвутствующем trigger файле.

        Атрибуты TriggerHandler:

        1. trigger_path - путь к файлу с флагом
        2. current_state - наибольший актуальный приоритет записи в логе

        Варианты state:
            {0, 10, 20} - SUCCESS
            {30, 40} - WARNING
            {40, 50} - ERROR

    """

    STATES = {'SUCCESS': 20, 'WARNING': 30, 'ERROR': 40}

    MAX_TIME_DIFF = 5 * 60 * 60  # 5 часов

    def __init__(self, trigger_path):
        self.baseFilename = trigger_path
        self.current_run_state = 25
        self.refresh_trigger_state()
        lowest_priority_status = min(self.STATES, key=self.STATES.get)
        if self.current_run_state >= self.state_trigger:
            self.emit(lowest_priority_status)
        elif (time.time() - self.mtime_trigger) >= self.MAX_TIME_DIFF:
            self.emit(lowest_priority_status)

    def handle(self, record):
        """Обработчик записей.

        Обновляет статус в триггер файле, если новый имеет приоритет выше,
        либо предыдущий устарел.

        """
        self.refresh_trigger_state()
        if record.levelno > self.current_run_state:
            self.current_run_state = record.levelno

        if self.current_run_state >= self.state_trigger:
            self.emit(record.levelname)
        elif (time.time() - self.mtime_trigger) >= self.MAX_TIME_DIFF:
            self.emit(record.levelname)

    def emit(self, state_name):
        with open(self.baseFilename, 'w+') as trigger_file:
            trigger_file.write(state_name)

    def refresh_trigger_state(self):
        state = None
        try:
            with open(self.baseFilename) as trigger:
                state = trigger.read()
        except IOError:
            self.mtime_trigger = 0
        else:
            self.mtime_trigger = os.path.getmtime(self.baseFilename)

        if state not in self.STATES:
            state = min(self.STATES, key=self.STATES.get)
        self.state_trigger = self.STATES.get(state)
