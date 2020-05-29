from .base_strategy import BaseStrategy


class PgDumpStrategy(BaseStrategy):

    @classmethod
    def clean(cls, cleaner, action, days, max_files, **kwargs):
        patterns = cls.parse_patterns(cleaner, action.get_patterns())
        exclusions = cls.parse_exclusions(cleaner, action, action.exclusions)

        files = cls.collect_files(
            cleaner=cleaner,
            path=kwargs.get('path', action.generate_dirname()),
            patterns=patterns,
            exclusions=exclusions,
        )
        files = cls.filter_files(
            cleaner=cleaner,
            files=files,
            action=action,
            max_files=max_files,
            days=days,
        )
        cls.remove_files(cleaner, files)
        return True

    @classmethod
    def parse_exclusions(cls, cleaner, action, exclusions):
        exclusions = exclusions or []
        result_exclusions = []

        for exclusion in exclusions:
            exclusion_ = cleaner.prepare_pattern(exclusion)
            if not exclusion_:
                continue
            exclusion_ = action.scheme.get_pgdump_pattern(
                action,
                dbname=exclusion_,
            )
            exclusion_ = cls.parse_pattern(cleaner, exclusion_)
            if exclusion_:
                result_exclusions.append(exclusion_)

        cleaner.logger.debug(
            'Добавлены группы исключений: %s',
            [exc.pattern for exc in result_exclusions],
        )
        return result_exclusions
