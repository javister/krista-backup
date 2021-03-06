.. _configuration:

Конфигурация
============


Общая стуктура
--------------

Рядом с выполняемым файлом должен находится файл конфигураций ``config.yaml``.

Конфигурация состоит из следующих частей:

- ``naming``

 Содержит ``server_name``, ``region`` и ``project``. Они
 используются для выходных файлов и логов. Для полноценного запуска
 действий необходимо их заполнить.

 Для выполнения заданий поля ``region`` и ``project`` могут
 быть пропущены, если они явно указаны в описании заданий.

 Также поддерживает атрибут :ref:`naming_scheme <naming_schemes>`.

- ``cron``

 Содержит ``cron_user`` - имя пользователя, в чей ``crontab`` будет добавляться расписание.

- ``logging``

 Содержит ``logs_path`` - директорию для хранения логов.
 
 Также имеет вариативный параметр ``trigger_filepath``, который содержит
 путь к триггер-файлу. Если путь указан, то будет создан файл, который
 будет хранить состояние последнего бэкапа: 
 "SUCCESS", "WARNING" или "ERROR" (обновляется после выполнения, если последняя запись имела приоритет ниже или была
 сделана более 5 часов назад).

- ``web``

 Содержит ``host``, ``port`` и ``SECRET_KEY`` для конфигурации веб модуля.

- ``actions``

 Содержит список действий. Подробнее о действиях можно узнать :ref:`здесь <actions_index>`.

- ``schedule``

 Расписание -- список всех заданий; ниже подробно описана его структура.

Расписание
----------

Расписание (schedule) -- список всех заданий.

Терминология
~~~~~~~~~~~~

- Минимальная единица -- действие (action).
- Задание (task) содержит список действий, которые требуется выполнить.
- Все задания вместе явлются расписанием (schedule).

Пример
~~~~~~

.. code-block:: yaml

  schedule: # расписание
    full_dump: # задание
      actions: # действия в задании
        - some_action_1 # действие 1
        - some_action_2 # действие 2
      cron: 00 23 * * 1-6
      descr: описание задания

  actions: #  список всех действий
    some_action_1: #  конфигурация действия 1
      type: type1

    some_action_2: #  конфигурация действия 2
      type: type2

Примечание
~~~~~~~~~~

Существует атрибут ``allow_parallel``, который запрещает
запускать одновременно несколько заданий/действий. 

.. code-block:: yaml
  
  allow_parallel: false

  naming:
    ...

Он имеет стандартное значение ``true``.

Описание заданий
----------------

Как было выше упомянуто, задания указаны в расписании. Каждое
задание содержит следующие параметры:

- ``naming``

 содержит ``project`` и ``region``: если они не указаны, то будут
 использованы параметры из ``naming`` в корне конфигурации. Также
 поддерживает атрибут :ref:`naming_scheme <naming_schemes>`.

- ``actions``

 упорядоченный список действий; у действий могут быть
 параметры (подробнее в примечании)

- ``cron``

 время повторения задания в формате ``cron``

- ``all_fields_match``

 стандартное значение ``false``

 используется в редких случаях,
 когда требуется точное совпадение дня месяца И дня недели в ``crontab``
 (по умолчанию в ``crontab`` используется отношение ИЛИ)

Также, имя задания должно быть уникальным.

Примечание
~~~~~~~~~~

Атрибут ``actions`` может содержать не только имя действия, но
и ещё параметры его вызова. Для этого существует специальная запись
с квадратными скобками, которая показана в примере ниже.



.. _configuration_task_example:

Пример
~~~~~~

.. code-block:: yaml

  schedule:
    full_dump:
      naming:
          project: app
          region: 99
      actions:
          - cleaner_tarjob_0level_application
          - tarjob_0level_application
          - [some_unstable_action, --dry] # данное действие будет выполняться в тестовом режиме
      cron: '00 23 * * 1-6'
      descr: Бекап каталога /application 0-го уровня (полный)

Подробнее о тестовом режиме в разделе :ref:`Действия <actions_index>`.


Пример написания конфигурации
-----------------------------

Здесь будет рассмотрен пример файла конфигураций, который будет
содержать настройки для выполнения полного и разностного бэкапа каталога ``/etc``.

Ротация полного бэкапа будет выполняться раз в неделю, одновременно будут хранится
две копии; ротация разностного бэкапа будет выполняться ежедневно, одновременно
будут хранится 4 копии.

В корневом каталоге находится файл ``config.yaml``, содержащий конфигурацию
в формате ``yaml``.

Добавим в начало файла блок ``naming``:

.. code-block:: yaml

  naming:
    server_name: example_server # имя серверва
    project: server_backup # название проекта
    region: region_name # название региона


Этот блок используется для подстановки в результирующие файлы.
Далее добавим блок ``logging``:

.. code-block:: yaml

  logging:
    logs_path:
      /var/log/KristaBackup # директория, в которой
                            # будут храниться логи

Теперь опишем действия. Создадим блок ``actions`` и
добавим в него действие, которое будет выполнять полный бэкап:

.. code-block:: yaml

  actions:
    tarjob_0level_etc:
      basename: etc # уникальное имя, не должно быть началом другого basename
      src_path: /etc # исходная директория
      dest_path: /backup # результирующая директория
      level: 0 # уровень бэкапа
      level_folders: 0,1 # имена папок для уровней бэкапа
      descr: бэкап файлов /etc 0-го уровня # ёмкое описание
      type: tar # тип

Наследуем от ``tarjob_0level_etc`` новое действие, которое
будет выполнять разностный бэкап:

.. code-block:: yaml

  actions:
    tarjob_0level_etc:
    ...
      type: tar

    tarjob_1level_etc:
      source: tarjob_0level_etc   # указано родительское действие
      level: 1
      descr: бэкап файлов /etc 1-го уровня
      type: tar

Действие ``tarjob_1level_etc`` импортировало все параметры,
которые установлены в ``tarjob_0level_etc``,
но не установлены в нём самом.

Заметим, что в ``tarjob_1level_etc`` указан тип ``tar``, хотя его
можно и упустить, так как в таком случае он бы был заимствован из ``tarjob_0level_etc``.

По аналогии добавим действия для ротации:

.. code-block:: yaml

  actions:
    tarjob_0level_etc:
    ...
      type: tar

    tarjob_1level_etc:
      ...
      type: tar

  cleaner_tarjob_0level_etc:
      descr: очистка каталога от файлов в зависимости от их количества
      max_files: 2
      source: tarjob_0level_etc
      type: cleaner

    cleaner_tarjob_1level_etc:
      descr: очистка каталога от файлов в зависимости от их количества
      max_files: 4
      source: tarjob_1level_etc
      type: cleaner

Осталось собрать действия в задания. Добавим ``schedule`` после ``logging``,
а в него задание для выполнения полного бэкапа:

.. code-block:: yaml

  ...
  logging:
    logs_path: /var/log/KristaBackup

  schedule:
    full_dump:                        # имя задания
      actions:                        # список действий
        - tarjob_0level_etc           # действие для создания бэкапа
        - cleaner_tarjob_0level_etc   # действие для ротации копий
      cron: '00 23 * * 0'             # время, в которое требуется
                                      # выполнять задание
      descr: Бекап каталога 0-го уровня (полный)

  actions:
    tarjob_0level_etc:
  ...


По аналогии сделаем задания для выполнения разностного бэкапа:

.. code-block:: yaml

  ...
  logging:
    logs_path: /var/log/KristaBackup

  schedule:
    full_dump:                        # имя задания
    ...
      descr: Бекап каталога 0-го уровня (полный)

    diff_dump:
      actions:
        - tarjob_1level_etc
        - cleaner_tarjob_1level_etc
      cron: '00 23 * * 1-6'
      descr: Бекап каталога 0-го уровня (полный)


Конфигурация завершена. Финальный результат:

.. code-block:: yaml

  naming:
    server_name: example_server
    project: server_backup
    region: region_name

  logging:
    logs_path: /var/log/KristaBackup

  schedule:
    full_dump:
      actions:
        - tarjob_0level_etc
        - cleaner_tarjob_0level_etc
      cron: '00 23 * * 0'
      descr: Бекап каталога 0-го уровня (полный)

    diff_dump:
      actions:
        - tarjob_1level_etc
        - cleaner_tarjob_1level_etc
      cron: '00 23 * * 1-6'
      descr: Бекап каталога 0-го уровня (полный)

  actions:
    tarjob_0level_etc:
      basename: etc
      src_path: /etc
      dest_path: /backup
      level: 0
      level_folders: 0,1
      descr: бэкап файлов /etc 0-го уровня
      type: tar

    tarjob_1level_etc:
      source: tarjob_0level_etc
      level: 1
      descr: бэкап файлов /etc 1-го уровня
      type: tar

    cleaner_tarjob_0level_etc:
      descr: очистка каталога от файлов в зависимости от их количества
      max_files: 2
      source: tarjob_0level_etc
      type: cleaner

    cleaner_tarjob_1level_etc:
      descr: очистка каталога от файлов в зависимости от их количества
      max_files: 4
      source: tarjob_1level_etc
      type: cleaner
