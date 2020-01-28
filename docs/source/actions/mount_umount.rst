.. _mount_umount:

.. _mount:
.. _umount:

Mount/Umount
============

Обёрка над ``mount`` и ``umount``.

Параметры:
~~~~~~~~~~

Mount
-----
.. csv-table::
   :widths: 15, 30, 20
   :header: "название", "описание", "значение"

   "mnt_dev", "монтироемое устройство", ""
   "mnt_point", "точка монтирования", ""
   "fs_type", "тип подключаемой файловой системы", ""
   "cred_file", "файл с данными для подключения", ""
   "flags", "флаги для выполнения", ""

Umount
------

.. csv-table::
   :widths: 15, 30, 20
   :header: "название", "описание", "значение"

   "mnt_point", "точка монтирования, которую требуется отмонтировать", ""
   "flags", "флаги для выполнения", ""

Пример:
~~~~~~~

.. code-block:: yaml

  mount_volume:
    descr: подключить внешний диск
    mnt_dev: 10.0.10.2:/backup
    mnt_point: /backup_mount
    fs_type: nfs
    flags: -v
    type: mount

  umount_volume:
    descr: отключить внешний диск
    mnt_point: /backup_mount
    type: umount