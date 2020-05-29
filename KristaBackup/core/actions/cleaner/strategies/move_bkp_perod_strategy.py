import os

from . import match_strategy
from .base_strategy import BaseStrategy


class MoveBkpPeriodStrategy(BaseStrategy):

    @classmethod
    def clean(cls, cleaner, action, **kwargs):
        """Выполнение очистки MoveBkpPeriod.

        Алгоритм:
        1. обработка периодов в цикле
            1.1 сбор файлов для данного периода
            1.2 удаление файлов периода

        """
        if not action.action_list or not action.periods:
            return True
        action_list = action.action_list

        for period_name in action.periods:
            period_path = os.path.join(
                action.dest_path,
                action.periods[period_name].get('path', period_name),
            )
            max_files = action.periods[period_name].get('max_files')
            days = action.periods[period_name].get('days')
            for subaction in action_list:
                strategy = match_strategy(subaction)
                strategy.clean(
                    cleaner=cleaner,
                    action=subaction,
                    path=period_path,
                    max_files=max_files,
                    days=days,
                )
        
        return True
