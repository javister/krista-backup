.. _usage:


Использование
=============

.. _run_task:

Запуск заданий
-------------------------

Для запуска заданий вручную:

.. code:: bash

  python3 KristaBackup.py run task_name

Для логирования выполнения в терминал существует флаг ``-v/--verbose``:

.. code:: bash

  python3 KristaBackup.py run task_name --verbose

Список доступных опций можно увидеть
выполнив:

.. code:: bash

  python3 KristaBackup.py --help

.. _run_action:

Запуск действий
---------------

В приложении доступен запуск отдельных действий:

.. code:: bash

  python3 KristaBackup.py run action_name

Действия поддерживают флаги заданий и флаг ``--dry``.

При запуске с данным флагом действия будут запущены в
тестовом режиме:

.. code:: bash

  python3 KristaBackup.py run action_name --dry --verbose

Конкретные изменения в тестовом выполнении можно прочитать в описании
соответствующего действия.

В отличие от заданий, действия нельзя добавить в ``crontab`` и для
их полноценного использования требуется наличие ``naming`` в ``config.yaml``.

Подробнее о тестовом режиме в разделе :ref:`Действия <actions_index>`.

Подробнее о ``naming`` в разделе :ref:`Конфигурация <configuration>`.


.. _crontab_task:

Работа с crontab
----------------

Выполнение заданий можно автоматизировать добавлением в ``crontab``.
Для этого у них должен быть указан атрибут ``cron``, содержащий
время в формате ``cron``.

.. _crontab_add:

Добавление заданий в crontab
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

  python3 KristaBackup.py en task_name
  python3 KristaBackup.py enable task_name

.. _crontab_del:

Удаление задания из crontab
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

  python3 KristaBackup.py dis task_name
  python3 KristaBackup.py disable task_name

Также, все задания (которые указаны в ``config.yaml``) можно одновременно
добавить в ``crontab`` или удалить из него используя ключевое слово ``all``.

cron-расписания с заданиями хранятся в ``crontab`` пользователя,
который указан в конфигурации (``root`` по умолчанию).

.. _run_web:

Запуск веб-api или веб-приложения
---------------------------------

В приложение также встроен веб-модуль. С его помощью
можно просмотривать файлы логов и состояние триггер-файла,
если он используется.

Пример работы с веб-приложением:

.. code:: bash

  python3 KristaBackup.py web start
  python3 KristaBackup.py web stop  # Или Ctrl+C

Для запуска веб-api (без интерфейса) нужно выполнить следующую команду:

.. code:: bash

  python3 KristaBackup.py web --webapi start

По умолчанию приложение запускается на http://127.0.0.1:5555.
Хост и порт можно поменять в config.yaml:

.. code:: yaml

  web:
    host: '0.0.0.0'
    port: 5555


Данную информацию можно получить командой ``python3 KristaBackup.py --help``.

.. _user_utils:

Управления пользователями веб-приложения
----------------------------------------

В интерфейсе web модуля существует система пользователей. Пользователи
с правами администратора могут редактировать права других пользователей
и управлять заданиями.

Управлять списком пользователей можно также из консольного интерфейса.

.. code:: bash

  $ python3 KristaBackup.py web users list --help
  usage: KristaBackup.py web users [-h] <действие> ...

  positional arguments:
    <действие>
      list      список пользователей
      add       добавить пользователя
      upd       обновить пользователя
      rm        удалить пользователя

Пример добавления нового пользователя:

.. code:: bash

  $ python3 KristaBackup.py web users add new_user new_user@their.mail pAs$w0rd --admin
  Добавлен пользователь new_user

  $ python3 KristaBackup.py web users add --help
  usage: KristaBackup.py web users add [-h] [--plain | --admin]
                                      user email password

  positional arguments:
    user        имя пользователя
    email       почтовый адрес
    password    пароль

  optional arguments:
    -h, --help  show this help message and exit
    --plain     назначить стандартные права (default)
    --admin     назначить права администратора