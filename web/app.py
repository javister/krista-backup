import logging
import os
import signal
from logging.handlers import RotatingFileHandler

from lib.bottle import Bottle

from model.Logging import get_log_path, get_web_module_logger_handler
from model.YamlConfig import AppConfig
from model.ProcUtil import process_iter
from web.api.app import api_app


class WebModule:
    # Если web module запущен, то возвращает pid
    # В противном случае возвращает None
    @staticmethod
    def check_process():
        pid = os.getpid()
        for process in process_iter():
            if pid != process.pid and 'KristaBackup.py run web_module' in process.cmdline:
                return process.pid
        return None

    @staticmethod
    def run():
        def configure_app(app):
            app.mount('/api/', api_app)
            try:
                config = AppConfig.conf().web_module
                app.config['host'] = config['host']
                app.config['port'] = config['port']
                app.config['SECRET_KEY'] = config['SECRET_KEY']
            except Exception as exc:
                logging.error('Ошибка при конфигурировании:')
                logging.error(repr(exc))
                return False
            return True

        if WebModule.check_process():
            logging.warning('web_module уже запущен!')
            return

        app = Bottle()

        if not configure_app(app):
            return
        app.run(host=app.config['host'], port=app.config['port'])

    @staticmethod
    def stop():
        pid = WebModule.check_process()
        if pid:
            os.kill(pid, signal.SIGINT)


if __name__ == '__main__':
    WebModule.run()
