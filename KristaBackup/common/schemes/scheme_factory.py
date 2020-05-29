import uuid

from .schemes import schemes
from .default_scheme import DefaultNamingScheme


class SchemeFactory:

    @staticmethod
    def from_dict(scheme_params):
        """Возвращает новую схему по переданным параметрам.

        Args:
            scheme_params: Словарь, naming_scheme из config.yaml

        Raises:
            KeyError, если схема с таким scheme_id уже существует

        """
        scheme_params.setdefault(
            'scheme_id',
            'CustomNamingScheme_{uniq_id}'.format(
                uniq_id=generate_random_string(),
            ),
        )
        custom_scheme = type(
            scheme_params['scheme_id'],
            (
                DefaultNamingScheme,
            ),
            scheme_params,
        )
        if custom_scheme.scheme_id in schemes:
            raise KeyError(
                'Схема с scheme_id {0} уже существует.'.format(
                    custom_scheme.scheme_id,
                ),
            )
        schemes[custom_scheme.scheme_id] = custom_scheme
        return custom_scheme()


def generate_random_string():
    """Генерирует случайную строку из 6 печатаемых символов."""
    return uuid.uuid4().hex.upper()[0:6]
