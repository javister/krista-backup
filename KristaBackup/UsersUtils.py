#!/usr/bin/python3
#  -*- coding: UTF-8 -*-
import argparse

try:
    from web.webapp import Users
except Exception:
    import zipimport
    importer = zipimport.zipimporter('KristaBackup')
    lib = importer.load_module('lib')
    webapp = importer.load_module('webapp')
    Users = importer.load_module('model')


def print_user(user):
    print('Пользователь: {id}, почта: {email}, админ: {adm}'.format(
        id=user.id,
        email=user.email,
        adm=user.adm,
    ),
    )


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Централизованная система бэкапа, работа с пользователями',
    )
    parser.add_argument(
        metavar='действие', dest='action', type=str,
        choices=['check', 'del', 'list', 'add', 'mod'],
        help='требуемое действие (check, del, list, add, mod)',
    )
    parser.add_argument(
        '-u', dest='username', type=str, default=None,
        help='имя пользователя',
    )
    parser.add_argument(
        '-m', dest='email', type=str, default=None,
        help='почтовый адрес',
    )
    parser.add_argument(
        '-p', dest='passw', type=str, default=None,
        help='пароль',
    )
    parser.add_argument(
        '-a', dest='is_adm', default=True, action='store_true',
        help='сделать администратором (add, mod)',
    )

    args = parser.parse_args()
    if args.action == 'check':
        if (args.username is None) and (args.email is None):
            print('Для проверки необходимо передать имя пользователя или его email.')
            exit(-1)
        user = None
        if not (args.username is None):
            user = Users.get(args.username)
        elif not (args.email is None):
            user = Users.get_by_mail(args.email)
        if user is None:
            print('Пользователь не найден.')
        else:
            print_user(user)
    elif args.action == 'list':
        for user in Users.users.values():
            print_user(user)
    elif args.action == 'del':
        if args.username is None:
            print('Для удаления необходимо передать имя пользователя.')
            exit(-1)
        Users.delete(args.username)
        print('Удален пользователь ', args.username)
    elif args.action == 'add':
        if (args.username is None) or (args.email is None) or (args.passw is None):
            print('Для проверки необходимо передать имя пользователя, адрес электронной почты, пароль и опционально флаг админа.')
            exit(-1)
        Users.add(args.username, args.email, args.passw, admin=args.is_adm)
        print('Добавлен пользователь', args.username)
    elif args.action == 'mod':
        if args.username is None:
            print(
                'Для обновления необходимо передать имя пользователя и изменяемый параметр.')
            exit(-1)
        user = Users.get(args.username)
        if user is None:
            print('Пользователь не найден.')
            exit(-1)
        if not (args.email is None):
            user.email = args.email
        if not (args.passw is None):
            user.set_password(args.passw)
        if not (args.is_adm is None):
            user.adm = True
            if args.is_adm:
                print('Пользователь будет назначен администратором.')
        Users.storeUser(user.id, user)
        print('Пользователь обновлен.')
