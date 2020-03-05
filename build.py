#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import shutil
import sys
import zipapp


PATTERNS_STARTS_WITH = [
    'common',
    'lib',
    'core',
    'Krista',
    'web',
    '_version'
]

FILES_SHOULD_BE_OUTSIDE = (
    'requirements.system',
    'requirements.txt',
    'UsersUtils.py',
)

DIRECTORIES_SHOULD_BE_OUTSIDE = (
    'web/webapp/templates',
    'web/webapp/static',
)


def src_filter(path):
    """Фильтрует временные файлы."""
    path = str(path)
    if all(not path.startswith(pattern) for pattern in PATTERNS_STARTS_WITH):
        return False
    return True


def generate_manual_steps():
    steps = [
        'To make a less memory-efficient build you can run:\n',
        'mkdir -p out',
        'python3 -m zipapp {source} -o out/KristaBackup -m "KristaBackup:main" -p "/usr/bin/env python3"\n'.format(
            source=source_path,
        )]

    for required_item in FILES_SHOULD_BE_OUTSIDE:
        steps.append('cp KristaBackup/{0} out/'.format(required_item))

    for required_item in DIRECTORIES_SHOULD_BE_OUTSIDE:
        steps.append(
            'cp -r KristaBackup/{0} out/webapp/'.format(required_item))
    return '\n'.join(steps)


if __name__ == '__main__':
    source_path = os.path.join(os.getcwd(), 'KristaBackup')
    if sys.version_info < (3, 7):
        print(
            'To use build.py the running python version should be >= 3.7 ',
            '(current: {0})'.format(
                '.'.join(map(str, sys.version_info[:3])),
            ),
            sep='',
        )
        print(generate_manual_steps())
    else:
        if not os.path.exists('out'):
            os.mkdir('out')
        zipapp.create_archive(
            source=source_path,
            target='out/KristaBackup',
            interpreter='/usr/bin/env python3',
            main='KristaBackup:main',
            filter=src_filter,
            compressed=True,
        )
        for required_item in FILES_SHOULD_BE_OUTSIDE:
            shutil.copy(os.path.join(source_path, required_item), 'out/')

        for required_item in DIRECTORIES_SHOULD_BE_OUTSIDE:
            dest_path = os.path.join(
                'out/',
                required_item,
            )
            if os.path.exists(dest_path):
                shutil.rmtree(dest_path)
            shutil.copytree(
                os.path.join(source_path, required_item),
                dest_path,
            )
        print('The build was created successfully.')
