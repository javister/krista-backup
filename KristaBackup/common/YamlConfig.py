# -*- coding: UTF-8 -*-

import os
import shutil
from datetime import datetime

from lib import yaml

from .procutil import get_entrypoint_path

class AppConfig:
    """Синглетон для хранения конфигурации приложения."""

    _config_filename = 'config.yaml'
    _config_default_path = '/opt/KristaBackup'
    _config = None

    _server_fullname = None
    _start_time = datetime.now()

    _filename_dateformat = '%Y%m%d_%H%M%S'
    _start_time_str = _start_time.strftime(
        _filename_dateformat)  # Для имени лога и создаваемых файлов
    # Для записей в логах используем формат, совпадающий с syslog: YYYY-MM-DD hh:mm:ss
    _log_dateformat = '%Y-%m-%d %H:%M:%S'

    is_packed = False

    try:
        from flask import app
    except Exception:
        flask_on = False
    else:
        flask_on = True

    @staticmethod
    def get_log_dateformat():
        try:
            if AppConfig._config is None:
                AppConfig.conf()
        except Exception:
            pass
        return AppConfig._log_dateformat

    @staticmethod
    def get_filename_dateformat():
        try:
            if AppConfig._config is None:
                AppConfig.conf()
        except Exception:
            pass
        return AppConfig._filename_dateformat

    @staticmethod
    def get_starttime():
        try:
            if AppConfig._config is None:
                AppConfig.conf()
        except Exception:
            pass
        return AppConfig._start_time

    @staticmethod
    def get_starttime_str():
        if AppConfig._config is None:
            AppConfig.conf()
        return AppConfig._start_time_str

    @staticmethod
    def set_unit_name(unit_name):
        schedule = AppConfig.conf().setdefault('schedule', {})
        if unit_name in schedule:
            # попытка достать название проекта и региона
            # если unit оказался заданием
            naming = schedule[unit_name].get('naming', {})
            if 'project' in naming:
                AppConfig._project = str(naming.get('project'))
            if 'region' in naming:
                AppConfig._region = str(naming.get('region'))

        if AppConfig._project is None:
            raise ConfigError(
                'Не задан проект для задания в расписании файла конфигураций {0}'
                .format(AppConfig._config_filename),
            )

        if AppConfig._region is None:
                raise ConfigError(
                    'Не задан регион для задания в расписании файла конфигураций {0}'
                    .format(AppConfig._config_filename),
                )

    @staticmethod
    def get_server_name():
        if AppConfig._config is None:
            AppConfig.conf()

        return AppConfig._server_name

    @staticmethod
    def conf():
        if AppConfig._config is None:
            entrypoint = get_entrypoint_path()
            try:
                AppConfig._config = YamlConfigMapper(
                    os.path.dirname(entrypoint),
                    AppConfig._config_filename,
                )
            except (ConfigError, TypeError, AttributeError) as e:
                AppConfig._config = YamlConfigMapper(
                    AppConfig._config_default_path, AppConfig._config_filename)
            AppConfig.parseConfig()
        return AppConfig._config.config

    @staticmethod
    def parseConfig():
        if 'date_format' in AppConfig.conf().get('logging').keys():
            AppConfig._date_format = AppConfig.conf().get('logging')[
                'date_format']
            AppConfig._start_time_str = datetime.strftime(
                AppConfig._filename_dateformat)

        if not 'server_name' in AppConfig.conf().get('naming').keys():
            raise ConfigError(
                'Не задано имя сервера в файле конфигурации {0}'.format(
                    AppConfig._config_filename,
                ),
            )
        else:
            AppConfig._server_name = AppConfig.conf().get('naming').get('server_name')

        # Cтандартное значение региона
        if 'region' in AppConfig.conf().get('naming').keys():
            AppConfig._region = str(AppConfig.conf().get('naming')['region'])

        # Cтандартное значение проекта
        if 'project' in AppConfig.conf().get('naming').keys():
            AppConfig._project = AppConfig.conf().get('naming')['project']

        for s_name in sorted(AppConfig.conf().get('schedule').keys()):
            sc = AppConfig.conf().get('schedule')[s_name]
            if type(sc) != dict:
                print(sc)
                raise ConfigError("Ошибка в списке расписаний: конфиг не является словарем."
                                  " Проверьте отступы и разделители в разделе schedule: "
                                  " %s: %s" % (s_name, sc))

        for a_name in sorted(AppConfig.conf().get('actions').keys()):
            ac = AppConfig.conf().get('actions')[a_name]
            if type(ac) != dict:
                print(ac)
                raise ConfigError("Ошибка в списке расписаний: конфиг не является словарем."
                                  " Проверьте отступы и разделители в разделе actions: "
                                  " %s: %s" % (s_name, ac))


class YamlConfigMapper:
    """
        Класс YamlConfigMapper взаимодействует с файловой системой - читает файлы конфигураций в yaml
    """

    config_file_name = 'config.yaml'
    config = None

    def __init__(self, path, filename):
        self.config_file_name = filename
        if os.path.exists(self.config_file_name) and os.path.isfile(
                self.config_file_name):
            self.loadAll()
        else:
            apath = path
            if apath is None:
                entrypoint = get_entrypoint_path()
                if entrypoint is not None:
                    apath = os.path.dirname(entrypoint)
                else:
                    apath = AppConfig._config_default_path
            self.config_file_name = os.path.join(apath, filename)
            if os.path.exists(self.config_file_name) and os.path.isfile(
                    self.config_file_name):
                self.loadAll()
            else:
                raise ConfigError("Отсутствует файл конфигурации %s" %
                                  (self.config_file_name,))

    def getConf(self):
        return self.config

    def loadAll(self):
        with open(self.config_file_name, 'r') as stream:
            conf_dict = yaml.load(stream, Loader=yaml.FullLoader)
        if type(conf_dict) == dict:
            self.config = conf_dict
        else:
            raise ConfigError(
                'Невозможно загрузить конфигурацию %s - проверте форматирование файла!'.format(
                    self.config_file_name,)
            )

    def storeAll(self):
        if not os.path.exists('config_history'):
            os.mkdir('config_history')
        bk_filename = os.path.join(
            'config_history', '.'.join([
                self.config_file_name,
                datetime.now().strftime('%Y%m%d_%H%M%S')
            ]))
        shutil.copy(self.config_file_name, bk_filename)
        with open(self.config_file_name, 'w') as stream:
            yaml.dump(
                self.config,
                stream=stream,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )


class ConfigError(Exception):

    def __init__(self, msg):
        if msg:
            self.message = msg
        else:
            self.message = 'Ошибка в конфигурации config.yaml'
