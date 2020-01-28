#  -*- coding: UTF-8 -*-

import os
from model import Schedules
from model.Logging import get_trigger_filepath, get_logs_list
from model.YamlConfig import AppConfig


def get_server_info():
    result = {}
    result['name'] = str(AppConfig.get_server_name())
    result['flask'] = AppConfig.flask_on
    try:
        tr_file = get_trigger_filepath()
        if os.path.exists(tr_file):
            result['msg'] = 'триггер-файл'
            with open(tr_file, 'r') as trigger:
                result['errors'] = trigger.readlines()
            if not 'ERROR' in result['errors']:
                result['errors'] = ''
                result['msg'] = 'ок'
        else:
            result['msg'] = 'нет триггер-файла'
            result['errors'] = ''
    except Exception as e:
        result['msg'] = 'ошибка обработки запроса'
        result['errors'] = e.__repr__()
    return result


def get_server_config():
    result = {'full_name': AppConfig.get_server_name(), 'schedules': Schedules.get_schedules(),
              'actions': AppConfig.conf().actions, 'logs': get_logs_list()}
    return result
