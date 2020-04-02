# -*- encoding: utf-8 -*-

import os
import secrets
import tarfile

import docker
import pytest

from .docker_utils import INFINITY_PROCESS, CONTAINERS_OPTS, ENV


def pytest_addoption(parser):
    """Реализация дополнительных опций.

    Добавляет опции для выбора тестируемых версий python3,
    подверсия передаётся цифрой:
    -2 (3.2), -5 (3.5), -25 (3.2 и 3.5)

    Добавляет опцию для проверки сжатой версии:
        --wrapped (по-умолчанию false)

    """
    for os_name in CONTAINERS_OPTS.keys():
        parser.addoption(
            '-{0}'.format(os_name),
            action='store_true',
            help='run tests in {0}.'.format(os_name),
        )
    parser.addoption(
        '--all',
        action='store_true',
        help='run test in all versions.',
    )
    parser.addoption(
        '--wrapped',
        action='store_true',
        help='use wrapped form.',
    )


def pytest_generate_tests(metafunc):
    """Изменяет порядок генерации тестов.

    Генерирует тесты для необходимых ОС и подставляет соответствующую через
    фикстуру container.

    Также подставляет конфигурацию для сжатой версии, если был тест
    выполняется с аргументом --wrapped.

    """
    if 'container' in metafunc.fixturenames:
        testing_os = set()
        if metafunc.config.getoption('all'):
            chosen_versions = list(CONTAINERS_OPTS.keys())
        else:
            for os_name in CONTAINERS_OPTS.keys():
                if metafunc.config.getoption(os_name):
                    testing_os.add(os_name)
            if metafunc.config.getoption('5') or not testing_os:
                # добавлять python3.5, если версия не выбрана
                testing_os.add('5')
            chosen_versions = list(testing_os & set(CONTAINERS_OPTS.keys()))
        metafunc.parametrize(
            'container',
            chosen_versions,
            indirect=['container'],
            ids=['python3.{v}'.format(v=ver) for ver in chosen_versions],
        )
    if 'kristabackup_tar' in metafunc.fixturenames:
        if metafunc.config.getoption('wrapped'):
            params = [('../out', 'KristaBackup')]
            ids = ['wrapped']
        else:
            params = [('../KristaBackup', 'KristaBackup.py')]
            ids = ['unwrapped']
        metafunc.parametrize(
            'kristabackup_tar',
            params,
            indirect=['kristabackup_tar'],
            ids=ids,
        )


def pytest_sessionfinish(session, exitstatus):  # noqa: ignore=W0613
    """Чистит мусор после тестов.

    Запускается в конце сессии.

    """
    docker_client = docker.from_env()
    for os_entry in CONTAINERS_OPTS.values():
        if os_entry.get('prepared'):
            docker_client.images.remove(os_entry.get('prepared').short_id)


@pytest.fixture(scope='session')
def kristabackup_tar(request):
    """Фикстура для создания архива с приложением.

    Уже содержит в себе config.yaml. Архив удаляется после завершения всех
    тестов.

    Args:
        request: содержит параметр param (tuple), включающий путь
        к исходникам и имя исполняемого файла

    Yields:
        (tar_archive_stream, executable): архивированные данные приложения и
        имя исполняемого файла

    """
    path, executable = request.param
    arch_src = 'kristabackup_{0}.tar'.format(secrets.token_hex(4))
    with tarfile.open(arch_src, mode='w') as tar:
        tar.add(path, arcname='KristaBackup')
        tar.add(
            'test_config.yaml',
            arcname='KristaBackup/config.yaml',
        )
    with open(arch_src, 'rb') as tar_archive:
        yield (tar_archive.read(), executable)
    os.remove(arch_src)


@pytest.fixture(scope='class')
def container(request, kristabackup_tar):   # noqa: ignore=W0621, WPS442
    """Фикстура для создания докер контейнера.

    Название требуемой версии берётся из request.params, а соответствующая
    конфигурация хранится в docker_utils.CONTAINERS_OPTS.

    После выполнения теста контейнер уничтожается.

    Args:
        request: содержит параметр param имеющий значение требуемого окружения
        kristabackup_tar: результат фикстуры kristabackup_tar

    Yields:
        container: докер контейнер

    """
    py3version = request.param
    created_containers = []

    yield lambda: _container(
        py3version,
        kristabackup_tar,
        created_containers,
    )

    for xcontainer in created_containers:
        xcontainer.stop()
        xcontainer.remove()


def _container(
    py3version,
    kristabackup_tar,    # noqa: W0621, WPS442
    created_containers=None,
):
    config = CONTAINERS_OPTS[py3version]
    docker_client = docker.from_env()

    if config.get('prepared', None):
        # если образ контейнера был использован ранее и сохранён,
        # то он переиспользуется
        xcontainer = docker_client.containers.run(
            config.get('prepared'),
            INFINITY_PROCESS,
            detach=True,
            environment=ENV,
        )
    else:
        image = docker_client.images.pull(config['docker_image'])
        xcontainer = docker_client.containers.run(
            image,
            INFINITY_PROCESS,
            detach=True,
            environment=ENV,
        )
        xcontainer.put_archive('/opt/', kristabackup_tar[0])
        xcontainer.exec_run(
            'ln -s /opt/KristaBackup/{0} {1}'.format(
                kristabackup_tar[1],
                config['link'],
            ),
        )
        xcontainer.exec_run(
            'ln -fs /usr/bin/python3.{0} /usr/bin/python3'.format(
                py3version,
            ),
        )
        config['prepared'] = xcontainer.commit()

    if created_containers is not None:
        created_containers.append(xcontainer)
    return xcontainer


def pytest_configure():
    pytest.shared = {}
