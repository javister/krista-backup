.. _naming_schemes:

Именованные схемы
=================

Введение
--------

Система именованных схем нужна для конфигурирования имён выходных файлов,
если стандартная не подходит.

Для создания схемы **необходимо** указать три паттерна:

* fsdump_fileformat
* fsdump_hash_fileformat
* pgdump_fileformat
* pgdump_hash_fileformat


Виды переменных
---------------

Существует два вида переменных: контекстные и неконтекстные:

* Контекстные определяются во время выполнения. Для них зарезервированы следующие имена: `date`, `level`, `dbname`, `ext`, `basename`.

* Неконтекстные можно определить в схеме:

.. code:: yaml

    naming_scheme:
    ...
        test_var: 'test_var'
    ...

Примечание
~~~~~~~~~~

Неконтекстные переменные не могут иметь имя из списка зарезервированных имён
для контекстных переменных.


Применение
----------

Именную схему можно определить и применить следующим образом (приоритет в
порядке возрастания):

1. В разделе дефолтном разделе naming:

.. code:: yaml

    naming:
        server_name: example
        project: project
        region: region
        naming_scheme:
            scheme_id: 'example'
            test_param: 'new'
            fsdump_fileformat: '{test_param}-{date:%d%m%Y_%S}-{level}.{ext}'
            fsdump_hash_fileformat: '{test_param}-{date:%d%m%Y_%S}-test.hash'
            pgdump_fileformat: '{test_param}-{dbname}-{date:%d%m%Y}.pgdump'
            pgdump_hash_fileformat: '{test_param}-{dbname}-{date:%d%m%Y_%S}-test.hash'

2. В разделе naming у заданий:

.. code:: yaml

    schedule:
        make_full_dump:
            descr: Бекап каталога 0-го уровня (полный)
            cron: 00 23 * * *
            actions:
            - make_full
            - clean_full
            naming:
                project: cons
                region: 888
                naming_scheme:
                    fsdump_fileformat: 'last_backup.{ext}'
                    fsdump_hash_fileformat: 'last_backup_hash.hash'
                    pgdump_fileformat: '{dbname}-{date:%d%m%Y}.pgdump'
                    pgdump_hash_fileformat: '{dbname}-{date:%d%m%Y}.hash'

3. В разделе naming у действий:

.. code:: yaml

    actions:
        make_full:
            basename: etc
            src_path: /etc/
            level: 0
            type: tar
            naming_scheme:
                fsdump_fileformat: '{date:%d%m%Y_%S}-{basename}-{level}.{ext}'
                fsdump_hash_fileformat: '{name}-{date:%d%m%Y_%S}-test.hash'
                pgdump_fileformat: '{name}-{dbname}-{date:%d%m%Y}.pgdump'
                pgdump_hash_fileformat: '{name}-{dbname}-{date:%d%m%Y}.pgdump'

Идентификатор
-------------

У всех схем присутсутвует атрибут `scheme_id`, который является уникальным.
У стандартная схема атрибут `scheme_id` имеет значение `default`.  
Если `scheme_id` не указан явно, то он создаётся автоматически.

Его значение можно указывать *вместо* конфигурации именованной схемы. Это бывает
полезно, чтобы использовать уже заданные схемы.

Пример
~~~~~~

.. code:: yaml

    naming:
        server_name: example
        project: project
        region: region
        naming_scheme:
            scheme_id: old_scheme
            fsdump_fileformat: '{date:%d%m%Y_%S}-{level}.{ext}'
            pgdump_fileformat: '{dbname}-{date:%d%m%Y}.pgdump'
            hash_fileformat: '{test_param}-{date:%d%m%Y_%S}-test.hash'

    schedule:
        make_full_dump:
            descr: Бекап каталога 0-го уровня (полный)
            cron: 00 23 * * *
            actions:
            - make_full
            - clean_full
            naming:
                naming_scheme:
                    scheme_id: new_scheme
                    fsdump_fileformat: 'last_backup.{ext}'
                    pgdump_fileformat: '{dbname}-{date:%d%m%Y}.pgdump'
                    hash_fileformat: 'last_backup_hash.hash'
    
    actions:
        make_full:
            basename: etc
            src_path: /etc/
            level: 0
            type: tar
            naming_scheme: old_scheme


Дополнительно
-------------

Контекстная переменная ext
~~~~~~~~~~~~~~~~~~~~~~~~~~
На данный момент только `tar` и `zip` могут её использовать.
В остальных случаях её стоит пропустить

Контекстная переменная date
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Переменная date форматирует время в формате strftime. 

На данный момент поддерживаются только следующие параметры: `%d`, `%m`, `%Y`, `%H`, `%M`, `%S`.
Список расширяется по мере необходимости.

Также, настоятельно рекомендуется использовать одинаковый формат времени
для имён файлов и имён файлов с хэшсуммой, чтобы избежать проблем с ротированием и переносом.

Часто используемые схемы
~~~~~~~~~~~~~~~~~~~~~~~~

Часто используемые схемы для удобства можно добавить в саму программу.
Класс новой схемы нужно наследовать от
`DefaultNamingScheme <https://github.com/javister/krista-backup/blob/master/KristaBackup/common/schemes/default_scheme.py>`_.
Подробнее можно посмотреть в модуле
`schemes <https://github.com/javister/krista-backup/blob/master/KristaBackup/common/schemes/schemes.py>`_.