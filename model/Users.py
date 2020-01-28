#  -*- coding: UTF-8 -*-

from functools import wraps
from flask import current_app, flash, redirect
from flask_login import UserMixin, user_unauthorized
from flask_login.utils import _get_user
from werkzeug.local import LocalProxy
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadSignature, SignatureExpired
from model.YamlConfig import YamlConfigMapper
from webapp.WebAppConfig import webappconf

users = {}

class User(UserMixin):
    id = 'guest'
    mail = 'foo@bar.com'
    password_hash = ''
    adm = False

    @property
    def email(self):
        return self.mail

    # define email setter
    @email.setter
    def email(self, value):
        self.mail = value

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self, expiration = 600):
        s = Serializer(webappconf.config['SECRET_KEY'], expires_in = expiration)
        return s.dumps({ 'id': self.id })

    def is_admin(self):
        return self.adm

    def get_name(self):
        return self.id

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(webappconf['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # valid token, but expired
        except BadSignature:
            return None # invalid token
        user = users[data['id']]
        return user


current_user = LocalProxy(lambda: _get_user())


def admin_required(func):
    """
    Декоратор для представлений, проверяем, что текущий пользователь - админ, иначе запрещаем выполненеи функции
    :param func: The view function to decorate.
    :type func: function
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin():
            user_unauthorized.send(current_app._get_current_object())
            flash("Необходимы права администратора для выполнения операции")
            return redirect("/")
        return func(*args, **kwargs)
    return decorated_view


_users_config_filename = 'users.yaml'
_users = YamlConfigMapper(None, _users_config_filename)

for user in _users.config.users.keys():
    u = User()
    u.id = user
    u.mail = _users.config.users[user]['email']
    u.password_hash = _users.config.users[user]['pass']
    u.adm = _users.config.users[user]['adm']
    users[user] = u

def get(id):
    return users.get(id, None)


def get_by_mail(email):
    for user in users.values():
        if user.mail == email:
            return user
    return None


def add(name, email, password, admin=False):
    u = User()
    u.id = name
    u.mail = email
    u.set_password(password)
    u.adm = admin
    storeUser(name, u)

def storeUser(name, u):
    users[name] = u
    _users.config.users[name] = {
        'email': u.mail,
        'pass': u.password_hash,
        'adm': u.adm
    }
    _users.storeAll()


def setAdmin(name, adm):
    users[name].adm = adm
    _users.config.users[name] = {
        'email': users[name].mail,
        'pass': users[name].password_hash,
        'adm': adm
    }
    _users.storeAll()


def delete(name):
    users.pop(name, None)
    _users.config.users.pop(name, None)
    _users.storeAll()
