import os


class WalkAppierMixin:

    def walk_apply(self, src, apply, recursive=True, apply_dirs=False):
        """Метод проходит по файлам и применяет к ним apply.

        На время выполнения меняет текущую директорию на src. По умолчанию
        проход рекурсивный.

        Args:
            src: Строка, исходная директория.
            apply: Функция, принимает файл/строку.
            recursive: Логическое значение, задаёт рекурсивный обход.
            apply_dirs: Логическое значение, обработка и директории.

        """
        if not os.path.isdir(src):
            raise AttributeError(
                'директория src не существует: {0}'.format(src),
            )

        current_dir = os.getcwd()
        os.chdir(src)

        walker = (
            (dirpath[2:], filenames)
            for dirpath, _, filenames in os.walk('.')
        )
        if not recursive:
            walker = [next(walker)]
        for (dirpath, filenames) in walker:
            if apply_dirs and dirpath.strip():
                apply(dirpath)
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                apply(filepath)
        os.chdir(current_dir)
