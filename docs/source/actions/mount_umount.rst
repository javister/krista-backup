.. _mount_umount:

.. _mount:
.. _umount:

Mount и Umount
==============

Обёрка над ``mount`` и ``umount``.

Параметры:
~~~~~~~~~~

Mount
-----
.. csv-table::
   :widths: 15, 30, 20
   :header: "название", "описание", "значение"

   "mnt_dev", "Монтируемое устройство.", ""
   "mnt_point", "Точка монтирования.", ""
   "fs_type", "Тип подключаемой файловой системы.", ""
   "flags", "Параметры запуска.", ""
   "dry", "Не выполнять mount (dryrun).", "false (стандартное значение)."

Umount
------

.. csv-table::
   :widths: 15, 30, 20
   :header: "название", "описание", "значение"

   "mnt_point", "Точка монтирования.", ""
   "flags", "Параметры запуска.", ""
   "dry", "Не выполнять umount (dryrun).", "false (стандартное значение)."

Пример:
~~~~~~~

.. code-block:: yaml

  mount_volume:
    descr: подключить внешний диск
    mnt_dev: 10.0.10.2:/backup
    mnt_point: /backup_mount
    fs_type: nfs
    flags: -o credentials="/path/to/creds/.winpwd",sec=ntlm
    type: mount

  umount_volume:
    descr: отключить внешний диск
    mnt_point: /backup_mount
    type: umount