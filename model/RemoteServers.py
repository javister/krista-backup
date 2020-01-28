#  -*- coding: UTF-8 -*-
import hashlib
import json
import requests
from model.YamlConfig import YamlConfigMapper


class Server:
    url = ''
    name = 'Неизвестно'
    hash = ''

    flask = False
    msg = ''
    errors = ''
    msg = ''


    def update(self):
        print(self.url)
        status_url = '/'.join(map(lambda x: str(x).strip('/'), [self.url, 'api/si']))
        try:
            r = requests.get(status_url)
            print(r.content)
            if (r.ok):
                self.state = True
                jr = json.loads(r.content)
                self.name = jr.get('name', 'неизвестно')
                self.flask = jr.get('flask', False)
                self.msg = jr.get('msg', '')
                self.errors = jr.get('errors', '')
            else:
                self.state = False
                self.msg = 'ошибка при обращении к серверу'
                self.errors = 'HTTP Code %s, content: %s' % (str(r.status_code), str(r.content))
        except Exception as ex:
            self.state = False
            self.msg = 'исключение при обращении к серверу'
            self.errors = ex.__repr__()


    def __repr__(self):
        return "Server(%s, %s, %s, %s, %s)" % (self.url, self.name, self.errors, self.state)


def get_hash(url):
    if s.url is None:
        return None
    h = hashlib.md5()
    h.update(s.url.encode('utf-8'))
    return h.hexdigest()

_servers_config_filename = 'servers.yaml'
_servers_conf = YamlConfigMapper(None, _servers_config_filename)
servers = []
for s_conf in _servers_conf.config.servers:
    s = Server()
    s.url = s_conf
    s.hash = get_hash(s.url)
    s.update()
    servers.append(s)
    print(s_conf, s.url, s.hash)
servers = sorted(servers, key=lambda x: x.name)


def get_all():
    return servers


def updateAll():
    for s in servers:
        s.update()


def isRegistred(url):
    for s in servers:
        if s.url == url:
            return True
    return False


def add(url):
    s = Server()
    s.url = url
    s.hash = get_hash(s.url)
    s.update()
    servers.append(s)
    _servers_conf.config.servers.append(url)
    _servers_conf.storeAll()


def find_server(hash):
    for s in servers:
        if hash == s.hash:
            return s
    return None


def delete(hash):
    s = find_server(hash)
    if not s is None:
        servers.remove(s)
        for srv in _servers_conf.config.servers:
            _servers_conf.config.servers.remove(srv)
        _servers_conf.storeAll()


def get_remote_server_config(surl):
    status_url = '/'.join(map(lambda x: str(x).strip('/'), [surl, 'api/cf']))
    print('status_url', surl, status_url)
    try:
        r = requests.get(status_url)
        if (r.ok):
            return json.loads(r.content)
    except Exception as ex:
        return {'state': 'Ошибка доступа: %s, %s' % (type(ex).__name__, str(ex))}
