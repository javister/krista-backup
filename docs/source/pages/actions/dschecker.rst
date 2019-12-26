.. _dschecker:

DataSpaceChecker
================

Выполняет команду ``df -h``. Используется для вывода информации о занятом дисковом пространстве.


Пример:
~~~~~~~

.. code-block:: yaml

  check_free_space:
    type: dschecker
    descr: вывод информации о дисковом пространстве