# -*- coding: UTF-8 -*-
import fnmatch
import tarfile
import re
import os
import datetime
import time
import logging

from .action import Action


class TarArchiver(Action):
    """Обертка для tar."""

    # src_path               # наследуется от Аction, каталог, откуда копировать
    # dest_path              # наследуется от Аction, каталог, куда копировать

    compression = 5  # уровень сжатия
    exclusions = []  # Список файлов-исключений
    # Если включить этот параметр, то паттерны будут рассматриваться как regexp,
    use_re_in_exclusions = False
    # иначе как паттерны sh
    level = 0  # уровень бекапа
    # в параметре определяется список папок для каждого уровня по 1 папке
    level_folders = []
    list_extension = "list"  # расширение для файла-списка архива
    extension = "tar.gz"  # расширение архива по-умолчанию
    # возможные: gz, bz2

    use_absolute_path = False
    """ Определяет какие пути следует использовать.
    По умолчанию используются относительные пути.
    """
    overwrite = False  # перезаписывать одноименные файлы,
    # или прерывать процесс при наличии файла-получаетеля

    check_level_list_only = True
    # если параметр установлен, то при инкрементельном бекапе проверяется только наличие
    # файла-списка, иначе проверяется наличие самого файла исходного бекапа.
    # это параметр имеет смысл использовать только если мы жестко ограничены местом
    # в каталоге dest_path и файлы-бекапы регулярно копируются куда-то в другое место,
    #  причем гарантируется, что полная копия сущетсвует где-то, если в папке dest_path
    # лежит list-файл от нее.

    log_tar_files = False  # регулирует логирование добавления файлов в архив

    list_file = None
    inc_list = {}
    excl_re = []

    def __init__(self, name):
        Action.__init__(self, name)

    def findSourceListFile(self):
        if self.level == 0:
            return None

        files = []
        needed_level = self.level - 1
        needed_filename_pattern = '{0}*{1}.{2}'.format(
            self.basename,
            str(needed_level),
            self.list_extension,
        )

        file_path = os.path.join(self.dest_path,
                                 self.level_folders[needed_level])
        if not os.path.exists(file_path):
            return None

        for file in os.listdir(file_path):
            fullpath = os.path.join(file_path, file)
            if fnmatch.fnmatch(
                    file, needed_filename_pattern) and os.path.isfile(fullpath):
                files.append(file)

        prev_list_file = None

        if len(files) == 1:
            prev_list_file = os.path.join(self.dest_path,
                                          self.level_folders[needed_level],
                                          files[0])
        elif len(files) > 1:
            sorted_files = sorted(files, reverse=True)
            prev_list_file = os.path.join(self.dest_path,
                                          self.level_folders[needed_level],
                                          sorted_files[0])

        self.logger.debug(u"Файл списка предыдущего архива %s" %
                          prev_list_file)
        return prev_list_file

    def add_files_to_tar(self, src, tar):

        def add_file(tar, filepath):
            if self.use_absolute_path:
                filepath = os.path.join(self.src_path, filepath[2:])
            tar.add(filepath)
            # добавление записи о файле в snapshot list
            self.list_file.write(line)
            self.list_file.write("\n")

        def exclude(path, mtime, fsize):
            if self.use_re_in_exclusions:
                for er in self.excl_re:
                    if er.search(path):
                        files_logger.debug("re excluded %s" % path)
                        return True
            else:
                for p in self.exclusions:
                    if fnmatch.fnmatch(path, p):
                        files_logger.debug("sh excluded  %s" % path)
                        return True

            files_logger.debug("+ %s,%s,%s", mtime, fsize, path)

            if (path in self.inc_list.keys() and
                    self.inc_list[path][0] == str(mtime) and
                    self.inc_list[path][1] == str(fsize)):
                files_logger.debug("= %s,%s,%s", mtime, fsize, path)
                return True

            return False

        files_logger = logging.getLogger("{}.tar_files".format(
            self.logger.name))
        files_logger.propagate = self.log_tar_files

        for (dirpath, _, filenames) in os.walk(src):
            if self.use_absolute_path:
                dirpath_tarinfo = os.path.join(self.src_path, dirpath[2:])
            else:
                dirpath_tarinfo = dirpath
            try:
                dir = tar.gettarinfo(name=dirpath_tarinfo)
                mtime = os.path.getmtime(dirpath)
                fsize = os.path.getsize(dirpath)
            except Exception as e:
                self.logger.warning(
                    'Не удалось прочитать свойства каталога %s, ошибка %s',
                    dirpath, e,
                )
                continue

            if not exclude(dirpath, mtime, fsize):
                try:
                    tar.addfile(dir)
                except FileNotFoundError:
                    self.logger.debug(
                        'Следующая директория не найдена/broken link: %s',
                        dirpath,
                    )
                except Exception as e:
                    # если во время добавления произошла ошибка, то
                    # повторить добавление файла через 5 секунд
                    time.sleep(5)
                    self.logger.warning(
                        'Не удалось добавить, повторная попытка добавить каталог: %s, ошибка %s',
                        dirpath, e,
                    )
                    try:
                        tar.addfile(dir)
                    except Exception as e:
                        self.logger.warning(
                            'Не удалось добавить каталог %s, ошибка %s',
                            dirpath, e,
                        )
                    continue

            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    mtime = os.path.getmtime(filepath)
                    fsize = os.path.getsize(filepath)
                except FileNotFoundError:
                    self.logger.debug(
                        'Следующий файл не найден/broken link: %s',
                        filepath,
                    )
                except Exception as e:
                    self.logger.warning(
                        'Не удалось прочитать свойства файла %s, ошибка %s',
                        filepath, e,
                    )
                    continue

                # используется в add_file
                line = "%s,%s,%s" % (mtime, fsize, filepath)
                if not exclude(filepath, mtime, fsize):
                    try:
                        add_file(tar, filepath)
                    except Exception as e:
                        # если во время добавления произошла ошибка, то
                        # повторить добавление файла через 5 секунд
                        time.sleep(5)
                        self.logger.warning(
                            'Не удалось добавить, повторная попытка добавить файл: %s, ошибка %s',
                            filepath, e,
                        )
                        try:
                            add_file(tar, filepath)
                        except Exception as e:
                            self.logger.warning(
                                'Не удалось добавить файл: %s', e,
                            )
                        continue

    def start(self):

        time = datetime.datetime.now()

        if len(self.level_folders) < (self.level + 1):
            self.logger.error(
                'Неверно сконфигурированы папки уровней бекапов!'
            )
            self.loggin.error(
                'Для уровня бекапа %s отсутствует папка - level_folders= %s',
                self.level,
                self.level_folders,
            )
            return self.continue_on_error

        # Проверяем каталоги
        if not os.path.exists(self.src_path):
            if os.path.isfile(self.src_path):
                self.logger.error(
                    'Отсутствует исходный файл %s', self.src_path
                )
            else:
                self.logger.error(
                    'Отсутствует исходная папка %s.', self.src_path
                )
            return self.continue_on_error

        if not os.path.exists(self.dest_path):
            os.makedirs(self.dest_path, 0o755)

        # Перевариваем исключения
        if not self.exclusions is None and len(self.exclusions):
            for e in self.exclusions:
                if self.use_re_in_exclusions:
                    try:
                        if e and len(e.strip()):
                            self.excl_re.append(re.compile(e))
                            self.logger.debug(u"Добавлено исключение (re): %s" %
                                              e)
                    except:
                        self.logger.warning(
                            u"Ошибка в регулярном выражении %s в excludes." % e)
                else:
                    self.logger.debug(u"Добавлено исключение (sh): %s" % e)

        # Компрессия
        if self.compression < 0:
            self.compression = 0
        elif self.compression > 9:
            self.compression = 9
        self.logger.info(u"Сжатие: %s" % self.compression)

        self.logger.info(u"Рабочий каталог: %s" % self.dest_path)

        # Определяемся с уровнем бекапа
        self.logger.info("level configured: %s" % str(self.level))

        # Для инкрементального бекапа делаем дополнительные проверки
        if self.level > 0:

            # ищем файл список и файл архива предыдущего уровня, если не находим - понижаем уровень архива,
            # пока не дойдем до полного
            src_list_file = self.findSourceListFile()
            while self.level > 0 and src_list_file is None:
                self.level -= 1
                src_list_file = self.findSourceListFile()

            if src_list_file is None:
                self.logger.warn(
                    u"Отсутствует список полного архива, будет создана полная копия"
                )
                self.level = 0
            elif not os.path.exists(src_list_file):
                self.logger.warn(
                    u"Отсутствует файл списка полного архива %s, будет создана полная копия"
                    % src_list_file)
                self.level = 0
            else:
                with open(src_list_file, "r") as f:
                    src_name = f.readline().strip()
                    if not self.check_level_list_only and not os.path.exists(
                            src_name):
                        self.logger.warn(
                            u"Отсутствует указанный в листинге файл-источник инкрементального архива %s,"
                            + u" будет создана полная копия" % src_name)
                    else:
                        # Читаем лист
                        linenum = 0
                        for l in f:
                            linenum += 1
                            line = l.strip().split(",")
                            if len(line) < 3:
                                self.logger.warn(
                                    u"Ошибка в строке %s файла-списка %s" %
                                    (str(linenum), l))
                                continue
                            mtime = line[0].strip()
                            size = line[1].strip()
                            file = line[2].strip()
                            self.inc_list[file] = (mtime, size)

        # Создаем архив
        full_filename = self.makeFilename()

        if os.path.exists(full_filename):
            if self.overwrite:
                os.remove(full_filename)
            else:
                self.logger.error(
                    'Получатель уже существует: %s, архив не будет создан',
                    full_filename,
                )
                return self.continue_on_error

        src = self.src_path
        if os.path.isdir(self.src_path):
            os.chdir(self.src_path)
            src = "."

        listfilename = self.makeFilename(ext=self.list_extension)
        if not os.path.exists(os.path.dirname(listfilename)):
            os.makedirs(os.path.dirname(listfilename))

        try:
            with open(listfilename, "a") as self.list_file:
                self.list_file.write(full_filename)
                self.list_file.write("\n")
                with tarfile.open(
                        full_filename,
                        "w:gz",
                        compresslevel=self.compression,
                ) as tar:
                    self.logger.info(u"Исходные данные архива: %s", src)
                    self.add_files_to_tar(src, tar)

        except Exception as exc:
            self.logger('Ошибка при выполнении архивации: %s', exc)
            return self.continue_on_error

        self.logger.info('Архив создан: % s, время обработки: % s',
                         full_filename, str(datetime.datetime.now() - time))

        return True
