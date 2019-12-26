# -*- coding: UTF-8 -*-
import os
import re
import subprocess
import logging
from threading import Thread
from runner.Action import Action


class PgDump(Action):
    """
        Выполняется pg_dump с некоторым набором парамтеров.
        Список баз, для которых нужно делать бекап формируется следующим образом:
        - с сервера по указанным пользователь вычитывается список баз.
        - из списка вычитаются имена, которые подходят под критерии параметра exclusions (список регулярных выражений)
        - для каждой базы создается 1 файл бекапа, имя определяется как basename-имя базы-датавремя.extension
    """

    # dest_path              # наследуется от Аction, каталог, куда складываются бекапы
    # basename               # основа для имени файла, наследуется от Action
    """
     mode - режим работы, если all - то бекапяться все базы, если режим
            single, то бекапяться базы из списка databases
    """
    databases = []
    mode = "all"
    host = ""  # параметры подключения к СУБД
    port = 5432
    user = ""
    password = ""
    format = "custom"  # формат бекапа

    # исключения, которые не надо бекапить
    exclusions = ["postgres.*", "template.*"]
    extension = "pg_dump"  # расширение для файла бекапа
    command_path = "pg_dump"  # путь к команде pg_dump
    opts = ""  # опции запуска pg_dump, могут переопределяться в настройках

    pgdump_log_debug = False

    excl_re = []

    debug_patterns = [
        "reading .*",
        "last built-in .*",
        "identifying .*",
        "finding .*",
        "flagging. *",
        "saving .*",
        "dumping .*",
    ]

    def __init__(self, name):
        Action.__init__(self, name)

    def backupDatabase(self, database):
        if not os.path.exists(self.dest_path):
            os.makedirs(self.dest_path)
        filename = self.makeFilename(database)
        filepath = os.path.join(self.dest_path, filename)
        if self.format.strip().lower() == "directory" and not os.path.exists(filepath):
            os.makedirs(filepath)

        cmdline = " ".join(
            [
                self.command_path,
                self.opts,
                "-d",
                database,
                " ".join(["-h", self.host]) if self.host and self.user else "",
                " ".join(["-p", str(self.port)]) if self.port else "",
                " ".join(["-U", self.user]) if self.user else "",
                "=".join(["--format", self.format]),
            ]
        )
        # запуск команды под postgres и перенаправление потока на требуемый файл
        cmdline = "su postgres -c ' {} ' > {}".format(cmdline, filepath)

        self.logger.debug(u"Выполнение коменды %s" % cmdline)
        try:
            cmd = subprocess.Popen(
                cmdline,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                shell=True
            )

            stdo = Thread(
                target=self.stream_watcher,
                name="stdout-watcher",
                args=(cmd.stdout, False),
            )
            stdo.start()

            stde = Thread(
                target=self.stream_watcher_debug_filter,
                name="stderr-watcher",
                args=(
                    cmd.stderr, self.debug_patterns,
                    True, self.pgdump_log_debug
                ),
            )
            stde.start()

            cmd.wait()

            stdo.join()
            stde.join()

        except Exception as exc:
            self.logger.error('Ошибка при выполнении: %s', exc)
            return False
        self.logger.info("Архивирована база %s" % database)
        return True

    def isExclusion(self, dbname):
        for ex in self.excl_re:
            if re.match(ex, dbname):
                return True
        return False

    # Возвращает список баз данных postgresql
    # Требует наличия переменной PGPASSWORD в окружении
    @staticmethod
    def get_database_list(user, host, port):
        database_list = subprocess.Popen(
            "echo \"select datname from pg_database\" | su postgres -c 'psql {} -t -d postgres'".format(
                " ".join(
                    [
                        " ".join(["-U", user]) if user else "",
                        " ".join(["-h", host]) if host and user else "",
                        " ".join(["-p", str(port)]) if port else "",
                    ]
                )
            ),
            stdout=subprocess.PIPE,
            universal_newlines=True,
            shell=True,
        ).stdout.readlines()
        return database_list

    def start(self):
        failed = False
        for e in self.exclusions:
            try:
                if e and len(e.strip()):
                    self.excl_re.append(re.compile(e))
                    self.logger.info(u"Добавлено исключение (re): %s" % e)
            except:
                self.logger.warning(
                    u"Ошибка в регулярном выражении %s в excludes." % e)

        if self.user and self.password:
            os.putenv("PGPASSWORD", self.password)

        database_list = list()

        if self.mode == "all":
            database_list = PgDump.get_database_list(
                self.user, self.host, self.port)
        elif self.mode == "single":
            database_list = self.databases

        for dbname in database_list:
            db = dbname.strip()
            if db and len(db):
                if self.isExclusion(db):
                    self.logger.debug("- %s" % db)
                    continue
                else:
                    self.logger.debug("+ %s" % db)
                    res = self.backupDatabase(db)
                    failed = not res and failed

        if failed:
            return self.continue_on_error

        return True
