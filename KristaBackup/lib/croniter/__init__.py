# -*- coding: utf-8 -*-
from __future__ import absolute_import
try:
    from .croniter import (
        croniter,
        CroniterBadDateError,  # noqa
        CroniterBadCronError,  # noqa
        CroniterNotAlphaError  # noqa
    )  # noqa
    croniter.__name__  # make flake8 happy
except ImportError:
    croniter = None  # make unittest in python3.5 happy
