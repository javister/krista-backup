from .base_strategy import BaseStrategy


class ArchiverStrategy(BaseStrategy):

    @classmethod
    def clean(cls, cleaner, action, max_files=None, days=None, **kwargs):
        patterns = cls.parse_patterns(cleaner, action.get_patterns())

        files = cls.collect_files(
            cleaner=cleaner,
            path=kwargs.get('path', action.generate_dirname()),
            patterns=patterns,
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
