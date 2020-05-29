import os
from abc import ABCMeta, abstractmethod


class NameGenerationInterface(metaclass=ABCMeta):

    def generate_filepath(self, *args, **kwargs):
        """Генерирует путь к выходному файлу."""
        dirname = self.generate_dirname(*args, **kwargs)
        filename = self.generate_filename(*args, **kwargs)
        return os.path.join(dirname, filename)

    def generate_hash_filepath(self, *args, **kwargs):
        """Генерирует путь к выходному файлу с хэш-суммой."""
        dirname = self.generate_dirname(*args, **kwargs)
        hash_filename = self.generate_hash_filename(*args, **kwargs)
        return os.path.join(dirname, hash_filename)

    def generate_dirname(self, *args, **kwargs):
        """Возвращает имя для выходной директории."""
        return self.dest_path

    @abstractmethod
    def generate_filename(self, *args, **kwargs):
        """Возвращает имя для выходного файла."""
        raise NotImplementedError('Should have implemented this')

    @abstractmethod
    def generate_hash_filename(self, *args, **kwargs):
        """Возвращает имя для выходного файла с хэш-суммой."""
        raise NotImplementedError('Should have implemented this')

    @abstractmethod
    def get_patterns(self, *args, **kwargs):
        """Возвращает паттерны создаваемых действием файлов."""
        raise NotImplementedError('Should have implemented this')
