#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import shutil
import sys
import zipapp


patterns = [
    'runner',
    'lib',
    'model',
    'web',
    'Krista',
]


def src_filter(path):
    """Фильтрует временные файлы."""
    path = str(path)
    if all(not path.startswith(pattern) for pattern in patterns):
        return False
    return True


if __name__ == '__main__':
    if sys.version_info < (3, 7):
        print(
            'To use build.py your python version should be >= 3.7 ',
            '(current: {0})\n'.format(
                '.'.join(map(str, sys.version_info[:3])),
            ),
            'To make a not memory-efficient build you can run:\n\n',
            'python3 -m zipapp {source} -o /tmp/KristaBackup'.format(
                source=os.getcwd(),
            ),
            ' -m "KristaBackup:main" -p "/usr/bin/env python3"\n\n',
            'mkdir -p out\n\n',
            'mv /tmp/KristaBackup out/ \n\n',
            'cp requirements.system out/',
            sep='',
        )
    else:
        if not os.path.exists('out'):
            os.mkdir('out')
        zipapp.create_archive(
            source=os.getcwd(),
            target='out/KristaBackup',
            interpreter='/usr/bin/env python3',
            main='KristaBackup:main',
            filter=src_filter,
            compressed=True,
        )
        shutil.copy('requirements.system', 'out/')
