# -*- coding: UTF-8 -*-

import os
import sys
import traceback

from flask import render_template, url_for, flash, redirect, request, send_from_directory, Flask
from flask_login import current_user, logout_user, login_required, login_user, fresh_login_required, LoginManager
from werkzeug.urls import url_parse
from model import Logging, RemoteServers, Users, Schedules
from model.RemoteServerApi import get_server_info, get_server_config
from model.RemoteServers import get_remote_server_config
from model.Users import admin_required
from model.YamlConfig import AppConfig
from webapp.Forms import LoginForm, ScheduleForm, RegistrationForm, ServersForm

sys.path.insert(0, "/opt/KristaBackup")
sys.path.insert(1, os.getcwd())

app = Flask(__name__)

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
    if hash=='0':
        schedules = Schedules.get_schedules()
        return render_template('info.html', full_name=AppConfig.get_server_name(),
                               schedules=schedules, sorted_schedules=sorted(schedules),
                               actions=AppConfig.conf().actions, sorted_actions=sorted(AppConfig.conf().actions),
                               logs=Logging.get_logs_list())
    else:
        s = RemoteServers.find_server(hash)
        if s is None or not s.state:
            return redirect(url_for('servers'))
        resp = get_remote_server_config(s.url)
        return render_template('info.html', full_name = resp['full_name'],
                               schedules = resp['schedules'], sorted_schedules = sorted(resp['schedules']),
                               actions = resp['actions'], sorted_actions = sorted(resp['actions']),
                               logs = resp['logs'])


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
        Schedules.update_schedule(form.name.data, form.cron.data, form.descr.data, form.actions.data)
        flash('Изменения применены')
        return redirect(url_for('servers'))
    return render_template('add_schedule.html', edit=False,
                           form=form,
                           actions=AppConfig.conf().actions,
                           sorted_actions=sorted(AppConfig.conf().actions))


@app.route('/sch-ed/<name>', methods=['GET', 'POST'])
@login_required
@admin_required
def editSchedule(name):
    form = ScheduleForm()
    if not form.validate_on_submit():
        sch = Schedules.get_schedule(name)
        form['name'].data = name
        form['descr'].data = sch['descr']
        form['cron'].data = sch['cron']
        form['actions'].data = ', '.join(sch['actions'])
    else:
        Schedules.update_schedule(form.name.data, form.cron.data, form.descr.data, form.actions.data)
        flash('Изменения применены')
        return redirect(url_for('servers'))
    return render_template('add_schedule.html', edit=True, form=form,
           actions=AppConfig.conf().actions, sorted_actions = sorted(AppConfig.conf().actions))


@app.route('/sch-confirm/<name>', methods=['GET', 'POST'])
@fresh_login_required
@admin_required
def confirmDeleteSchedule(name):
    return render_template('del_confirm.html', obj_type='"расписание"', obj_name=name,
                           return_link=url_for('servers'), del_link=url_for('sch-del',  name=name.strip()))


@app.route('/sch-del/<name>', methods=['GET', 'POST'])
@login_required
@admin_required
def deleteSchedule(name):
    Schedules.delete_schedule(name)
    return redirect(url_for('servers'))


@app.route('/sch-en/<name>', methods=['GET', 'POST'])
@fresh_login_required
@admin_required
def enableSchedule(name):
    Schedules.activate_schedule(name)
    flash('Изменения применены ' + name)
    return redirect(url_for('servers'))


@app.route('/sch-dis/<name>', methods=['GET', 'POST'])
@fresh_login_required
@admin_required
def disableSchedule(name):
    Schedules.deactivate_schedule(name)
    flash('Изменения применены ' + name)
    return redirect(url_for('servers'))


@app.route('/logs/<dir>/<name>', methods=['GET'])
@app.route('/api/log', methods=['GET'])
@login_required
def get_log(dir, name):
    return render_template('log.html', full_name=AppConfig.get_server_name(),
                           dir=dir, log=Logging.get_log_content(dir, name))


@app.route('/logp/<dir>/<name>', methods=['GET'])
@login_required
def get_logp(dir, name):
    return send_from_directory(directory=os.path.join(Logging.get_log_path(), dir), filename=name)


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
    flash('Сервер ' + s.url +' удален')
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
    flash('Пользователь ' + name +' удален')
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
        return get_server_info()
    except Exception as e:
        return {'status': e}


@app.route('/api/cf', methods=['GET'])
def si():
    try:
        return get_server_config()
    except Exception as e:
        return {'status': e}
