# -*- encoding: utf-8 -*-


def single_action_str(self):
    return '/'.join(list(iter(self)))


def multi_action_str(_):
    cmd_actions = [
        str(arg) for arg in [
            RUN_OPTS,
            STOP_OPTS,
            ENABLE_OPTS,
            DISABLE_OPTS,
        ]
    ]
    return ', '.join(cmd_actions)


frozenset_single_action_opts = type(
    'frozenset_argv_action_opts',
    (frozenset,),
    {'__str__': single_action_str},
)

frozenset_multiple_action_opts = type(
    'frozenset_argv_action_opts',
    (frozenset,),
    {'__str__': multi_action_str},
)


RUN_OPTS = frozenset_single_action_opts({'run'})
STOP_OPTS = frozenset_single_action_opts({'stop'})

ENABLE_OPTS = frozenset_single_action_opts({'enable', 'en'})
DISABLE_OPTS = frozenset_single_action_opts({'disable', 'dis'})

ARGS_ACTION_OPTS = frozenset_multiple_action_opts(
    RUN_OPTS | STOP_OPTS | ENABLE_OPTS | DISABLE_OPTS,
)

ALL = 'all'
