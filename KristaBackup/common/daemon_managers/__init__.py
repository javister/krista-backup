# -*- encoding: utf-8 -*-

import os

try:
    CURRENT_USER = os.getlogin()
except OSError:
    CURRENT_USER = 'root'

from .crontab_manager import CrontabManager

crontab_manager = CrontabManager()
