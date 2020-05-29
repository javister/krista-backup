# -*- coding: UTF-8 -*-

import os
import shutil
from datetime import datetime

from common import schemes as schemes

from common.procutil import get_entrypoint_path

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
    _server_name = 'current_server'

    _start_time = datetime.now()

    _filename_dateformat = '%Y%m%d_%H%M%S'
    _start_time_str = _start_time.strftime(_filename_dateformat)
    # Формат имени лога и создаваемых файлов.

    _log_dateformat = '%Y-%m-%d %H:%M:%S'
    # Формат времени в логах, совпадает с syslog: YYYY-MM-DD hh:mm:ss

    try:
        from flask import app
    except (ImportError, SyntaxError):
        flask_on = False
    else:
        flask_on = True

    @classmethod
    def get_log_dateformat(cls):
        return cls._log_dateformat

    @classmethod
    def get_filename_dateformat(cls):
        return cls._filename_dateformat

    @classmethod
    def get_starttime(cls):
        return cls._start_time

    @classmethod
    def get_starttime_str(cls):
        return cls._start_time_str

    @classmethod
    def get_server_name(cls):
        if cls._config is None:
            cls.load()
        return cls._server_name

    @classmethod
    def set_unit_name(cls, unit_name):
        if unit_name == 'all':
            return
        schedule = cls.conf().setdefault('schedule', {})
        if unit_name in schedule:
            # попытка достать название проекта и региона
            # если unit оказался заданием
            naming = schedule[unit_name].get('naming', {})
            if 'project' in naming:
                cls._project = str(naming.get('project'))
            if 'region' in naming:
                cls._region = str(naming.get('region'))
            if 'naming_scheme' in naming:
                cls._update_naming_scheme(naming.get('naming_scheme'))

        try:
            cls._project
        except AttributeError:
            exc = ConfigError(
                'Не задан проект в файле конфигурации {0}'
                .format(cls._config_filename),
            )
            exc.__cause__ = None
            raise exc

        try:
            cls._region
        except AttributeError:
            exc = ConfigError(
                'Не задан регион в файле конфигурации {0}'
                .format(cls._config_filename),
            )
            exc.__cause__ = None
            raise exc

    @classmethod
    def load(cls):
        paths = [
            ('.', cls._config_filename),
            (os.path.dirname(get_entrypoint_path()), cls._config_filename),
            (cls._config_default_dirpath, cls._config_filename),
        ]
        for dirname, filename in paths:
            config_path = os.path.join(dirname, filename)
            try:
                cls._config = YamlConfigMapper(config_path)
            except ConfigError:
                raise
            except (FileNotFoundError, TypeError) as exc:
                pass
            else:
                cls._config_filename = os.path.abspath(config_path)
                break
        else:
            exc = FileNotFoundError('Конфигурация не найдена!')
            exc.__cause__ = None
            raise exc
        cls.parse_config()

    @classmethod
    def conf(cls):
        """Возвращает конфигурацию приложения.

        Raises:
            FileNotFoundError: Если файл конфигурации не найден
            ConfigError: Если есть ошибки в содержимом конфигурации  
        """
        if cls._config is None:
            cls.load()
        return cls._config.config

    @classmethod
    def parse_config(cls):
        if 'server_name' not in cls.conf().get('naming', {}):
            raise ConfigError(
                'Не задано имя сервера в файле конфигурации {0}'.format(
                    cls._config_filename,
                ),
            )
        else:
            cls._server_name = cls.conf().get('naming').get('server_name')

        # Cтандартное значение региона
        if 'region' in cls.conf().get('naming'):
            cls._region = str(cls.conf().get('naming')['region'])

        # Cтандартное значение проекта
        if 'project' in cls.conf().get('naming'):
            cls._project = cls.conf().get('naming')['project']

        # Настройка стандартной схемы именования
        if 'naming_scheme' in cls.conf().get('naming'):
            scheme = cls.conf().get('naming')['naming_scheme']
            cls._update_naming_scheme(scheme)

        for s_name in sorted(cls.conf().get('schedule')):
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

    @staticmethod
    def _update_naming_scheme(scheme):
        if not scheme:
            return
        if isinstance(scheme, dict):
            scheme = schemes.get_scheme_by_config(scheme)
            scheme_id = scheme.scheme_id
        else:
            scheme_id = str(scheme)
        schemes.set_default(scheme_id)


class YamlConfigMapper:
    """Класс нужен загрузки/обновления файлов конфигураций."""

    def __init__(self, filepath):
        self.filepath = filepath
        self.config = None

        try:
            self.load_all()
        except yaml.scanner.ScannerError as exc:
            exc.__cause__ = None
            exc = ConfigError(str(exc))
            raise exc

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
