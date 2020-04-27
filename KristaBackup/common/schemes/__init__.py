from .default_scheme import DefaultNamingScheme
from .scheme_factory import SchemeFactory
from .schemes import schemes


def get_scheme(scheme_id=None):
    """Возвращает схему по scheme_id.

    Args:
        scheme_id: Строка, уникальное имя схемы;
    если None, то возвращает стандартную схему.

    Returns:
        Scheme или None, если схемы с scheme_id не существует.

    """
    if not scheme_id:
        return DefaultNamingScheme()
    scheme_class = schemes.get(scheme_id, None)
    if scheme_class:
        return scheme_class()
    return None


def get_scheme_by_config(scheme_config):
    """Возвращает схему по конфигурации.

    Returns:
        Сформированную схему

    Raises:
        Если схема с текущим scheme_id уже существует.

    """
    return SchemeFactory(scheme_config)
