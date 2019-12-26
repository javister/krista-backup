# KristaBackup

## Описание

Система для автоматизации процесса создания, ротации и перемещения бэкапов.

Особенности:

1. Работает автономно
2. Имеет кросс-платформенную конфигурацию
3. Логирование во время выполнения: сокращённое и подробное
4. Интегрируема с системами мониторинга (например, Zabbix)

## Требования

Поддерживаемые OS: Ubuntu 14.04 и выше, Debian 8 и выше, CentOS 7, AltLinux 8, Astra Linux 1.6

Для запуска: `python3.4`

Для сборки: `python3.7`

## Установка

1 вариант - клонирование из репозитария
```bash
git clone ...
```

Назначаем владельца и права, если копировали не под рутом:

```bash
chown -R root:root KristaBackup
chmod -R 0755 KristaBackup/KristaBackup.py
```

2 вариант - собранный бинарник

Для сборки:

```bash
python3 build.py
# если стандартная версия питона ниже
python3.7 build.py
```

В папке `out` будет результат сборки, который удобно использовать и распространять:

```bash
root@pc:~/KristaBackup$ ls out/
KristaBackup  requirements.system
```

## Терминология

- Минимальная единица -- действие (action).
- Задание (task) содержит список действий, которые требуется выполнить.
- Все задания вместе являются расписанием (schedule).

Схематичный пример:

```yaml
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
```

## Использование

По умолчанию, требуется запуск от пользователя с root правами.

Запуск задания вручную:

```bash
./KristaBackup run your_task
```

Для подробного вывода действий в консоль существует флаг `-v`:

```bash
./KristaBackup run your_task -v
```

Также, выполнение заданий можно автоматизировать добавлением их в `crontab`.

Добавить задание в `crontab` и убрать можно следующими командами:

```bash
./KristaBackup en your_task  # включить задание
./KristaBackup dis your_task # выключить задание
```

## Пример написания конфигурации

Здесь будет рассматриваться пример файла конфигураций, который будет
содержать настройки для выполнения полного и разностного бэкапа каталога `/etc`.

Ротация полного бэкапа будет выполняться раз в неделю, хранится
2 копии; ротация разностного бэкапа будет выполняться ежедневно, хранится 4 копии.

В корневом каталоге находится файл `config.yaml`, содержащий конфигурацию
в формате `yaml`.

Добавим в начало файла блок `naming`:

```yaml
naming:
  server_name: example_server # имя сервера
  project: server_backup # название проекта
  region: region_name # название региона
```

Этот блок используется для подстановки в результирующие файлы. Далее добавим блок `logging`:

```yaml
logging:
  logs_path:
    /var/log/KristaBackup # директория, в которой
    # будут храниться логи
```

Теперь опишем действия. Создадим блок `actions` и добавим в него действие, которое
будет выполнять полный бэкап:

```yaml
actions:
  tarjob_0level_etc:
    basename: etc # уникальное имя
    src_path: /etc # исходная директория
    dest_path: /backup # результирующая директория
    level: 0 # уровень бэкапа
    level_folders: 0,1 # имена папок для уровней бэкапа
    descr: бэкап файлов /etc 0-го уровня # ёмкое описание
    type: tar # тип
```

Наследуем от `tarjob_0level_etc` новое действие, которое будет выполнять разностный бэкап:

```yaml
actions:
  tarjob_0level_etc:
  ...
    type: tar

  tarjob_1level_etc:
    source: tarjob_0level_etc   # указано родительское действие
    level: 1
    descr: бэкап файлов /etc 1-го уровня
    type: tar
```

Действие `tarjob_1level_etc` импортировало все параметры, которые установлены в `tarjob_0level_etc`,
но не установлены в нём самом.

Заметим, что в `tarjob_1level_etc` указан тип `tar`, хотя его
можно и упустить, так как в таком случае он бы был заимствован из `tarjob_0level_etc`.

По аналогии добавим действия для ротации:

```yaml
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
```

Осталось собрать действия в задания. Добавим ``schedule`` после ``logging``,
а в него задание для выполнения полного бэкапа:

```yaml
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
    descr: Бэкап каталога 0-го уровня (полный)

actions:
  tarjob_0level_etc:
...
```

По аналогии сделаем задания для выполнения разностного бэкапа:
```yaml
...
logging:
  logs_path: /var/log/KristaBackup

schedule:
  full_dump:                        # имя задания
  ...
    descr: Бэкап каталога 0-го уровня (полный)
  
  diff_dump:
    actions:
      - tarjob_1level_etc
      - cleaner_tarjob_1level_etc
    cron: '00 23 * * 1-6'
    descr: Бэкап каталога 0-го уровня (полный)
```

Конфигурация завершена. Финальный результат:

```yaml
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
    descr: Бэкап каталога 0-го уровня (полный)

  diff_dump:
    actions:
      - tarjob_1level_etc
      - cleaner_tarjob_1level_etc
    cron: '00 23 * * 1-6'
    descr: Бэкап каталога 0-го уровня (полный)

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
```

Подробнее о конфигурировании можно прочитать в docs/build/html/pages/configuration.html

# Разработчики

s.postnikov@krista.ru, m.adrian@krista.ru

# Лицензия

Copyright 2019 ООО НПО Криста

Licensed under the Apache License, Version 2.0