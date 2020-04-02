# -*- coding: UTF-8 -*-

import os
import shutil
from datetime import datetime

from .procutil import get_entrypoint_path

try:
    from lib import yaml
except (ImportError, SyntaxError):
    from lib import yaml_3 as yaml
    old_yaml = True
else:
    old_yaml = False


class AppConfig:
    """Синглетон для хранения конфигурации приложения."""

    _config_filename = 'config.yaml'
    _config_default_dirpath = '/opt/KristaBackup'
    _config = None

    _start_time = datetime.now()

    _filename_dateformat = '%Y%m%d_%H%M%S'
    _start_time_str = _start_time.strftime(_filename_dateformat)
    # Формат имени лога и создаваемых файлов.

    _log_dateformat = '%Y-%m-%d %H:%M:%S'
    # Формат времени в логах, совпадает с syslog: YYYY-MM-DD hh:mm:ss

    is_packed = False

    try:
        from flask import app
    except ImportError:
        flask_on = False
    else:
        flask_on = True

    @classmethod
    def get_log_dateformat(cls):
        if cls._config is None:
            cls.conf()
        return cls._log_dateformat

    @classmethod
    def get_filename_dateformat(cls):
        if cls._config is None:
            cls.conf()
        return cls._filename_dateformat

    @classmethod
    def get_starttime(cls):
        if cls._config is None:
            cls.conf()
        return cls._start_time

    @classmethod
    def get_starttime_str(cls):
        if cls._config is None:
            cls.conf()
        return cls._start_time_str

    @classmethod
    def get_server_name(cls):
        if cls._config is None:
            cls.conf()
        return cls._server_name

    @classmethod
    def set_unit_name(cls, unit_name):
        schedule = cls.conf().setdefault('schedule', {})
        if unit_name in schedule:
            # попытка достать название проекта и региона
            # если unit оказался заданием
            naming = schedule[unit_name].get('naming', {})
            if 'project' in naming:
                cls._project = str(naming.get('project'))
            if 'region' in naming:
                cls._region = str(naming.get('region'))

        if cls._project is None:
            raise ConfigError(
                'Не задан проект для задания в расписании файла конфигураций {0}'
                .format(cls._config_filename),
            )

        if cls._region is None:
            raise ConfigError(
                'Не задан регион для задания в расписании файла конфигураций {0}'
                .format(cls._config_filename),
            )

    @classmethod
    def conf(cls):
        if cls._config is None:
            paths = [
                ('.', cls._config_filename),
                (os.path.dirname(get_entrypoint_path()),
                 cls._config_filename),
                (cls._config_default_dirpath,
                 cls._config_filename,)
            ]
            for dirname, filename in paths:
                config_path = os.path.join(dirname, filename)
                try:
                    cls._config = YamlConfigMapper(config_path)
                except (OSError, ConfigError, TypeError, AttributeError):
                    pass
                else:
                    break
            else:
                raise ConfigError('Конфигурация не найдена!')
            cls.parse_config()
        return cls._config.config

    @classmethod
    def parse_config(cls):
        if 'server_name' not in cls.conf().get('naming').keys():
            raise ConfigError(
                'Не задано имя сервера в файле конфигурации {0}'.format(
                    cls._config_filename,
                ),
            )
        else:
            cls._server_name = cls.conf().get('naming').get('server_name')

        # Cтандартное значение региона
        if 'region' in cls.conf().get('naming').keys():
            cls._region = str(cls.conf().get('naming')['region'])

        # Cтандартное значение проекта
        if 'project' in cls.conf().get('naming').keys():
            cls._project = cls.conf().get('naming')['project']

        for s_name in sorted(cls.conf().get('schedule').keys()):
            sc = cls.conf().get('schedule')[s_name]
            if not isinstance(sc, dict):
                raise ConfigError("Ошибка в списке расписаний: конфиг не является словарем."
                                  " Проверьте отступы и разделители в разделе schedule: "
                                  " %s: %s" % (s_name, sc))

        for a_name in sorted(cls.conf().get('actions').keys()):
            ac = cls.conf().get('actions')[a_name]
            if not isinstance(ac, dict):
                raise ConfigError("Ошибка в списке расписаний: конфиг не является словарем."
                                  " Проверьте отступы и разделители в разделе actions: "
                                  " %s: %s" % (a_name, ac))


class YamlConfigMapper:
    """Класс нужен загрузки/обновления файлов конфигураций."""

    def __init__(self, filepath):
        self.filepath = filepath
        self.config = None

        if os.path.exists(self.filepath) and os.path.isfile(self.filepath):
            self.load_all()
        else:
            raise OSError(
                'Отсутствует файл конфигурации {0}'.format(self.filepath))

    def load_all(self):
        with open(self.filepath, 'r') as stream:
            if not old_yaml:
                conf_dict = yaml.load(stream, Loader=yaml.FullLoader)
            else:
                conf_dict = yaml.load(stream)
        if isinstance(conf_dict, dict):
            self.config = conf_dict
        else:
            raise ConfigError(
                'Невозможно загрузить конфигурацию {0} - проверьте форматирование файла!'.format(
                    self.filepath,
                ),
            )

    def storeAll(self):
        if not os.path.exists('config_history'):
            os.mkdir('config_history')
        bk_filename = os.path.join(
            'config_history', '.'.join([
                self.filepath,
                datetime.now().strftime('%Y%m%d_%H%M%S')
            ]))
        shutil.copy(self.filepath, bk_filename)
        with open(self.filepath, 'w') as stream:
            yaml.dump(
                self.config,
                stream=stream,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )


class ConfigError(Exception):
    pass
