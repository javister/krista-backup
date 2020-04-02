import random
import string
import datetime

from common.YamlConfig import AppConfig

alphabet = string.ascii_lowercase + string.ascii_uppercase + string.digits


def get_random_string(length=6):
    """Возвращает случайную строку из букв и цифр.

    Args:
        length: Целое число, длина требуемой строки

    """
    return ''.join(random.choice(alphabet) for _ in range(length))
