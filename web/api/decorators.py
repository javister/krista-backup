import hashlib
import time
from functools import wraps

from lib.bottle import abort, request

MAX_DELAY = 30
"""int: Наибольшая разница во временем запроса и временем на сервере."""


def auth_middleware(view):
    """Декоратор, реализующий проверку валидности запроса.

    Проверка происходит при помощи параметров time и hashed_value.
    """
    @static_vars(used=[])
    def check_hash(htime, received_hash):
        current_time = int(time.time())
        print(current_time)
        if abs(current_time - htime) > MAX_DELAY:
            return False

        required_value = request.app.config['SECRET_KEY'].encode('ascii') + str(htime).encode('ascii')
        print(required_value)
        trusted_hash = hashlib.sha224(required_value).hexdigest()
        print(trusted_hash)
        if (trusted_hash != received_hash or
                received_hash in check_hash.used):
            return False

        if len(check_hash.used) > 10:
            check_hash.used.pop()
        check_hash.used.append(received_hash)

        return True

    @wraps(view)
    def wrapper(*args, **kwargs):
        request_time = request.params.get('time')
        request_key = request.params.get('key')

        if request_time is None or request_key is None:
            abort(403)
        try:
            result = check_hash(int(request_time), request_key)
        except:
            abort(403)
        if not result:
            abort(403)

        return view(*args, **kwargs)

    return wrapper


def static_vars(**kwargs):
    def decorate(func):
        for key in kwargs:
            setattr(func, key, kwargs[key])
        return func

    return decorate
