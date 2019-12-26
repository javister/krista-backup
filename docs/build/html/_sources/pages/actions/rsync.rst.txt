.. _rsync:

Rsync
=====

Оболочка над ``rsync``. Может использоваться для перемещения
бэкапов с сервера приложения на сервер с бэкапами или наоборот.


.. csv-table:: 
   :widths: 15, 30, 20
   :escape: '
   :header: "название", "описание", "значение"

   "exclusions", "файлы, которые стоит игнорировать", ""
   "opts", "параметры подключения", "-e '\" '\\"ssh -p 22'\\" 
   "other_opts", "параметры для конкретного расписания", "-ahv \\-\\-delete-after \\-\\-delete-excluded"
   "bwlimit", "максимальная скорость передачи", "если 0 и меньше - не ограничено"

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
