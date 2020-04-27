# -*- coding: UTF-8 -*-

import os
import sys
import traceback

from flask import (Flask, flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import (LoginManager, current_user, fresh_login_required,
                         login_required, login_user, logout_user)
from werkzeug.urls import url_parse

from common import Logging
from common.daemon_managers import crontab_manager
from common.YamlConfig import AppConfig

from .. import RemoteServerApi, RemoteServers
from . import Users
from .Forms import LoginForm, RegistrationForm, ScheduleForm, ServersForm
from .Users import admin_required
from common import procutil

path = os.path.join(
    os.path.dirname(procutil.get_entrypoint_path()),
    'web',
    'webapp',
)

app = Flask(
    __name__,
    root_path=path,
)

login = LoginManager(app)
login.login_view = 'login'


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'eye_icn.png')


@app.after_request
def after_request(response):
    if response.status_code != 500:
        app.logger.info('%s %s %s %s %s',
                        request.remote_addr,
                        request.method,
                        request.scheme,
                        request.full_path,
                        response.status)
    return response


@app.errorhandler(Exception)
def exceptions(e):
    tb = traceback.format_exc()
    app.logger.error('%s %s %s %s 5xx INTERNAL SERVER ERROR\n%s',
                     request.remote_addr, request.method, request.scheme, request.full_path,
                     tb)
    return "Internal Server Error", 500


@login.user_loader
def load_user(id):
    return Users.get(id)


"""
    Раутинг веб-приложения, функции возвращают веб-страницы
"""


@app.route('/', methods=['GET', 'POST'])
@login_required
def servers():
    form = ServersForm()
    if form.validate_on_submit():
        url = form['address'].data
        if not RemoteServers.isRegistred(url):
            RemoteServers.add(url)
            flash('Добавлен сервер ' + url)
        else:
            flash('Cервер ' + url + ' уже зарегистрирован')
    RemoteServers.updateAll()
    return render_template('servers.html', full_name='Зарегистрированные сервера',
                           servers=RemoteServers.get_all(), form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('servers'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.get(form.username.data)
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('servers')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('servers'))


@app.route('/info/<hash>', methods=['GET'])
@login_required
def info(hash):
    if hash == '0':
        try:
            schedules = crontab_manager.get_tasks_with_info()
        except Exception as exc:
            app.logger.error('Ошибка при получении crontab: %s', exc)
            flash(str(exc))
            schedules = []
        return render_template('info.html', full_name=AppConfig.get_server_name(), remote=False,
                               schedules=schedules, sorted_schedules=sorted(
                                   schedules),
                               actions=AppConfig.conf().get('actions'), sorted_actions=sorted(AppConfig.conf().get('actions')),
                               logs=Logging.get_logs_list())
    else:
        s = RemoteServers.find_server(hash)
        if s is None or not s.state:
            return redirect(url_for('servers'))
        resp = RemoteServers.get_remote_server_config(s.url)
        if len(resp) < 2:
            from collections import defaultdict
            flash(resp.get('status', 'Возникла неизвестная ошибка'))
            resp = defaultdict(dict)
        return render_template('info.html', full_name=resp['full_name'], hash=s.hash, remote=True,
                               schedules=resp['schedules'], sorted_schedules=sorted(
                                   resp['schedules']),
                               actions=resp['actions'], sorted_actions=sorted(
                                   resp['actions']),
                               logs=resp['logs'])


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('servers'))
    form = RegistrationForm()
    if form.validate_on_submit():
        Users.add(form.username.data, form.email.data, form.password.data)
        flash(u'Поздравляем, вы теперь зарегистрированный пользователь!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/sch-add', methods=['GET', 'POST'])
@login_required
@admin_required
def addSchedule():
    form = ScheduleForm()
    if form.validate_on_submit():
        try:
            crontab_manager.update_task(form.name.data, form.cron.data,
                                        form.descr.data, form.actions.data)
        except Exception as exc:
            flash('Произошла ошибка:'.format(exc))
        else:
            flash('Изменения применены')
        return redirect(url_for('servers'))
    return render_template('add_schedule.html', edit=False,
                           form=form,
                           actions=AppConfig.conf().get('actions'),
                           sorted_actions=sorted(AppConfig.conf().get('actions')))


@app.route('/sch-ed/<name>', methods=['GET', 'POST'])
@login_required
@admin_required
def editSchedule(name):
    form = ScheduleForm()
    if not form.validate_on_submit():
        sch = crontab_manager.get_task(name)
        form['name'].data = name
        form['descr'].data = sch['descr']
        form['cron'].data = sch['cron']
        form['actions'].data = ', '.join(sch['actions'])
    else:
        crontab_manager.update_task(form.name.data, form.cron.data,
                                    form.descr.data, form.actions.data)
        flash('Изменения применены')
        return redirect(url_for('servers'))
    return render_template('add_schedule.html', edit=True, form=form,
                           actions=AppConfig.conf().get('actions'), sorted_actions=sorted(AppConfig.conf().get('actions')))


@app.route('/sch-confirm/<name>', methods=['GET', 'POST'])
@fresh_login_required
@admin_required
def confirmDeleteSchedule(name):
    return render_template(
        'del_confirm.html', obj_type='"расписание"', obj_name=name,
        return_link=url_for('servers'), del_link=url_for('sch-del', name=name.strip()),
        )


@app.route('/sch-del/<name>', methods=['GET', 'POST'])
@login_required
@admin_required
def deleteSchedule(name):
    crontab_manager.delete_task(name)
    return redirect(url_for('servers'))


@app.route('/sch-en/<name>', methods=['GET', 'POST'])
@fresh_login_required
@admin_required
def enableSchedule(name):
    crontab_manager.activate_task(name)
    flash('Изменения применены ' + name)
    return redirect(url_for('servers'))


@app.route('/sch-dis/<name>', methods=['GET', 'POST'])
@fresh_login_required
@admin_required
def disableSchedule(name):
    crontab_manager.deactivate_task(name)
    flash('Изменения применены ' + name)
    return redirect(url_for('servers'))


@app.route('/logs/<dir>/<name>', methods=['GET'])
@login_required
def get_log(dir, name):
    return render_template('log.html', full_name=AppConfig.get_server_name(),
                           dir=dir, log=Logging.get_log_content(dir, name))


@app.route('/rlogs/<shash>/<dir>/<name>', methods=['GET'])
@login_required
def get_remote_log(shash, dir, name):
    s = RemoteServers.find_server(shash)
    if s is None or not s.state:
        return redirect(url_for('servers'))
    logs = RemoteServers.get_remote_server_logs(s.url, dir, name)
    return render_template('log.html', full_name=s.name, dir=dir, log=logs)


@app.route('/logp/<dir>/<name>', methods=['GET'])
@login_required
def get_logp(dir, name):
    return send_from_directory(directory=os.path.join(Logging.get_log_dirpath(), dir), filename=name)


@app.route('/s-confirm/<hash>', methods=['GET'])
@fresh_login_required
@admin_required
def confirmDeleteServer(hash):
    s = RemoteServers.find_server(hash)
    if s is None:
        flash('Сервер не найден в списке')
        return redirect(url_for('servers'))
    return render_template('del_confirm.html', obj_type='"Сервер"', obj_name=s.url,
                           return_link=url_for('servers'), del_link=url_for('deleteServers', hash=hash))


@app.route('/s-del/<hash>', methods=['GET'])
@fresh_login_required
@admin_required
def deleteServers(hash):
    s = RemoteServers.find_server(hash)
    RemoteServers.delete(hash)
    flash('Сервер ' + s.url + ' удален')
    return redirect(url_for('servers'))


@app.route('/users', methods=['GET'])
@login_required
@admin_required
def users():
    RemoteServers.updateAll()
    return render_template('users.html', full_name='Пользователи системы', users=Users.users)


@app.route('/u-confirm/<name>', methods=['GET'])
@fresh_login_required
@admin_required
def confirmDeleteUser(name):
    return render_template('del_confirm.html', obj_type='"Пользователь"', obj_name=name,
                           return_link=url_for('servers'), del_link=url_for('deleteUser', name=name.strip()))


@app.route('/u-del/<name>', methods=['GET'])
@fresh_login_required
@admin_required
def deleteUser(name):
    Users.delete(name)
    flash('Пользователь ' + name + ' удален')
    return redirect(url_for('users'))


@app.route('/mka/<name>', methods=['GET'])
@fresh_login_required
@admin_required
def makeAdminUser(name):
    Users.setAdmin(name, True)
    flash('Пользователю ' + name + ' добавлены админские права')
    return redirect(url_for('users'))


@app.route('/mku/<name>', methods=['GET'])
@fresh_login_required
@admin_required
def makeGuestUser(name):
    Users.setAdmin(name, False)
    flash('У пользователя ' + name + ' отобраны админские права')
    return redirect(url_for('users'))


"""
    Раутинг веб-api, функции возвращают json
"""


@app.route('/api/si', methods=['GET'])
def trigger_status():
    try:
        return RemoteServerApi.get_server_info()
    except Exception as e:
        return {'status': e}


@app.route('/api/cf', methods=['GET'])
def si():
    try:
        return RemoteServerApi.get_server_config()
    except Exception as e:
        return {'status': str(e)}


@app.route('/api/rl/<dir>/<name>', methods=['GET'])
def get_logapi(dir, name):
    try:
        return Logging.get_log_content(dir, name)
    except Exception as e:
        return {'status': e}
