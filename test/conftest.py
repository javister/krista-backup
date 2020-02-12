# -*- encoding: utf-8 -*-

import os
import secrets
import tarfile

import docker
import pytest

from .docker_utils import INFINITY_PROCESS, OS_CONFIG


def pytest_addoption(parser):
    """Реализация дополнительных опций.

    Добавляет опции для запуска определённых ОС:
        --ubuntu (по-умолчанию), --debian и т.д.
        --all для выбора всех.

    Добавляет опцию для проверки сжатой версии:
        --wrapped (по-умолчанию false)

    """
    for os_name in OS_CONFIG.keys():
        parser.addoption(
            '--{0}'.format(os_name),
            action='store_true',
            help='run tests in {0}.'.format(os_name),
        )
    parser.addoption(
        '--all',
        action='store_true',
        help='run test in all OS.',
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
            valid_os = list(OS_CONFIG.keys())
        else:
            for os_name in OS_CONFIG.keys():
                if metafunc.config.getoption(os_name):
                    testing_os.add(os_name)
            if metafunc.config.getoption('ubuntu') or not testing_os:
                # добавлять ubuntu если множество пусто
                testing_os.add('ubuntu')
            valid_os = list(testing_os & set(OS_CONFIG.keys()))
        metafunc.parametrize(
            'container',
            valid_os,
            indirect=['container'],
            ids=valid_os,
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

def pytest_sessionfinish(session, exitstatus):
    """Чистит мусор после тестов.

    Запускается в конце сессии.

    """
    docker_client = docker.from_env()
    for os_entry in OS_CONFIG.values():
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
    tar = tarfile.open(arch_src, mode='w')
    try:
        tar.add(path, arcname='KristaBackup')
        tar.add(
            'test_config.yaml',
            arcname='KristaBackup/config.yaml',
        )
    finally:
        tar.close()
    with open(arch_src, 'rb') as tar_archive:
        yield (tar_archive.read(), executable)
    os.remove(arch_src)


@pytest.fixture(scope='class')
def container(request, kristabackup_tar):
    """Фикстура для создания докер контейнера.

    Название требуемой OS берётся из request.params, а соответствующая
    конфигурация хранится в docker_utils.OS_CONFIG.

    После выполнения теста контейнер уничтожается.

    Args:
        request: содержит параметр param имеющий значение требуемой OS
        kristabackup_tar: результат фикстуры kristabackup_tar

    Yields:
        container: докер контейнер

    """
    os_name = request.param
    created_containers = []

    if os_name == 'ubuntu':
        yield lambda: _ubuntu_container(
            kristabackup_tar,
            created_containers,
        )

    elif os_name == 'debian':
        yield lambda: _debian_container(
            kristabackup_tar,
            created_containers,
        )

    for container in created_containers:
        container.stop()
        container.remove()


def _ubuntu_container(
    kristabackup_tar,
    created_containers=None,
):
    docker_client = docker.from_env()
    if OS_CONFIG['ubuntu'].get('prepared'):
        container = docker_client.containers.run(
            OS_CONFIG['ubuntu'].get('prepared'),
            INFINITY_PROCESS, detach=True,
            environment=['PYTHONIOENCODING=utf8', 'LANG=ru_RU.utf8'],
        )
    else:
        image = docker_client.images.pull(
            OS_CONFIG['ubuntu']['docker_image'],
        )
        container = docker_client.containers.run(
            image, INFINITY_PROCESS, detach=True,
            environment=['PYTHONIOENCODING=utf8', 'LANG=ru_RU.utf8'],
        )
        container.exec_run('locale-gen ru_RU')
        container.exec_run('locale-gen ru_RU.UTF-8')
        container.exec_run(
            'ln -s /opt/KristaBackup/{0} {1}'.format(
                kristabackup_tar[1],
                OS_CONFIG['debian']['link'],
            ),
        )
        container.put_archive('/opt/', kristabackup_tar[0])
        OS_CONFIG['ubuntu']['prepared'] = container.commit()

    if created_containers is not None:
        created_containers.append(container)
    return container


def _debian_container(
    kristabackup_tar,
    created_containers=None,
):
    docker_client = docker.from_env()
    if OS_CONFIG['debian'].get('prepared'):
        container = docker_client.containers.run(
            OS_CONFIG['debian'].get('prepared'), INFINITY_PROCESS, detach=True,
            environment=['PYTHONIOENCODING=utf8', 'LANG=C.UTF-8'],
        )
    else:
        image = docker_client.images.pull(
            OS_CONFIG['debian']['docker_image'],
        )
        container = docker_client.containers.run(
            image, INFINITY_PROCESS, detach=True,
            environment=['PYTHONIOENCODING=utf8', 'LANG=C.UTF-8'],
        )
        container.exec_run('apt update')
        container.exec_run('apt install python3 -y')
        container.exec_run('apt install locales')
        container.exec_run('locale-gen ru_RU.UTF-8')
        container.exec_run(
            'ln -s /opt/KristaBackup/{0} {1}'.format(
                kristabackup_tar[1],
                OS_CONFIG['debian']['link'],
            ),
        )
        container.put_archive('/opt/', kristabackup_tar[0])
        OS_CONFIG['debian']['prepared'] = container.commit()

    if created_containers is not None:
        created_containers.append(container)
    return container




class State:
    """Класс для сохранения состояния"""
    
@pytest.fixture(scope='class')
def state():
    """Фикстура для сохранения состояния между тестами.

    Используется для случаев, когда следующий тест основывается
    на окружении текущего.
    """
    state = State()
    yield state
    del state