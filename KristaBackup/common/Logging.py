# -*- coding: UTF-8 -*-

import datetime
import logging
import os
import sys
import time
from collections import OrderedDict
from logging.handlers import RotatingFileHandler
from operator import itemgetter

from common.TriggerHandler import TriggerHandler
from common.YamlConfig import AppConfig, ConfigError

DEFAULT_LOGS_PATH = '/var/log/KristaBackup'


def get_log_dirpath(subdir=None):
    """Возвращает путь к директории логирования.

    Если директория не сущестувет, то она создаётся.

    Args:
        subdir: Строка или None, требуемая поддиректория.

    Returns:
        Строку, путь к существующей директории.

    """
    try:
        conf = AppConfig.conf()
    except (FileNotFoundError, ConfigError):
        path = os.path.abspath(DEFAULT_LOGS_PATH)
    else:
        path = conf.get('logging', {}).get(
            'logs_path',
            os.path.abspath(DEFAULT_LOGS_PATH),
        )
    if subdir:
        path = os.path.join(path, subdir)
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def get_trigger_filepath():
    """Возвращает путь к триггеру.

    Рекурсивно создаёт директорию необходимую, если на момент
    инициализации её не существовало.
    Если в конфигурации отстутствует параметр logging.trigger_filepath,
    то возвращает None.

    Returns:
        Строка, путь к триггеру, или None.

    """
    try:
        conf = AppConfig.conf()
    except (FileNotFoundError, ConfigError):
        trigger_filepath = None
    else:
        trigger_filepath = conf.get('logging', {}).get('trigger_filepath')

    if not trigger_filepath:
        return trigger_filepath
    trigger_dirpath = os.path.dirname(trigger_filepath)
    if trigger_dirpath and not os.path.exists(trigger_dirpath):
        os.makedirs(trigger_dirpath)
    return trigger_filepath


def get_formatter(full_name):
    """Возвращает logging.Formatter для логов."""
    rec_pattern = '%(asctime)s.%(msecs)-3d {full_name} %(levelname)s %(name)s %(message)s'
    rec_format = rec_pattern.format(full_name=full_name)
    date_format = AppConfig.get_log_dateformat()
    return logging.Formatter(rec_format, date_format)


def get_default_file_handler(name, path):
    """Возвращает стандартный хэндлер для файла.

    Returns:
        handler

    """
    return get_handler(
        name,
        logging.INFO,
        path=path,
        handler_type=logging.FileHandler,
    )


def get_debug_file_handler(name, path):
    """Возвращает хэндлер для файла с дебагом.

    Returns:
        handler

    """
    return get_handler(
        name,
        logging.DEBUG,
        path=path,
        handler_type=logging.FileHandler,
    )


def get_console_handler(name):
    """Возвращает хэндлер для консоли.

    Returns:
        handler

    """
    return get_handler(name, logging.DEBUG)


def get_trigger_handler():
    """Возвращает хэндлер для консоли.

    Returns:
        handler

    """
    return get_handler(
        'trigger',
        logging.WARNING,
        path=get_trigger_filepath(),
        handler_type=TriggerHandler,
    )


def get_handler(
    name,
    level,
    path=sys.stdout,
    handler_type=logging.StreamHandler,
):
    """Инициализирует хэндлеры для логирования.

    По умолчанию возвращает хэндлер для консоли.

    """
    if handler_type is RotatingFileHandler:
        log_handler = handler_type(
            path,
            maxBytes=10240000,
            backupCount=10,
        )
    else:
        log_handler = handler_type(path)

    if handler_type is not TriggerHandler:
        log_handler.setFormatter(get_formatter(name))

    log_handler.setLevel(level)
    return log_handler


def get_generic_logger(name='krista_backup.log'):
    """Инициализиуерт и возвращает общий логгер.

    Логгеру добавляются два хэндлера:
        - терминал
        - файл

    Args:
        name: Имя логгера

    Returns:
        logger

    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        logger.addHandler(get_console_handler(name))
        try:
            handler = get_debug_file_handler(
                name,
                path=os.path.join(get_log_dirpath('krista_backup'), name),
            )
        except PermissionError as exc:
            message = 'Ошибка при логировании в файл: {0}'.format(exc)
            logger.error(message)
        else:
            logger.addHandler(handler)
    return logger


def configure_logging(verbose=False):
    """Конфигурирует логирование для выполнения заданий/действий.

    Инициализирует и добавляет хэндлеры для логирования.
    Следующие хэндлеры создаются:
        - log_default - INFO, в файл.
        - log_debug - DEBUG, в файл.
        - trigger - >=WARNING, в триггер файл, если он указан в конфиге.
        - stdout - DEBUG, в консоль, если указан параметр verbose.

    Args:
        verbose: Логическое значение, логировать в stdout.

    """
    try:
        full_name = '{region}-{project}-{servername}'.format(
            region=AppConfig._region,
            project=AppConfig._project,
            servername=AppConfig.get_server_name(),
        )
    except AttributeError:
        full_name = 'created-with-error'

    log_filename = '{full_name}-{time}.log'.format(
        full_name=full_name,
        time=AppConfig.get_starttime_str(),
    )
    log_debug_filename = '{full_name}-{time}-debug.log'.format(
        full_name=full_name,
        time=AppConfig.get_starttime_str(),
    )

    log_path_info = get_log_dirpath(
        subdir=AppConfig.get_starttime().strftime('%Y'),
    )
    log_path_debug = get_log_dirpath(subdir='debug')

    handlers = [
        get_default_file_handler(
            full_name,
            os.path.join(log_path_info, log_filename),
        ),
        get_debug_file_handler(
            full_name,
            os.path.join(log_path_debug, log_debug_filename),
        ),
    ]

    if verbose or AppConfig.conf().get('logging', {}).get('use_console', False):
        # Инициализация хэндлера консоли, если стоит verbose или use_console.
        handlers.append(get_console_handler(full_name))

    if get_trigger_filepath():
        # Инициализация хэндлера триггера, если к нему указан путь.
        handlers.append(get_trigger_handler())

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    for log_handler in handlers:
        logger.addHandler(log_handler)


def retrieve_seconds_from_name(filename):
    """Достаёт количество секунд по времени из имени файли.

    Если время достать не удалось, то возвращает -1.

    Returns:
        datetime.datetime с временной отметкой, либо None.

    """
    if '.' in filename:
        dot_index = filename.index('.')
        filename_noext = filename[:dot_index - len(filename)]
    else:
        filename_noext = filename

    splitted = filename_noext.split('-')
    for part in reversed(splitted):
        try:
            dtime = datetime.datetime.strptime(
                part,
                AppConfig._filename_dateformat,
            ).timetuple()
            return time.mktime(dtime)
        except Exception:
            pass
    return -1


def get_logs_list():
    res = {}
    for dir in os.listdir(get_log_dirpath()):
        if dir == "debug" or os.path.isfile(os.path.join(get_log_dirpath(), dir)):
            continue
        res[dir] = []
        for filename in sorted(os.listdir(os.path.join(get_log_dirpath(), dir)), reverse=True):
            log = {}
            log["name"] = filename
            if dir == 'krista_backup' or dir == 'web_api':
                log['debugname'] = ''
            else:
                # Файл для дебаг лога имеет суффикс debug
                log['debugname'] = '{0}-debug{1}'.format(
                    filename[:-4], filename[-4:])
            file_exists, error, warning, msg = analyze_log_file(dir, filename)
            log['exist'] = file_exists
            log['error'] = error
            log['warning'] = warning
            log['msg'] = msg
            res[dir].append(log)

    res = OrderedDict(sorted(res.items(), key=itemgetter(0), reverse=True))
    # сортировка по годам в порядке убывания

    for key, value in res.items():
        # сортировка записей с логами по времени в порядке убывания
        res[key] = sorted(
            value,
            key=lambda entry: retrieve_seconds_from_name(entry.get('name')),
            reverse=True,
        )
    return res


def analyze_log_file(dir, name):
    file_exists, error, warning = False, False, False
    msg = ""
    filepath = os.path.join(get_log_dirpath(), dir, name)
    file_exists = os.path.exists(filepath) and os.path.isfile(filepath)
    if file_exists:
        with open(filepath, "r") as log:
            for line in log:
                if "ERROR" in line or "CRITICAL" in line:
                    error = True
                    msg = line
                    break
                elif "WARNING" in line:
                    warning = True
                    msg = line
    return file_exists, error, warning, msg


def get_log_content(dir, filename):
    # Проверяет существование файла в указанной директории
    def check_path():
        dir_path = os.path.join(get_log_dirpath(), dir)
        if not os.path.isdir(dir_path) or not dir in os.listdir(get_log_dirpath()):
            return False
        file_path = os.path.join(dir_path, filename)
        if not os.path.isfile(file_path) or not filename in os.listdir(dir_path):
            return False
        return True

    content = {}

    if check_path():
        filepath = os.path.join(get_log_dirpath(), dir, filename)
        content["filename"] = filepath
        with open(filepath, "r") as log:
            lines = log.readlines()
            log.close()
    else:
        lines = []

    if len(lines) == 0:
        content["lines"] = "файл отсутствует в файловой системе или нет прав на чтение"
    content["lines"] = lines

    return content
