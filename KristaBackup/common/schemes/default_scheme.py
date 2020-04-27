from common.YamlConfig import AppConfig

from .scheme_formatter import SchemeFormatter


class DefaultNamingScheme(object):
    """Стандартная схема именования.

    Если в формате используется параметр подстановки, который не указан в
    _reserved_keywords, то объект схемы должен содержать атрибут
    с данным именем.

    Attributes:
        scheme_id: Уникальный идентификатор схемы.

        fsdump_fileformat: Формат файловых бэкапов.
        pgdump_fileformst: Формат бэкапов баз данных.

        _reserved_keywords: Множество зарезервированных слов.

    """

    scheme_id = 'default'
    name = 'default_scheme_basement'

    default_fileformat = '{name}-{date:%d%m%Y_%H%M%S}'
    fsdump_fileformat = '{name}-{date:%d%m%Y}-{level}.{ext}'
    pgdump_fileformat = '{name}-{dbname}-{date:%d%m%Y_%H}.pgdump'

    _reserved_keywords = frozenset({'date', 'level', 'dbname', 'ext'})

    def __init__(self):
        self.formatter = SchemeFormatter()
        self._static_values = {'date': AppConfig.get_starttime()}
        self._check_params_presence(self.fsdump_fileformat)
        self._check_params_presence(self.pgdump_fileformat)

    def get_fsdump_name(self, obj, **kwargs):
        """Возвращает имя файла fsdump в формате текущей схемы."""
        field_values = dict(self._static_values, **kwargs)
        return self.formatter.format(self.fsdump_fileformat, **field_values)

    def get_pgdump_name(self, obj, **kwargs):
        """Возвращает имя файла pgdump в формате текущей схемы."""
        field_values = dict(self._static_values, **kwargs)
        return self.formatter.format(self.pgdump_fileformat, **field_values)

    def get_fsdump_pattern(self, obj, **kwargs):
        """Возвращает паттерн файлов fsdump в формате текущей схемы."""
        kwargs.setdefault(
            'date',
            self._get_regex_by_strftime(
                self.formatter.get_format_spec(
                    self.pgdump_fileformat, key='date',
                ),
            ),
        )
        field_values = dict(self._static_values, **kwargs)
        return self.formatter.format(self.fsdump_fileformat, **field_values)

    def get_pgdump_pattern(self, obj, **kwargs):
        """Возвращает паттерн файлов pgdump в формате текущей схемы."""
        kwargs.setdefault(
            'date',
            self._get_regex_by_strftime(
                self.formatter.get_format_spec(
                    self.pgdump_fileformat, key='date',
                ),
            ),
        )
        kwargs.setdefault('dbname', r'[^-\s]+')
        field_values = dict(self._static_values, **kwargs)
        return self.formatter.format(self.pgdump_fileformat, **field_values)

    @staticmethod
    def _get_regex_by_strftime(strftime):
        strftime = strftime.replace(r'%d', r'(?:0[1-9]|[1-2]\d|30|31)')
        strftime = strftime.replace(r'%m', r'(?:0[1-9]|1[0-2])')
        strftime = strftime.replace(r'%Y', r'(?:\d{4})')
        strftime = strftime.replace(r'%H', r'(?:[0-1]\d|2[0-4])')
        strftime = strftime.replace(r'%M', r'(?:[0-5]\d)')
        strftime = strftime.replace(r'%S', r'(?:[0-5]\d)')
        return strftime

    def _check_params_presence(self, fileformat):
        """Проверяет наличие неконтекстных параметров."""
        for field_tuple in self.formatter.parse(format_string=fileformat):
            field = field_tuple[1]
            if field and field not in self._reserved_keywords:
                try:
                    self._static_values[field] = self.__getattribute__(field)
                except AttributeError:
                    exc = AttributeError(
                        'В схеме {0} отсутвует параметр {1}'.format(
                            self.scheme_id,
                            field,
                        )
                    )
                    exc.__cause__ = None
                    raise exc
