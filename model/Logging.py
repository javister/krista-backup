# -*- coding: UTF-8 -*-
import logging
import os
import sys

from logging.handlers import RotatingFileHandler
from model.YamlConfig import AppConfig
from model.TriggerHandler import TriggerHandler
"""
    Вспомогательные методы для конфигурирования разных модулей из тестовых конфигураций
"""

DEFAULT_LOGS_PATH = '/var/log/KristaBackup'


def get_log_path():
    try:
        path = AppConfig.conf().logging.get(
            'logs_path',
            os.path.abspath(DEFAULT_LOGS_PATH),
        )
    except Exception:
        path = os.path.abspath(DEFAULT_LOGS_PATH)
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def get_trigger_filepath():
    try:
        trigger_filepath = AppConfig.conf().logging.get('trigger_filepath')
    except Exception:
        return ''
    if not trigger_filepath:
        return trigger_filepath
    trigger_dirpath = os.path.dirname(trigger_filepath)
    if trigger_dirpath and not os.path.exists(trigger_dirpath):
        os.makedirs(trigger_dirpath)
    return trigger_filepath


def get_formatter(full_name):
    rec_format = ' '.join(
        [
            '%(asctime)s.%(msecs)-3d',
            full_name,
            '%(levelname)s',
            '%(name)s',
            '%(message)s',
        ],
    )
    date_format = AppConfig.get_log_dateformat()
    return logging.Formatter(rec_format, date_format)


def get_default_handler(name):

    full_name = AppConfig.get_server_name()
    log_filename = ".".join(["-".join([full_name, name]), "log"])
    web_log_path = os.path.join(get_log_path(), name)

    if not os.path.exists(web_log_path):
        os.mkdir(web_log_path)

    rotating_file_handler = RotatingFileHandler(
        os.path.join(web_log_path, log_filename),
        mode="a",
        maxBytes=10240000,
        backupCount=10,
    )

    rotating_file_handler.setLevel(logging.DEBUG)
    rotating_file_handler.setFormatter(get_formatter(full_name))

    return rotating_file_handler


def configure_generic_logger(name='krista_backup'):
    logger = logging.getLogger(name)
    if logger is None:
        logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_default_handler(name))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(get_formatter(name))
    logger.addHandler(console_handler)

    return logger


def configure_task_logger(task_name, verbose=False):

    def configure_handler(handler_type, path, level, formatter=None):
        log_handler = handler_type(path)
        log_handler.setLevel(level)
        if formatter:
            log_handler.setFormatter(formatter)
        return log_handler

    try:
        AppConfig.set_task_name(task_name)
    except Exception:
        full_name = 'created-with-error'
        log_filename = '.'.join([full_name, 'log'])
        log_debug_filename = '.'.join([full_name, 'log'])
    else:
        full_name = '-'.join([
            AppConfig._region, AppConfig._project,
            AppConfig.get_server_name()
        ])
        log_filename = ".".join(
            ["-".join([full_name, AppConfig.get_starttime_str()]), "log"])
        log_debug_filename = ".".join([
            "-".join([full_name,
                      AppConfig.get_starttime_str(), "debug"]), "log"
        ])


    logs_path = get_log_path()
    trigger_filepath = get_trigger_filepath()

    log_path_info = os.path.join(
        logs_path,
        AppConfig.get_starttime().strftime('%Y'),
    )
    if not os.path.exists(log_path_info):
        os.makedirs(log_path_info)

    log_path_debug = os.path.join(logs_path, 'debug')
    if not os.path.exists(log_path_debug):
        os.makedirs(log_path_debug)


    handlers_config = [
        {
            # INFO
            'handler_type': logging.FileHandler,
            'path': os.path.join(log_path_info, log_filename),
            'level': logging.INFO,
            'formatter': get_formatter(full_name),
        },
        {
            # DEBUG
            'handler_type': logging.FileHandler,
            'path': os.path.join(log_path_debug, log_debug_filename),
            'level': logging.DEBUG,
            'formatter': get_formatter(full_name),
        },
    ]

    if verbose or AppConfig.conf().logging.get("use_console", False):
        handlers_config.append({
            'handler_type': logging.StreamHandler,
            'path': sys.stdout,
            'level': logging.DEBUG,
            'formatter': get_formatter(full_name),
        })

    if trigger_filepath:  # Инициализация триггера, если к нему указан путь.
        trigger_directory = os.path.dirname(trigger_filepath)
        if not os.path.exists(trigger_directory):
            os.makedirs(trigger_directory)
        handlers_config.append({
            'handler_type': TriggerHandler,
            'path': trigger_filepath,
            'level': logging.WARNING,
        })

    handlers = [configure_handler(**conf) for conf in handlers_config]

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    for log_handler in handlers:
        logger.addHandler(log_handler)

    return logger


def get_logs_list():
    res = {}
    for dir in os.listdir(get_log_path()):
        if dir == "debug" or os.path.isfile(os.path.join(get_log_path(), dir)):
            continue
        res[dir] = []
        for filename in sorted(os.listdir(os.path.join(get_log_path(), dir)), reverse=True):
            log = {}
            log["name"] = filename
            if dir=='krista_backup' or dir=='error':
                log['debugname'] = ''
            else:
                log['debugname'] = filename
            file_exists, error, warning, msg = analyze_log_file(dir, filename)
            log['exist'] = file_exists
            log['error'] = error
            log['warning'] = warning
            log['msg'] = msg
            res[dir].append(log)
    return res


def analyze_log_file(dir, name):
    file_exists, error, warning = False, False, False
    msg = ""
    filepath = os.path.join(get_log_path(), dir, name)
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
        dir_path = os.path.join(get_log_path(), dir)
        if not os.path.isdir(dir_path) or not dir in os.listdir(get_log_path()):
            return False

        file_path = os.path.join(dir_path, filename)
        if not os.path.isfile(file_path) or not filename in os.listdir(
                dir_path):
            return False

        return True

    content = {}
    lines = []

    if check_path():
        filepath = os.path.join(get_log_path(), dir, filename)
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


def analyze_logs():
    logs = get_logs_list()
    for dir in logs:
        for log in logs[dir]:
            ex, err, warn, msg = analyze_log_file(dir, log["name"])
            if err:
                return True
    return False


def handle_unexpected_exception(exception):
    """
    Обработчик ошибок на этапе инициализации.
    Нужен для того, чтобы инициализировать логгирование
    максимально быстро, вывести ошибку и завершить выполнение.
    """
    from model.Logging import configure_task_logger
    logger = configure_generic_logger(name='error')

    logger.error('Ошибка во время импорта зависимостей: %s', exception, exc_info=True)
    exit(2)
