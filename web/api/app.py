from lib.bottle import Bottle, request
from model.Logging import get_log_content, get_logs_list, get_trigger_filepath

from .decorators import auth_middleware

api_app = Bottle()


@api_app.route('/ping', method='GET')
def ping():
    return 'pong'


@api_app.route('/trigger_status', method='GET')
@auth_middleware
def trigger_status():
    try:
        with open(get_trigger_filepath(), 'r') as trigger:
            return {'status': trigger.read()}
    except Exception as e:
        return {'error': e.__repr__()}


@api_app.route('/logs', methods='GET')
@auth_middleware
def name():
    directory = request.params.get('dir')
    logfile = request.params.get('file')

    if directory and logfile:
        return str(get_log_content(directory.strip(), logfile.strip()))
    return get_logs_list()
