# -*- coding: UTF-8 -*-


def get_mount_dev(point):
    """Возвращает устройство по точке монтирования.

    Args:
        point (str): путь к точке монтирования.
    Returns:
        str или None, если point не является точкой монтирования.

    """
    with open('/proc/mounts', 'r') as mounts:
        for line in mounts:
            line = line.split()
            if line[1] == point:
                return line[0]
    return None
