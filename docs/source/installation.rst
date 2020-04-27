.. _installation:

Установка
=========

Рекомендуемый способ установки системы.

1. Клонировать репозиторий. 

.. code:: bash

  git clone https://github.com/javister/krista-backup

2. Скопировать проект в необходимую директорию. Обычно мы храним
приложение в каталоге /opt. Для установки в /opt могут
потребоваться права sudo.

.. code:: bash

  cp KristaBackup/KristaBackup /opt/

3. Установить зависимости для базовой системы (без веб-интерфейса) из файла requirements.system.
Зависимости устанавливаются из репозиториев ОС. Для Debian и Ubunutu команда будет выглядеть так:

.. code:: bash

  cd /opt/KristaBackup
  sed 's/#.*//' requirements.system | xargs sudo apt-get install -y

3. Установить python-зависимости для веб-интерфейса с помощью утилиты pip.
Для того чтобы не менять окружение системы и соблюсти требуемую версионность,
лучше установить зависимости в тот же каталог, что и приложение,
используя опцию --target.

.. code:: bash

  cd /opt/KristaBackup
  python3 -m pip install -r requirements.txt --target .

Назначаем владельца и права, если копировали/ставили зависимости не под root:

.. code:: bash

  chown -R root:root /opt/KristaBackup
  chmod -R 0755 /opt/KristaBackup/KristaBackup.py
  chmod -R 0755 /opt/KristaBackup/UsersUtils.py

