.. _pgdump:

PgDump
======


Оболочка над pgdump.

Параметры:
~~~~~~~~~~

.. csv-table:: 
   :widths: 15, 30, 20
   :header: "название", "описание", "значение"

   "exclusions", "базы, которые стоит игнорировать", ""
   "format", "формат бэкапа", "directory или custom (стандартное значение)"
   "host", "адрес/ip хоста", "\\'\\' (ip, стандартное значение)"
   "port", "порт базы", "5432 (порт, стандартное значение)"
   "user", "пользователь", ""
   "password", "пароль", ""
   "opts", "опции для pgdump", ""
   "extension", "расширение файла бэкапа", "pg_dump (стандартное значение"
   "command_path", "имя команды pgdump", "pg_dump (стандартное значение)"
   "mode", "режим, определяющий выбираемые базы", "all = бэкап всех баз, single = бэкап баз в databases"
   "databases", "имя баз, бэкап которых нужно выполнить", "[] (лист, работает если mode = \\'single\\')"

Пример:
~~~~~~~

.. code-block:: yaml

  pgdump:
    descr: бекап базы postgresql
    basename: pgdump
    databases: db_test_app
    dest_path: /backup/db/
    exclusions: postgres.*, template.*
    format: custom
    type: pgdump
    mode: 'all'
