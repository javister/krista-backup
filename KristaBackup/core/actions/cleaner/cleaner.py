# -*- coding: UTF-8 -*-

import os
import shutil

from ..action import Action
from ..decorators import side_effecting
from ..mixins import WalkAppierMixin
from .strategies import match_strategy


class Cleaner(Action, WalkAppierMixin):
    """Класс действия для удаления файлов.

    Attributes:
        Внешние:
            days: Число, максимальное количество дней файлов в группе
            max_files: Число, максимальное количество файлов в группе
            exclusions: Список паттернов для исключения файлов из удаляемых

    Список файлов для удаления определяется явными ограничениями и неявными.
    Пример явных:
        days, max_files.
    Пример неявных:
        при обработке наследника pgdump будут наследованы имена
        баз данных, а по ним будут построены паттерны.

    """

    def __init__(self, name):
        super().__init__(name)

        self.max_files = None
        self.days = None

    def start(self):
        """Входная точка действия.

        Содержит поиск и вызов стратегий для
        pgdump, move_bkp_period и archiver.
        """
        try:
            strategy = match_strategy(self.source)
        except ValueError as exc:
            self.logger.error(exc)
            return self.continue_on_error

        strategy.clean(
            self,
            self.source,
            max_files=self.max_files,
            days=self.days,
        )
        return True

    @side_effecting
    def remove(self, filepath):
        """Удалят определённый файл по filepath.

        Args:
            filepath (str): путь к файлу, директории или ссылке.

        Returns:
            True, если возникла ошибка.

        """
        error_occured = False

        def onerror(function, path, excinfo):
            nonlocal error_occured
            error_occured = True
            self.logger.warning(
                'Ошибка рекурсивного удаления %s, функция %s, ошибка %s',
                path,
                function.__name__,
                excinfo,
            )

        if os.path.isfile(filepath) or os.path.islink(filepath):
            try:
                os.remove(filepath)
            except FileNotFoundError as exc:
                self.logger.info(
                    'Файл уже удалён %s, %s',
                    filepath,
                    exc,
                )
            except OSError as exc:
                self.logger.error(
                    'Ошибка при удалении файла %s, %s',
                    filepath,
                    exc,
                )
        else:
            shutil.rmtree(
                filepath,
                ignore_errors=False,
                onerror=onerror,
            )

        return error_occured
