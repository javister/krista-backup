#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from common.Logging import get_generic_logger

from ..AppRunner import AppRunner
from .app import app
from .WebAppConfig import webappconf


class WebApp(AppRunner):

    name = 'web'

    def run_app(self):
        app.logger = get_generic_logger()
        app.config.from_object(webappconf)
        app.logger.debug('App configured')
        print("To open APP go to: http://%s:%d/" % (webappconf.HOST, webappconf.PORT))
        app.run(host=webappconf.HOST, port=webappconf.PORT)


if __name__ == '__main__':
    app = WebApp()
    print(app.name)
    app.run()
