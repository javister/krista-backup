#  -*- coding: UTF-8 -*-

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, EqualTo, Email, Optional

from model import Users


class LoginForm(FlaskForm):
    username = StringField(u'Пользователь', validators=[DataRequired()])
    password = PasswordField(u'Пароль', validators=[DataRequired()])
    remember_me = BooleanField(u'Запомнить меня')
    submit = SubmitField(u'Войти')


class RegistrationForm(FlaskForm):
    username = StringField(u'Логин', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField(u'Пароль', validators=[DataRequired()])
    password2 = PasswordField(
        u'Повторный ввод пароля', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(u'Зарегистрировать')

    def validate_username(self, username):
        user = Users.get(username.data)
        if user is not None:
            raise ValidationError(u'Имя пользователя уже используется.')

    def validate_email(self, email):
        user = Users.get_by_mail(email=email.data)
        if user is not None:
            raise ValidationError(u'Адрес электронной почты уже используется.')

class ServersForm(FlaskForm):
    address = StringField(u'Адрес или URL сервера', validators=[DataRequired()])
    submit = SubmitField(u'Добавить сервер')


class ScheduleForm(FlaskForm):
    name = StringField(u'Название', validators=[DataRequired()])
    descr = StringField(u'Описание', validators=[Optional()])
    cron = StringField(u'Расписание в формате cron', validators=[DataRequired()])
    actions = StringField(u'Задачи (через запятую)') #, validators=[DataRequired()]
    submit = SubmitField(u'Сохранить')
