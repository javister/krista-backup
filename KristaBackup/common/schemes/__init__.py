from .scheme_factory import SchemeFactory
from .schemes import schemes


_default_scheme_id = 'default'


def get_scheme(scheme_id=None):
    """Возвращает схему по scheme_id.

    Args:
        scheme_id: Строка, уникальное имя схемы.

    Returns:
        Scheme или None, если схемы с scheme_id не существует.

    """
    global _default_scheme_id
    if not scheme_id:
        scheme_id = _default_scheme_id
    scheme = schemes.get(scheme_id, None)
    if scheme:
        return scheme()
    return None


def update_scheme(name, new_scheme):
    schemes[name] = new_scheme


def set_default(scheme_id):
    global _default_scheme_id
    _default_scheme_id = scheme_id


def get_scheme_by_config(scheme_config):
    """Возвращает схему по конфигурации.

    Returns:
        Сформированную схему

    Raises:
        Если схема с текущим scheme_id уже существует.

    """
    return SchemeFactory.from_dict(scheme_config)
