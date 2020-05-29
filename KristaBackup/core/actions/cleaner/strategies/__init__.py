from ...archiver import Archiver
from ...movebkpperiod import MoveBkpPeriod
from ...pgdump import PgDump


def match_strategy(action):
    from .archiver_strategy import ArchiverStrategy
    from .move_bkp_perod_strategy import MoveBkpPeriodStrategy
    from .pgdump_strategy import PgDumpStrategy

    if isinstance(action, PgDump):
        return PgDumpStrategy

    if isinstance(action, MoveBkpPeriod):
        return MoveBkpPeriodStrategy

    if isinstance(action, Archiver):
        return ArchiverStrategy

    raise ValueError('Для действия {0} отсутствует стратегия очистки'.format(action.__class__))
