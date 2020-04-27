import string
import datetime


class SchemeFormatter(string.Formatter):

    def format_field(self, value, format_spec):
        if isinstance(value, datetime.datetime):
            value = value.strftime(format_spec)
        format_spec = ''
        return super().format_field(value, format_spec)

    def get_format_spec(self, fileformat, key):
        """Возвращает спецификацию формата по имени параметра.

        Returns:
            str или None

        """
        for field_tuple in self.parse(format_string=fileformat):
            if field_tuple[1] == key:
                return field_tuple[2]
