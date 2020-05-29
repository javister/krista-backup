from .scheme_formatter import SchemeFormatter

import re
import datetime


REQUIRED_PATTERNS = (
    'scheme_id',
    'fsdump_fileformat',
    'fsdump_hash_fileformat',
    'pgdump_fileformat',
    'pgdump_hash_fileformat',
)


class SchemeMeta(type):

    def __new__(cls, name, bases, _dict):
        for pattern in REQUIRED_PATTERNS:
            if pattern not in _dict:
                raise ValueError(
                    'Отсутствует необходимый паттерн {0} в схеме {1}'.format(
                        pattern,
                        name,
                    ),
                )
        return type.__new__(cls, name, bases, _dict)

class DefaultNamingScheme(metaclass=SchemeMeta):
    """Стандартная схема именования.

    Если в формате используется параметр подстановки, который не указан в
    _reserved_keywords, то объект схемы должен содержать атрибут
    с данным именем.

    Attributes:
        scheme_id: Уникальный идентификатор схемы.
        fsdump_fileformat: Формат файловых бэкапов.
        fsdump_hash_fileformat: Формат хэшфайла файловых бэкапов.
        pgdump_fileformst: Формат бэкапов баз данных.
        pgdump_hash_fileformat: Формат хэшфайла баз данных.
        _reserved_keywords: Множество зарезервированных слов.

    """

    scheme_id = 'default'

    fsdump_fileformat = '{basename}-{date:%Y%m%d_%H%M%S}-{level}.{ext}'
    fsdump_hash_fileformat = '{basename}-{date:%Y%m%d_%H%M%S}-{level}.hash'

    pgdump_fileformat = '{basename}-{dbname}-{date:%Y%m%d_%H%M%S}.pgdump'
    pgdump_hash_fileformat = '{basename}-{dbname}-{date:%Y%m%d_%H%M%S}.hash'

    _reserved_keywords = frozenset(
        ('date', 'level', 'dbname', 'ext', 'basename')
    )

    def __init__(self):
        from common.YamlConfig import AppConfig
        self.formatter = SchemeFormatter()
        self._static_values = {'date': AppConfig.get_starttime()}
        for fileformat in (
                self.fsdump_fileformat,
                self.fsdump_hash_fileformat,
                self.pgdump_fileformat,
                self.pgdump_hash_fileformat,
        ):
            self._check_noncontex_params_presence(fileformat)

    def get_fsdump_name(self, obj, **kwargs):
        """Возвращает имя файла fsdump в формате текущей схемы."""
        field_values = dict(self._static_values, **kwargs)
        field_values = self._assemble_pattern_params(
            self.fsdump_fileformat, obj, **field_values)
        return self.formatter.format(self.fsdump_fileformat, **field_values)

    def get_fsdump_pattern(self, obj, **kwargs):
        """Возвращает паттерн файлов fsdump в формате текущей схемы."""
        if 'date' not in kwargs:
            kwargs['date'] = _get_regex_by_strftime(
                self.formatter.get_format_spec(self.fsdump_fileformat, key='date'))

        field_values = dict(self._static_values, **kwargs)
        field_values = self._assemble_pattern_params(
            self.fsdump_fileformat, obj, use_defaults=True, **field_values)
        return self.formatter.format(self.fsdump_fileformat, **field_values)

    def get_fsdump_hashfile_name(self, obj, **kwargs): 
        """Возвращает имя хэшфайла fsdump в формате текущей схемы."""
        field_values = dict(self._static_values, **kwargs)
        field_values = self._assemble_pattern_params(
            self.fsdump_hash_fileformat, obj, **field_values)
        return self.formatter.format(self.fsdump_hash_fileformat, **field_values)

    def get_fsdump_hashfile_pattern(self, obj, **kwargs):
        """Возвращает паттерн имени хэшфайла fsdump в формате текущей схемы."""
        if 'date' not in kwargs:
            kwargs['date'] = _get_regex_by_strftime(
                self.formatter.get_format_spec(self.fsdump_hash_fileformat, key='date'))

        field_values = dict(self._static_values, **kwargs)
        field_values = self._assemble_pattern_params(
            self.fsdump_hash_fileformat, obj, use_defaults=True, **field_values)
        return self.formatter.format(self.fsdump_hash_fileformat, **field_values)

    def get_pgdump_name(self, obj, **kwargs):
        """Возвращает имя файла pgdump в формате текущей схемы."""
        field_values = dict(self._static_values, **kwargs)
        field_values = self._assemble_pattern_params(
            self.pgdump_fileformat, obj, **field_values)
        return self.formatter.format(self.pgdump_fileformat, **field_values)

    def get_pgdump_pattern(self, obj, **kwargs):
        """Возвращает паттерн файлов pgdump в формате текущей схемы."""
        if 'date' not in kwargs:
            kwargs['date'] = _get_regex_by_strftime(
                self.formatter.get_format_spec(self.fsdump_fileformat, key='date'))

        field_values = dict(self._static_values, **kwargs)
        field_values = self._assemble_pattern_params(
            self.pgdump_fileformat, obj, use_defaults=True, **field_values)
        return self.formatter.format(self.pgdump_fileformat, **field_values)

    def get_pgdump_hashfile_name(self, obj, **kwargs):
        """Возвращает имя хэшфайла pgdump в формате текущей схемы."""
        field_values = dict(self._static_values, **kwargs)
        field_values = self._assemble_pattern_params(
            self.pgdump_hash_fileformat, obj, **field_values)
        return self.formatter.format(self.pgdump_hash_fileformat, **field_values)

    def get_pgdump_hashfile_pattern(self, obj, **kwargs):
        """Возвращает паттерн имени хэшфайла pgdump в формате текущей схемы."""
        if 'date' not in kwargs:
            kwargs['date'] = _get_regex_by_strftime(
                self.formatter.get_format_spec(self.pgdump_hash_fileformat, key='date'))

        field_values = dict(self._static_values, **kwargs)
        field_values = self._assemble_pattern_params(
            self.pgdump_hash_fileformat, obj, use_defaults=True, **field_values)
        return self.formatter.format(self.pgdump_hash_fileformat, **field_values)

    def _check_noncontex_params_presence(self, fileformat):
        """Проверяет наличие неконтекстных параметров."""
        for field_tuple in self.formatter.parse(format_string=fileformat):
            field = field_tuple[1]
            if field and field not in self._reserved_keywords:
                try:
                    self._static_values[field] = getattr(self, field)
                except AttributeError:
                    exc = AttributeError(
                        'В схеме {0} отсутвует параметр {1}'.format(
                            self.scheme_id,
                            field,
                        )
                    )
                    exc.__cause__ = None
                    raise exc

    def _assemble_pattern_params(self, fileformat, obj, use_defaults=True, **kwargs):
        """Собирает контекстные параметры.

        Если параметр отсутстует в kwargs, то он будет искаться в действии,
        а потом в defaults.

        Returns:
            Словарь с контекстными параметрами.

        """
        if use_defaults:
            defaults = self._get_defaults(fileformat)
        else:
            defaults = {}
        context_params = {}
        for field_tuple in self.formatter.parse(format_string=fileformat):
            field = field_tuple[1]
            if field:
                param = kwargs.get(field)
                if param is None:
                    try:
                        param = getattr(obj, field)
                    except AttributeError:
                        if field in defaults:
                            param = defaults.get(field)
                        else:
                            exc = AttributeError(
                                'Отсутствует контекстный параметр {1} в схеме {0}'.format(
                                    self.scheme_id,
                                    field,
                                )
                            )
                            exc.__cause__ = None
                            raise exc
                context_params[field] = param
        return context_params

    def retrieve_time_from_name(self, name, pattern):
        """Возвращает время файла по имени.

        Дата пытается извлечь из группы date в pattern.

        Args:
            name: Строка, имя файла.
            pattern: Regex паттерн, соответствует файлу.

        Returns:
            datetime или None, если date отсутствует или он невалидный.

        """
        matched = re.match(pattern, name)

        if not matched:
            return None

        if 'date' not in matched.groupdict():
            return None

        date = re.match(pattern, name).group('date')

        # TODO не для всех случаев верно
        # (когда использован кастомный паттерн)
        # Возможно нужно реализовать обратную версию _get_regex_by_strftime
        # + добавить группы для времен
        for name_format in (
            self.fsdump_fileformat,
            self.fsdump_hash_fileformat,
            self.pgdump_fileformat,
            self.pgdump_hash_fileformat,
        ):
            date_format = self.formatter.get_format_spec(
                name_format,
                key='date',
            )
            try:
                date = datetime.datetime.strptime(date, date_format)
            except ValueError:
                continue
            return date
        return None

    def _get_defaults(self, fileformat):
        return {
            'level': r'\d',
            'ext': r'(?P<ext>.*)',
            'basename': r'(?P<basename>.*)',
            'dbname':  r'[^-\s]+',
        }


def _get_regex_by_strftime(strftime):
    strftime = strftime.replace(r'%d', r'(?:0[1-9]|[1-2]\d|30|31)')
    strftime = strftime.replace(r'%m', r'(?:0[1-9]|1[0-2])')
    strftime = strftime.replace(r'%Y', r'(?:\d{4})')
    strftime = strftime.replace(r'%H', r'(?:[0-1]\d|2[0-4])')
    strftime = strftime.replace(r'%M', r'(?:[0-5]\d)')
    strftime = strftime.replace(r'%S', r'(?:[0-5]\d)')
    return '(?P<date>{0})'.format(strftime)
