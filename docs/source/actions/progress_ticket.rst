.. _inprogressticket:

InProgressTicket
================

Базовое действие для работы с тикетами. Абстрактный

.. csv-table::
   :widths: 15, 30, 20
   :escape: '
   :header: "название", "описание", "значение"

   "ticket_filename", "имя тикет файла", "backup_in_progress (стандартное значение)"


.. _set_in_progress_ticket:

SetInProgressTicket
~~~~~~~~~~~~~~~~~~~
Действие для создания тикет файлов.

Параметры:
~~~~~~~~~~

.. csv-table::
   :widths: 15, 30, 20
   :escape: '
   :header: "название", "описание", "значение"

   "src_path", "путь к директории, в которой нужно создать тикет", ""

Пример:
~~~~~~~

.. code-block:: yaml

    set_backup_in_progess:
        ticket_filename: backup_in_progress
        src_path: /backup/
        type: set_in_progress_ticket

Примечание
~~~~~~~~~~
В ситуации, когда до выполнения тикет файл уже существует, создаётся
предупреждение.

.. _unset_in_progress_ticket:

UnsetInProgressTicket
~~~~~~~~~~~~~~~~~~~~~

Действие для удаления тикет файлов.

Параметры:
~~~~~~~~~~

.. csv-table::
   :widths: 15, 30, 20
   :escape: '
   :header: "название", "описание", "значение"

   "src_path", "путь к директории, в которой нужно удалить тикет", ""

Пример:
~~~~~~~

.. code-block:: yaml

    unset_backup_in_progess:
        ticket_filename: backup_in_progress
        src_path: /backup/
        type: unset_in_progress_ticket
        desc: удаляет тикет

Примечание
~~~~~~~~~~
Ситуация, когда во время выполнения тикет файла не существует, считается
обычной (не приводит к ошибке).

.. _check_in_progress_ticket:

CheckInProgressTicket
~~~~~~~~~~~~~~~~~~~~~

Действие для проверки существования тикет файла.

Параметры:
~~~~~~~~~~

.. csv-table::
   :widths: 15, 30, 20
   :escape: '
   :header: "название", "описание", "значение"

   "src_path", "путь к директории, в которой находится тикет", ""
   "ssh_servername", "имя удалённого сервера", ""
   "rsync_opts", "опции для подключения через rsync", ""
   "wait_time", "время ожидания в секундах", "10 (стандартное значение)"
   "wait_cycle_number", "количество циклов ожидания", "12 (стандартное значение)"

Пример:
~~~~~~~

.. code-block:: yaml

    check_backup_in_progess:
        ticket_filename: backup_in_progress
        src_path: /backup/
        ssh_servername: servername
        rsync_opts: '-e "ssh -p 22"'
        wait_time: 10
        wait_cycle_number: 12
        type: check_in_progress_ticket
        desc: проверяет наличие тикета
