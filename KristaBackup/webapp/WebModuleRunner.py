#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from functools import wraps

from lib.bottle import Bottle, request, response
from model import Logging
from model.Logging import get_generic_logger
from model.RemoteServerApi import get_server_info, get_server_config
from model.YamlConfig import AppConfig
from webapp.AppRunner import AppRunner

app = Bottle()

logger = get_generic_logger()

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

@app.route('/rl/:dir/:name', method=['GET'])
def get_rl(dir, name):
    try:
        return Logging.get_log_content(dir, name)
    except Exception as e:
        return {'status': e}


def log_to_logger(fn):
    @wraps(fn)
    def _log_to_logger(*args, **kwargs):
        actual_response = fn(*args, **kwargs)
        logger.info('%s %s %s %s' % (request.remote_addr, request.method, request.url, response.status))
        return actual_response
    return _log_to_logger


class WebModule(AppRunner):

    name = 'webapi'

    def get_config(self):
        conf = {}
        conf['host'] = '127.0.0.1'
        conf['port'] = 5556
        if AppConfig.conf().get('web'):
            conf['host'] = AppConfig.conf().get('web').get('host', '127.0.0.1')
            conf['port'] = AppConfig.conf().get('web').get('port', 5556)

        return conf

    def run_app(self):
        api_app = Bottle()
        api_app.install(log_to_logger)
        app.install(log_to_logger)
        api_app.mount('/api/', app)
        conf = self.get_config()
        api_app.config['host'] = conf['host']
        api_app.config['port'] = conf['port']
        api_app.run(host=api_app.config['host'], port=api_app.config['port'])


if __name__ == '__main__':
    app = WebModule()
    print(app.name)
    app.run()
