# -*- coding: UTF-8 -*-

import datetime
import functools
import logging
import os
import re
import tarfile
import time
import zipfile

from .action import Action
from .decorators import side_effecting, use_exclusions
from .interfaces import NameGenerationInterface
from .mixins import WalkAppierMixin


@use_exclusions
class Archiver(Action, NameGenerationInterface, WalkAppierMixin):
    """Класс действия для создания архивов.

    Attributes:
        Внешние:
            src_path: Строка, путь к исходной директории с файлами.
            dest_path: Строка, путь к директории для файлов с результатом.
            exclusions: Список паттернов для исключения файлов из удаляемых.
            check_level_list_only: Логическое значение, если параметр
                установлен, то при инкрементельном бекапе проверяется только
            наличие файла-списка, иначе проверяется наличие самого файла
                исходного бекапа.
            use_absolute_path: Логическое значение, использовать
                абсолютные пути.
            log_files: Логическое значение, логировать добавление файлов.
            overwrite: Логическое значение, перезаписывать файлы
                с одинаковым именем.
            level: Число, уровень бэкапа.
            level_folders: Список с именами директорий для каждого уровня
                бэкапа.
            list_extension: Расширение лист-файла.
            hash_extension: Расширение файла с хэш-суммой.
        Внутренние:
            prepared_exclusions
            parent_type: Строка с типом родительского действия
            open_mode

    """

    def __init__(self, name):
        super().__init__(name)
        self.compression = 5
        self.list_extension = 'list'  # расширение для файла-списка архива
        self.check_level_list_only = True
        self.log_files = False
        self.overwrite = False
        self.checksum_file = False
        self.inc_list = {}
        self.use_absolute_path = False

        self.compression_lib = None
        self.open_mode = None
        self.extension = None

        self.level = 0
        self.level_folders = []

    def configure_archiver(self):
        self.compression = 5
        if self.compression < 0:
            self.compression = 0
        elif self.compression > 9:
            self.compression = 9

    def open_file(self, archive_filepath):
        raise NotImplementedError('open_file - should have implemented this')

    def append(self, archive, file):
        raise NotImplementedError('append - should have implemented this')

    def generate_dirname(self, *args, **kwargs):
        level = kwargs.get('level', self.level)
        if self.level_folders:
            return os.path.join(
                super().generate_dirname(self),
                self.level_folders[level],
            )
        return super().generate_dirname(self)

    def generate_filename(self, *args, **kwargs):
        """Генерирует выходное имя файла."""
        extension = kwargs.get('extension', self.extension)
        return self.scheme.get_fsdump_name(
            self,
            ext=extension,
        )

    def generate_hash_filename(self, *args, **kwargs):
        """Генерирует выходное имя файла c чексуммой."""
        return self.scheme.get_fsdump_hashfile_name(self)

    def get_patterns(self, *args, **kwargs):
        patterns = [self.scheme.get_fsdump_pattern(self)]
        if self.checksum_file:
            hash_p = self.scheme.get_fsdump_hashfile_name(self)
            patterns.append(hash_p)
        return patterns

    def find_source_listfile(self, level):
        """Находит list файл по уровню.

        Args:
            level: Целое число, необходимый уровень.

        Returns:
            str или None, если путь к файлу не найден/не существует.

        """
        if level < 0:
            return None
        dirpath = self.generate_dirname(level=level)

        if not os.path.exists(dirpath):
            return None

        required_filename_pattern = self.scheme.get_fsdump_pattern(
            self,
            level=level,
            ext=self.list_extension,
        )
        listfiles_candidates = []

        for filename in os.listdir(dirpath):
            if re.match(required_filename_pattern, filename):
                filepath = os.path.join(dirpath, filename)
                if os.path.isfile(filepath):
                    listfiles_candidates.append(filepath)

        if not listfiles_candidates:
            return None

        return max(
            listfiles_candidates,
            key=lambda filepath: self.scheme.retrieve_time_from_name(
                os.path.basename(filepath),
                required_filename_pattern,
            ),
        )

    def fill_archive(self, archive_file=None, list_file=None):
        """Добавление файлов в tar.

        Args:
            archive_file: Tarfile, файл архива.
            list_file: Лист файл, содержит записи о содержимом tar архива.

        """
        file_logger = logging.getLogger(
            '{0}.archiver_files'.format(self.logger.name),
        )
        file_logger.propagate = self.log_files

        get_signature = functools.partial(
            self._get_signature,
            file_logger=file_logger,
            matcher=re.match,
        )

        add = functools.partial(
            self._add_item,
            archive=archive_file,
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
        """Обработка переданных исключений."""
        for exclusion in self.exclusions:
            exclusion = self.prepare_pattern(exclusion)
            if not exclusion:
                continue
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
            'Добавлены исключения: %s',
            [excl.pattern for excl in self.prepared_exclusions],
        )

    def configure_parameters(self):
        """Выполняет конфигурацию параметров действия.

        Returns:
            True, если возникли ошибки.

        """
        if self.level > 1:
            self.logger.warning('Уровни выше 1 не реализованы')
            self.logger.info('Понижаю уровень до 1')
            self.level = 1

        if self.level_folders and len(self.level_folders) < self.level + 1:
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

        return False

    def adjust_backup_level(self):
        """Поиск/проверка списка файлов и архива предыдущего уровня.

        Уровень бэкапа понижается, если они отсутствуют.

        """
        if self.level == 0:
            return

        src_list_file = None
        while self.level > 0 and not src_list_file:
            # Поиск list файла минимального уровня.
            src_list_file = self.find_source_listfile(level=self.level - 1)
            if not src_list_file:
                self.level -= 1

        if not src_list_file:
            self.logger.warning(
                'Лист файл не найден, будет создана копия %s уровня.',
                self.level,
            )
            return

        self.logger.debug(
            'Файл списка бэкапа %s уровня: %s',
            self.level - 1,
            src_list_file,
        )

        with open(src_list_file, 'r') as lines:
            src_name = lines.readline().rstrip()
            if not self.check_level_list_only:
                if not os.path.exists(src_name):
                    self.logger.warning(
                        'Архив %s указанный в list файле отсутствует, '
                        'будет выполнен полный бэкап',
                        src_name,
                    )
                    self.level = 0
                    return
            for line_num, line in enumerate(lines):
                if line.count(',') < 2:
                    self.logger.warning(
                        'Ошибка в строке %s, файл будет пропущен: %s',
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
        if self.configure_archiver():
            return self.continue_on_error
        self.parse_exclusions()

        if not os.path.exists(self.dest_path):
            os.makedirs(self.dest_path, 0o755)
        self.adjust_backup_level()

        archive_filepath = self.generate_filepath(
            extension=self.extension,
        )
        if os.path.exists(archive_filepath):
            if self.overwrite:
                os.remove(archive_filepath)
            else:
                self.logger.error(
                    'Получатель уже существует: %s, архив не будет создан',
                    archive_filepath,
                )
                return self.continue_on_error

        list_filename = self.generate_filepath(
            extension=self.list_extension,
        )
        if not os.path.exists(os.path.dirname(list_filename)):
            os.makedirs(os.path.dirname(list_filename))

        self.logger.info(
            'Исходные данные архива: %s',
            self.src_path,
        )

        if self.dry:
            self.fill_archive()
        else:
            with open(list_filename, 'w+') as list_file:
                list_file.write(archive_filepath)
                list_file.write('\n')
                arhive = self.open_file(archive_filepath)
                self.fill_archive(arhive, list_file)
                arhive.close()

        self.logger.info(
            'Архив создан: %s, время обработки: %s',
            archive_filepath,
            datetime.datetime.now() - start_time,
        )

        if self.checksum_file:
            hash_filepath = self.generate_hash_filepath()
            self.create_checksum_file(archive_filepath, hash_filepath)

        return True

    def get_filename_patterns(self):
        patterns = (
            self.scheme.get_fsdump_pattern(self),
            self.scheme.get_hash_pattern()
        )
        return patterns

    @side_effecting
    def _add_item(self, path, signature, archive, list_file, repeat=False):
        try:
            self.append(archive, path)
        except FileNotFoundError:
            self.logger.debug(
                'Файл/директория не найдена: %s',
                path,
            )
        except OSError as exc:
            self.logger.debug(
                'Не удалось добавить %s: %s',
                path,
                exc,
            )
            if repeat:
                self.logger.debug('Новая попытка через 5 секунд.')
                time.sleep(5)
                self._add_item(path, signature, archive, list_file)
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
        if path in self.inc_list:
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
        if self.use_absolute_path:
            path = os.path.abspath(path)
        signature = get_signature(path)
        if signature:
            add(path, signature)


@use_exclusions
class ArchiverTar(Archiver):
    """Класс действия для создания tar архивов.

    Attributes:
        Внешние:
            compression: Целое число, уровень сжатия.
            compression_lib: тип библиотеки шифрования gzip, bzip; lzma (python3.3+)

    """

    compression_types = {
        'gzip': ['w:gz', 'tar.gz'],
        'bzip': ['w:bz2', 'tar.bz2'],
    }

    try:
        import lzma
    except ImportError:
        # Модуль lzma появился в python3.3
        pass
    else:
        compression_types['lzma'] = ['w:xz', 'xz']

    def __init__(self, name):
        super().__init__(name)
        self.compression_lib = 'gzip'

    def configure_archiver(self):
        super().configure_archiver()
        if self.compression_lib not in self.compression_types:
            self.compression_lib = 'gzip'
        self.open_mode = self.compression_types[self.compression_lib][0]
        self.extension = self.compression_types[self.compression_lib][1]
        return False

    def open_file(self, archive_filepath):
        if self.compression_lib != 'lzma':
            return tarfile.open(
                archive_filepath,
                mode=self.open_mode,
                compresslevel=self.compression,
            )
        return tarfile.open(
            archive_filepath,
            mode=self.open_mode,
        )

    def append(self, archive, file):
        archive.add(file, recursive=False)


@use_exclusions
class ArchiverZip(Archiver):
    """Класс действия для создания tar архивов.

    Attributes:
        Внешние:
            compression: Целое число, уровень сжатия.
            compression_lib: тип библиотеки шифрования zip; bzip, lzma (python3.3+)

    """
    compression_types = {
        'zip': [zipfile.ZIP_DEFLATED, 'zip'],
    }

    try:
        import lzma
    except ImportError:
        # Модуль lzma и сжатие bz2 появились в python3.3
        pass
    else:
        compression_types['bzip'] = [zipfile.ZIP_BZIP2, 'bz2']
        compression_types['lzma'] = [zipfile.ZIP_LZMA, 'xz']

    def __init__(self, name):
        super().__init__(name)
        self.compression_lib = 'zip'

    def configure_archiver(self):
        super().configure_archiver()
        if self.compression_lib not in self.compression_types:
            self.compression_lib = 'zip'
        self.open_mode = self.compression_types[self.compression_lib][0]
        self.extension = self.compression_types[self.compression_lib][1]

    def open_file(self, archive_filepath):
        return zipfile.ZipFile(
            archive_filepath,
            mode='w',
            compression=self.open_mode,
        )

    def append(self, archive, file):
        archive.write(file)
