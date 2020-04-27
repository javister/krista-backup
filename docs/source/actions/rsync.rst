.. _rsync:

Rsync
=====

Оболочка над ``rsync``. Может использоваться для перемещения
бэкапов с сервера приложения на сервер с бэкапами или наоборот.


.. csv-table:: 
   :widths: 15, 30, 20
   :header: "название", "описание", "значение"

   "bwlimit", "Максимальная скорость передачи, килобайт/с.", "0 (стандартное значение, не ограничено)"
   "exclusions", "Файлы, которые стоит игнорировать.", "[ ]"
   "opts", "Параметры подключения.", '-e "ssh -p 22"' 
   "other_opts", "Дополнительны параметры для действия.", '-ahv --delete-after --delete-excluded'
   "dry", "Не выполнять синхронизацию (dryrun). Во время выполнения будет выполнен запрос на src_path для получения списка файлов.", "false (стандартное значение)"
 
Пример:
~~~~~~~

.. code-block:: yaml

  rsyncjob:
    descr: синхронизация файлов
    exclusions: tmp, *.dll, *.exe
    opts: '-e "ssh -p 22"'
    other_opts: '-v -h -a --delete-after'
    type: rsync
    continue_on_error: true

  rsyncjob-remoteserver-weekly:
    descr: еженедельная копия бэкапа приложения
    source: rsyncjob
    src_path: remoteserver:/backup/0/
    dest_path: /backup/0/remoteserver/
