# -*- coding: UTF-8 -*-
from model.YamlConfig import AppConfig


class webappconf:
    HOST = '127.0.0.1'
    if 'web' in AppConfig.conf().keys():
        HOST = AppConfig.conf().get('web').get('host', '127.0.0.1')
    PORT = 5555
    if AppConfig.conf().get('web') and 'port' in AppConfig.conf().get('web', {}).keys():
        PORT = AppConfig.conf().get('web').get('port', '5555')
    CSRF_ENABLED = True
    SECRET_KEY = 'you-will-never-guess'
    LOGIN_MESSAGE = u'Пожалуйста, авторизуйтесь для доступа к этой странице.'
    DEBUG = False
