#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from model.Logging import get_generic_logger
from webapp.AppRunner import AppRunner
from webapp.WebAppConfig import webappconf
from webapp.app import app

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
