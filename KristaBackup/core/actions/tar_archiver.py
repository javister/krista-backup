# -*- coding: UTF-8 -*-

import fnmatch
import functools
import tarfile
import re
import os
import datetime
import time
import logging

from .action import Action
from .decorators import use_exclusions, use_levels, side_effecting


@use_exclusions
@use_levels
class TarArchiver(Action):
    """Класс действия для создания архивов.

    Attributes:
        Внешние:
            src_path: Строка, путь к исходной директории с файлами.
            dest_path: Строка, путь к директории для файлов с результатом.
            exclusions: Список паттернов для исключения файлов из удаляемых.
            compression: Целое число, уровень сжатия.
            check_level_list_only: Логическое значение, если параметр
            установлен, то при инкрементельном бекапе проверяется только
            наличие файла-списка, иначе проверяется наличие самого файла
            исходного бекапа.
            use_absolute_path: Логическое значение, использовать
            абсолютные пути.
            log_tar_files: Логическое значение, логировать добавление файлов.
            overwrite: Логическое значение, перезаписывать файлы
            с одинаковым именем.
            level: Число, уровень бэкапа.
            level_folders: Список с именами директорий для каждого уровня
            бэкапа.

        Внутренние:
            list_extension:
            prepared_exclusions:
            parent_type: Строка с типом родительского действия

    """

    def __init__(self, name):
        super().__init__(name)
        self.compression = 5
        self.list_extension = 'list'  # расширение для файла-списка архива
        self.extension = 'tar.gz'
        self.check_level_list_only = True
        self.log_tar_files = False
        self.overwrite = False

        self.list_file = None
        self.inc_list = {}
        self.use_absolute_path = False

    def generate_dirname(self):
        return os.path.join(
            super().generate_dirname(),
            self.level_folders[self.level],
        )

    def generate_filename(self, name, time_suffix, extension=None):
        """Генерирует выходное имя файла."""
        parts = [self.basename, name, time_suffix, str(self.level)]
        filename = '-'.join(
            [part for part in parts if part is not None],
        )
        if extension and isinstance(extension, str):
            return '.'.join([filename, extension])
        return filename

    def find_source_listfile(self, level):
        """Находит list файл по уровню.

        Args:
            level: Целое число, необходимый уровень.

        Returns:
            str или None, если путь к файлу не найден/не существует.

        """
        if self.level <= 0:
            return None

        dirpath = os.path.join(self.dest_path, self.level_folders[level])
        if not os.path.exists(dirpath):
            return None

        files = []
        required_filename_pattern = '{0}*{1}.{2}'.format(
            self.basename,
            level,
            self.list_extension,
        )

        for filename in os.listdir(dirpath):
            filepath = os.path.join(dirpath, filename)
            if fnmatch.fnmatch(filename, required_filename_pattern):
                if os.path.isfile(filepath):
                    files.append(filename)
        if not files:
            return None

        prev_list_file = None
        if len(files) == 1:
            prev_list_file = os.path.join(
                self.dest_path,
                self.level_folders[level],
                files[0],
            )
        elif len(files) > 1:
            sorted_files = sorted(files, reverse=True)
            prev_list_file = os.path.join(
                self.dest_path,
                self.level_folders[level],
                sorted_files[0],
            )
        self.logger.debug(
            'Файл списка бэкапа %s уровня: %s',
            level,
            prev_list_file,
        )

        return prev_list_file

    def fill_tar_archive(self, tar=None, list_file=None):
        """Добавление файлов в tar.

        Args:
            tar: Tarfile, файл архива.
            list_file: Лист файл, содержит записи о содержимом tar архива.

        """
        file_logger = logging.getLogger(
            '{0}.tar_files'.format(self.logger.name),
        )
        file_logger.propagate = self.log_tar_files

        get_signature = functools.partial(
            self._get_signature,
            file_logger=file_logger,
            matcher=self.get_pattern_matcher(),
        )
        add = functools.partial(
            self._add_item,
            tar=tar,
            list_file=list_file,
            repeat=True,
        )
        handle_file = functools.partial(
            self._handle_item,
            get_signature=get_signature,
            add=add,
        )
        self.walk_apply(src=self.src_path, apply=handle_file, apply_dirs=True)

    def parse_exclusions(self):
        if not self.exclusions:
            return
        if self.use_re_in_patterns:
            for exclusion in self.exclusions:
                exclusion = exclusion.strip()
                try:
                    exclusion = re.compile(exclusion)
                except Exception as exc:
                    self.logger.warning(
                        'Ошибка в исключении %s: %s',
                        exclusion,
                        exc,
                    )
                else:
                    self.prepared_exclusions.append(exclusion)
            self.logger.debug(
                'Добавлены исключения (re): %s',
                self.prepared_exclusions,
            )
        else:
            for exclusion in self.exclusions:
                exclusion = exclusion.strip()
                if exclusion:
                    self.prepared_exclusions.append(exclusion)
            self.logger.debug(
                'Добавлены исключения (sh): %s',
                self.prepared_exclusions,
            )

    def configure_parameters(self):
        """Выполняет конфигурацию параметров действия.

        Returns:
            True, если возникли ошибки.

        """
        if self.level > 1:
            self.logger.warning(
                'Уровни выше 1 не реализованы.',
            )
            self.logger.info('Понижаю уровень до 1')
            self.level = 1

        if len(self.level_folders) < self.level + 1:
            self.logger.error(
                'Неверно сконфигурированы папки уровней бекапов!',
            )
            self.logger.debug(
                'Для уровня %s отсутствует имя в level_folders: %s',
                self.level,
                self.level_folders,
            )
            return True
        if not os.path.exists(self.src_path):
            if os.path.isfile(self.src_path):
                self.logger.error(
                    'Отсутствует исходный файл %s',
                    self.src_path,
                )
            else:
                self.logger.error(
                    'Отсутствует исходная папка %s.',
                    self.src_path,
                )
            return True
        if self.compression < 0:
            self.compression = 0
        elif self.compression > 9:
            self.compression = 9
        return False

    def adjust_backup_level(self):
        """Поиск / проверка списка файлов и архива предыдущего уровня.

        Уровень бэкапа понижается, если они отсутствуют.

        """
        while self.level > 0:
            # Поиск list файла минимального уровня.
            src_list_file = self.find_source_listfile(level=self.level - 1)
            if src_list_file is not None:
                break
            self.level -= 1

        if src_list_file is None:
            self.logger.warning(
                'Лист файл не найден, будет создана копия %s уровня.',
                self.level,
            )
            return

        with open(src_list_file, 'r') as lines:
            src_name = lines.readline().rstrip()
            if not self.check_level_list_only:
                if not os.path.exists(src_name):
                    self.logger.warning(
                        'Архив %s указанный в list файле отсутствует.',
                        src_name,
                    )
                    self.logger.warning('Будет выполнен полный бэкап.')
                    self.level = 0
                    return
            for line_num, line in enumerate(lines):
                if line.count(',') < 2:
                    self.logger.warning(
                        'Ошибка в строке %s файла-списка:\n%s',
                        line_num,
                        line,
                    )
                    continue
                mtime, size, filename = line.rstrip().split(',', 2)
                self.inc_list[filename] = (mtime, size)

    def start(self):
        start_time = datetime.datetime.now()
        if self.configure_parameters():
            return self.continue_on_error
        self.parse_exclusions()

        if not os.path.exists(self.dest_path):
            os.makedirs(self.dest_path, 0o755)

        if self.level > 0:
            self.adjust_backup_level()

        # Создаем архив
        full_filename = self.generate_filepath(
            name=None,
            extension=self.extension,
        )
        if os.path.exists(full_filename):
            if self.overwrite:
                os.remove(full_filename)
            else:
                self.logger.error(
                    'Получатель уже существует: %s, архив не будет создан',
                    full_filename,
                )
                return self.continue_on_error

        list_filename = self.generate_filepath(
            name=None,
            extension=self.list_extension,
        )
        if not os.path.exists(os.path.dirname(list_filename)):
            os.makedirs(os.path.dirname(list_filename))

        self.logger.info(
            'Исходные данные архива: %s',
            self.src_path,
        )

        if self.dry:
            self.fill_tar_archive()
        else:
            with open(list_filename, 'a') as list_file:
                list_file.write(full_filename)
                list_file.write('\n')
                tar = tarfile.open(
                    full_filename,
                    mode='w:gz',
                    compresslevel=self.compression,
                )
                self.fill_tar_archive(tar, list_file)

        self.logger.info(
            'Архив создан: %s, время обработки: %s',
            full_filename,
            datetime.datetime.now() - start_time,
        )

        return True

    @side_effecting
    def _add_item(self, path, signature, tar, list_file, repeat=False):
        try:
            tar.add(path, recursive=False)
        except FileNotFoundError:
            self.logger.debug(
                'Файл/директория не найдена: %s',
                path,
            )
        except Exception as exc:
            self.logger.debug(
                'Не удалось добавить %s: %s',
                path,
                exc,
            )
            if repeat:
                self.logger.debug('Новая попытка через 5 секунд.')
                time.sleep(5)
                self._add_item(path, signature, tar, list_file)
        else:
            list_file.write('{0}\n'.format(signature))

    def _get_signature(self, path, file_logger, matcher):
        try:
            mtime = os.path.getmtime(path)
            fsize = os.path.getsize(path)
        except FileNotFoundError:
            return None
        signature = '{0},{1},{2}'.format(mtime, fsize, path)
        for exclusion in self.prepared_exclusions:
            if matcher(exclusion, path):
                file_logger.debug('ex %s', path)
                return None
        if path in self.inc_list.keys():
            if mtime == float(self.inc_list[path][0]):
                if fsize == float(self.inc_list[path][1]):
                    file_logger.debug('eq %s', signature)
                    return None
        file_logger.debug('add %s', signature)
        return signature

    def _handle_item(self, path, add, get_signature):
        """Обрабатывает файл.

        Если get_signature возвращает не None, то вызывается
        add(path, signature).

        Args:
            path: Строка, путь к файлу/директории.
            add: Функция добавления в архив.
            get_signature: Функция получения сигнатуры файла.

        """
        signature = get_signature(path)
        if signature:
            add(path, signature)
