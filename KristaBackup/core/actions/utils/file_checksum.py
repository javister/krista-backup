# -*- encoding: utf-8 -*-

import hashlib
import os


def create_sha1sum_file(src_file, dest_file):
    """Считает SHA1 сумму файла и записывает её в новый файл.

    Args:
        src_file: Строка, путь к файлу хэш которого требуется найти.
        dest_file: Строка, путь к файлу, в который нужно записать результат.

    Raises:
        FileNotFoundError, если src_file не существует/ не является файлом
        PermitionError, если нет доступа к src_file или dest_file

    """
    if not os.path.isfile(src_file):
        raise FileNotFoundError('Исходный файл не найден')
    buf_size = 65536
    sha1 = hashlib.sha1()
    with open(dest_file, 'w') as dest_file:
        with open(src_file, 'rb') as file_content:
            while True:
                part = file_content.read(buf_size)
                if not part:
                    break
                sha1.update(part)
        hash_value = sha1.hexdigest()
        dest_file.write(hash_value)
        return hash_value
