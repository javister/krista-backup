.. _cleaner:

Cleaner
=======

Выполняет ротацию бэкапов. 

Для ротации нужно указать ``source`` и настроить частоту ротации.

В качестве ``source`` может быть указано действие типа ``tar``, ``zip``, ``pgdump`` и ``move_bkp_period``.

Параметры:
~~~~~~~~~~

.. csv-table:: 
   :widths: 15, 30, 20
   :header: "название", "описание", "значение"

   "max_files", "Максимальное количество файлов.", "целочисленное"
   "days", "Максимальный возраст бэкапа.", "целочисленное, в днях"
   "dry", "Не удалять файлы при обработке (dryrun).", "False (стандартное значение)"


Пример:
~~~~~~~

.. code-block:: yaml

  cleaner_tarjob_0level_etc:
    descr: очистка каталога от файлов в зависимости от их количества
    max_files: 3
    days: 5
    source: tarjob_0level_etc
    type: cleaner

  tarjob_0level_etc:
    basename: etc
    check_level_list_only: 'False'
    compression: 3
    descr: бэкап файлов /etc 0-го уровня
    dest_path: /backup/app
    level: 0
    level_folders: 0,1,2
    src_path: /etc
    type: tar
    use_re_in_patterns: false

  clean_move_bkp_period:
    source: copy_backup_palnning_db_reglament
    type: cleaner

  copy_backup_palnning_db_reglament:
    descr: копирование бэкапов БД необходимые каталоги
    action_list:
        - 'make_full'
    periods:
        daily:
            path: daily
            cron: '00 21  * * *'
            max_files: 2
        weekly:
            path: weekly
            cron: '* *  * * *'
            max_files: 1
    src_path: /backup/0
    dest_path: /backup/vault/
    type: move_bkp_period

Примечание:
~~~~~~~~~~~

Для удаление файлов, которые не являются результатами действий,
можно использовать :ref:`command <command>` и :ref:`script <script>`.