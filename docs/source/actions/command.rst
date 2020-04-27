.. _command_script:

Command и Script
================

.. _command:

Command
-------

Выполняет команду в ``cmd``.

Имеет атрибут ``src_path`` - путь к исходной директории.

Пример:
~~~~~~~

.. code-block:: yaml

  test_command:
    type: command
    src_path: /home
    cmd: ls -l



.. _script:

Script
------

Выполняет список команд из ``cmds``.

Имеет атрибут ``src_path`` - путь к исходной директории.

Пример:
~~~~~~~

.. code-block:: yaml

  test_script:
    type: script
    src_path: /opt
    cmds:
     - ls -l
     - echo 'test'