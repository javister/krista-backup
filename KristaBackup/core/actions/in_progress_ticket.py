# -*- coding: UTF-8 -*-

import errno
import os
import time

from .action import Action


class InProgressTicket(Action):
    """
        Базовый action для работы с тикетами.

    """

    ticket_filename = "backup_in_progress"
    """str: имя тикет файла
    """


class SetInProgressTicket(InProgressTicket):
    """
        Action для создания тикет файлов.

    """

    creation_flags = os.O_CREAT | os.O_EXCL
    """int: флаги для создания тикет файла
    для os.open():
    O_CREAT - создаёт файл
    O_EXCL - выдаёт ошибку, если файл уже существует
    """

    def __init__(self, name):
        super().__init__(name)

    def start(self):
        try:
            self.createTicket()
        except OSError as e:
            if e.errno == errno.EEXIST:
                self.logger.warn(
                    "Тикет файл %s в директории %s уже существует!",
                    self.ticket_filename,
                    self.src_path,
                )
            else:
                self.logger.error(
                    "Ошибка при создании тикет файла %s в директории %s: %s!",
                    self.ticket_filename,
                    self.src_path,
                    str(e),
                )
            return self.continue_on_error

        self.logger.info("Тикет файл %s в директории %s создан.",
                         self.ticket_filename, self.src_path)
        return True

    def createTicket(self):
        """
        Создаёт тикет файл с именем self.ticket_filename
        в директории self.src_path.

        Если файл уже существует, то возвращает OSError
        исключение.
        """
        filepath = os.path.join(self.src_path, self.ticket_filename)

        if not os.path.exists(self.src_path):
            self.logger.debug(
                "Требуемая директория отсутствует, попытка создать")
            if os.path.isfile(self.src_path):
                raise OSError("Невозможно создать файл в директории %s",
                              self.src_path)
            os.makedirs(self.src_path)

        os.open(filepath, self.creation_flags)


class UnsetInProgressTicket(InProgressTicket):
    """
        Action для удаления тикет файлов.

    """

    def __init__(self, name):
        super().__init__(name)

    def start(self):
        try:
            self.removeTicket()
        except Exception as e:
            self.logger.error(
                "Ошибка при удалении тикет файла %s в директории %s: %s!",
                self.ticket_filename,
                self.src_path,
                str(e),
            )
            return self.continue_on_error

        self.logger.info(
            "Тикет файл %s в директории %s успешно удалён.",
            self.ticket_filename,
            self.src_path,
        )
        return True

    def removeTicket(self):
        """
        Удаляет тикет файл с именем self.ticket_filename
        в директории self.src_path.

        """
        filepath = os.path.join(self.src_path, self.ticket_filename)
        if not os.path.exists(filepath):
            self.logger.debug("Тикет файл не существует.")
        else:
            self.logger.debug("Тикет файл существует, попытка удалить.")
            os.remove(filepath)


class CheckInProgressTicket(InProgressTicket):
    """
        Action для проверки наличия тикет файла.

    """

    ssh_servername = ""
    """str: имя удалённого ssh-сервера"""

    rsync_opts = ""
    """str: параметры подключения rsync"""

    wait_time = 10
    """int: время ожидания в секундах"""

    wait_cycle_number = 12
    """int: количество циклов ожидания"""

    def __init__(self, name):
        super().__init__(name)
        self.__cmdline_ticket = None
        self.__cmdline_file_doesnt_exists = None

        if self.wait_cycle_number == 0:
            self.wait_cycle_number = 1

    def start(self):
        try:
            while self.wait_cycle_number:
                self.logger.debug("Осталось проверок: %s",
                                  self.wait_cycle_number)
                if not self.check_ticket():
                    self.logger.debug("Тикет отсутвует")
                    break
                self.logger.debug(
                    "Тикет существует, повторение через %s секунд",
                    self.wait_time)
                self.wait_cycle_number -= 1
                time.sleep(self.wait_time)
            else:
                raise ValueError(
                    "Превышено максимальное количество повторений.")
        except Exception as e:
            self.logger.error("Ошибка при проверке существования тикета: %s",
                              str(e))
            return self.continue_on_error

        return True

    def build_cmdline_for_file(self, filename):
        """
        Строит cmdline, которая позволяет проверить наличие
        файла filename по пути, который находится в директории
        self.src_path.

        Если указан параметр self.ssh_servername, то проверка
        будет осуществляться на указанном ssh-сервере.

        """
        full_src_path = ':'.join([self.ssh_servername, self.src_path])
        cmdline = " ".join([
            "rsync",
            self.rsync_opts,
            "--include={}".format(filename),
            "--exclude='*'",
            full_src_path,
        ])
        return cmdline

    def check_ticket(self):
        """
        Проверяет существование файла self.ticket_filename
        в директории self.src_path.
        Возвращает True, если тикет существует.

        """

        if not self.__cmdline_ticket:
            self.__cmdline_ticket = self.build_cmdline_for_file(
                self.ticket_filename)

        if not self.__cmdline_file_doesnt_exists:
            self.__cmdline_file_doesnt_exists = self.build_cmdline_for_file(
                "this_filename_doesnt_exist")

        ticket_output = self.unsafe_execute_cmdline(
            self.__cmdline_ticket,
            return_stdout=True,
        ).split('\n')

        nofile_output = self.unsafe_execute_cmdline(
            self.__cmdline_file_doesnt_exists,
            return_stdout=True,
        ).split('\n')

        if len(ticket_output) - len(nofile_output) == 1:
            return True

        return False
