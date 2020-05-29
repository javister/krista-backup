import datetime
import functools
import os
import re


class BaseStrategy:

    @classmethod
    def parse_patterns(cls, cleaner, patterns):
        """Обработка всех переданных патернов.

        Args:
            patterns: Список паттернов.

        """
        patterns = patterns or []
        result_patterns = []

        for pattern in patterns:
            pattern_ = cls.parse_pattern(cleaner, pattern)
            if pattern_:
                result_patterns.append(pattern_)

        cleaner.logger.debug(
            'Добавлены группы для удаления: %s',
            [pat.pattern for pat in result_patterns],
        )
        return result_patterns

    @staticmethod
    def parse_pattern(cleaner, pattern):
        try:
            return re.compile(pattern)
        except re.error as exc:
            cleaner.logger.warning(
                'Ошибка в регулярном выражении: %s, %s',
                pattern,
                exc,
            )

    @classmethod
    def collect_files(cls, cleaner, path, patterns, exclusions=None):
        """Возвращает словарь с файлами из директории path."""
        if not patterns:
            cleaner.logger.warning('Не заданы паттерны')
            return None

        exclusions = exclusions or []
        path = path or cleaner.source.generate_dirname()
        files = {}

        composed_filter = functools.partial(
            cls._filter_file,
            patterns=patterns,
            exclusions=exclusions
        )

        apply = functools.partial(
            cls.add_file,
            getkey=composed_filter,
            files=files,
            base_path=path,
        )
        try:
            cleaner.walk_apply(path, apply, recursive=False, apply_dirs=False)
        except AttributeError:
            cleaner.logger.info('Указаный путь не существует')
        cleaner.logger.debug('Список файлов %s', files)
        return files

    @classmethod
    def filter_files(cls, cleaner, action, files, days=None, max_files=None):
        files_to_remove = []

        if days is not None:
            cls.add_files_to_remove_by_days(
                files, action, add=files_to_remove.append, days=days)

        if max_files is not None:
            cls.add_files_to_remove_by_amount(
                files, action,
                add=files_to_remove.append,
                max_files=max_files,
            )
        if files_to_remove:
            cleaner.logger.debug(
                'Файлы для удаления: %s',
                files_to_remove,
            )
        else:
            cleaner.logger.info('Нет файлов для удаления')
        return files_to_remove

    @staticmethod
    def add_files_to_remove_by_days(files, action, add, days):
        """Фильтрует и исключает файлы из self.full_files_list по количеству дней.

        Информацию о количестве дней берёт через схему именования.

        Args:
            days: Целое число, максимальное время жизни файлов в днях.
            add: Функция добавления файла в список удаляемых.
            action: Действие, которое создаёт данные файлы.

        """
        now_date = datetime.datetime.now()
        for signature, file_group in files.items():
            for filepath in file_group:
                file_ctime = action.scheme.retrieve_time_from_name(
                    os.path.basename(filepath),
                    signature[1],
                )
                if file_ctime and (now_date - file_ctime).days >= days:
                    add(filepath)

    @staticmethod
    def add_files_to_remove_by_amount(files, action, add, max_files):
        """Фильтрует/исключает файлы по количеству в группе.

        Файлы обрабатываются из self.full_files_list.

        """
        for signature, file_group in files.items():
            key_list = sorted(
                file_group,
                key=lambda filepath:
                    action.scheme.retrieve_time_from_name(
                        os.path.basename(filepath),
                        signature[1],
                    ),
                reverse=True,
            )
            while key_list and len(key_list) > max_files:
                file_to_remove = key_list.pop()
                add(file_to_remove)

    @staticmethod
    def remove_files(cleaner, files):
        for filepath in files:
            if not cleaner.remove(filepath):
                cleaner.logger.debug('Удалён: %s', filepath)

    @classmethod
    def _filter_file(cls, filepath, patterns, exclusions):
        """Проверяет попадание файл в паттерны и отсутствие в исключениях."""
        full_filename = os.path.basename(filepath)
        _, file_extension = os.path.splitext(full_filename)
        file_extension = file_extension or ' '

        for pattern in patterns:
            match = re.match(pattern, full_filename)
            if not match:
                continue
            for exclusion_pattern in exclusions:
                if re.match(exclusion_pattern, full_filename):
                    return False
            if 'ext' in match.groupdict():
                file_extension = match.group('ext')

            return (file_extension, pattern)
        return False

    @staticmethod
    def add_file(src, files, getkey, base_path=None):
        """
        Args:
            src: Строка, путь к файлу, чаще всего относительный.
            getkey: Функция получения сигнатуры, которая используется
            в качестве ключа в full_files_list.
            base_path: Строка, путь до относительного пути src.

        """
        key = getkey(src)
        if key:
            if base_path:
                src = os.path.join(base_path, src)
            files.setdefault(key, []).append(src)
