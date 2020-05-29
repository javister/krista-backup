# -*- encoding: utf-8 -*-


def _single_action_str(self):
    return '/'.join(list(iter(self)))


def _multi_action_str(_):
    cmd_actions = [
        str(arg) for arg in [
            RUN_OPT_NAME,
            STOP_OPT_NAME,
            ENABLE_OPTS_NAME,
            ENABLE_OPTS_NAME,
        ]
    ]
    return ', '.join(cmd_actions)


frozenset_single_action_opts = type(
    'frozenset_argv_action_opts',
    (frozenset,),
    {'__str__': _single_action_str},
)

frozenset_multiple_action_opts = type(
    'frozenset_argv_action_opts',
    (frozenset,),
    {'__str__': _multi_action_str},
)


RUN_OPT_NAME = 'run'

START_OPT_NAME = 'start'
STOP_OPT_NAME = 'stop'

ENABLE_OPT_NAME = 'en'
ENABLE_OPT_NAME_ALIAS = 'enable'

ENABLE_OPTS_NAME = frozenset_single_action_opts(
    {ENABLE_OPT_NAME, ENABLE_OPT_NAME_ALIAS},
)

DISABLE_OPT_NAME = 'dis'
DISABLE_OPT_NAME_ALIAS = 'disable'
DISABLE_OPTS_NAME = frozenset_single_action_opts(
    {DISABLE_OPT_NAME, DISABLE_OPT_NAME_ALIAS},
)

ARGS_ACTION_OPTS = frozenset_multiple_action_opts(
    {RUN_OPT_NAME} | {STOP_OPT_NAME} | ENABLE_OPTS_NAME | DISABLE_OPTS_NAME,
)

ALL = 'all'
