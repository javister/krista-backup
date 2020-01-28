#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import logging

from lib.bottle import Bottle
from model.Logging import get_default_handler
from model.RemoteServerApi import get_server_info, get_server_config
from model.YamlConfig import AppConfig
from webapp.AppRunner import AppRunner

app = Bottle()

@app.route('/si', method=['GET'])
def si():
    try:
        return get_server_info()
    except Exception as e:
        return {'status': e}


@app.route('/cf', method=['GET'])
def si():
    try:
        return get_server_config()
    except Exception as e:
        return {'status': e}


class WebModule(AppRunner):

    name = 'webapi'

    def get_config(self):
        conf = {}
        conf['host'] = '127.0.0.1'
        conf['port'] = 5556
        if 'web' in dir(AppConfig.conf()):
            conf['host'] = AppConfig.conf().web.get('host', '127.0.0.1')
            conf['port'] = AppConfig.conf().web.get('port', 5556)

        return conf

    def run_app(self):

        api_app = Bottle()

        logging.getLogger('bottle').addHandler(get_default_handler('app_runner'))
        logging.getLogger('bottle.exception').addHandler(get_default_handler('app_runner'))

        api_app.mount('/api/', app)

        conf = self.get_config()

        api_app.config['host'] = conf['host']
        api_app.config['port'] = conf['port']

        api_app.run(host=api_app.config['host'], port=api_app.config['port'])


if __name__ == '__main__':
    app = WebModule()
    print(app.name)
    app.run()
