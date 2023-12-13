from __future__ import annotations

import builtins
import json
import ntpath
import os.path
import posixpath
from unittest import mock

import pytest
from pre_commit.languages import docker
from pre_commit.util import CalledProcessError

from testing.language_helpers import run_language
from testing.util import xfailif_windows

DOCKER_CGROUP_EXAMPLE = b'''\
12:hugetlb:/docker/c33988ec7651ebc867cb24755eaf637a6734088bc7eef59d5799293a9e5450f7
11:blkio:/docker/c33988ec7651ebc867cb24755eaf637a6734088bc7eef59d5799293a9e5450f7
10:freezer:/docker/c33988ec7651ebc867cb24755eaf637a6734088bc7eef59d5799293a9e5450f7
9:cpu,cpuacct:/docker/c33988ec7651ebc867cb24755eaf637a6734088bc7eef59d5799293a9e5450f7
8:pids:/docker/c33988ec7651ebc867cb24755eaf637a6734088bc7eef59d5799293a9e5450f7
7:rdma:/
6:net_cls,net_prio:/docker/c33988ec7651ebc867cb24755eaf637a6734088bc7eef59d5799293a9e5450f7
5:cpuset:/docker/c33988ec7651ebc867cb24755eaf637a6734088bc7eef59d5799293a9e5450f7
4:devices:/docker/c33988ec7651ebc867cb24755eaf637a6734088bc7eef59d5799293a9e5450f7
3:memory:/docker/c33988ec7651ebc867cb24755eaf637a6734088bc7eef59d5799293a9e5450f7
2:perf_event:/docker/c33988ec7651ebc867cb24755eaf637a6734088bc7eef59d5799293a9e5450f7
1:name=systemd:/docker/c33988ec7651ebc867cb24755eaf637a6734088bc7eef59d5799293a9e5450f7
0::/system.slice/containerd.service
'''  # noqa: E501

DOCKER_MOUNTINFO_EXAMPLE = b'''\
348 271 0:134 / / rw,relatime master:69 - overlay overlay rw,lowerdir=/var/lib/docker/overlay2/l/JA7YFUDZG7HJ6SULPO4D4TOKEC:/var/lib/docker/overlay2/l/UKULGDGAAYVP5Y64C5QUS4RDU6:/var/lib/docker/overlay2/l/CFDV7YE32BB4XONCL3I7PHLOLG:/var/lib/docker/overlay2/l/YND6YIU57TVLAHWVZ2REKMSZ5R:/var/lib/docker/overlay2/l/Z65PZCFL6YK2L6KMZUJRWL4D75:/var/lib/docker/overlay2/l/IFNNE5WOAKIBU246GGLR7467QJ:/var/lib/docker/overlay2/l/53Q7PJSSB3NTJHROSQ5UAN7B4J:/var/lib/docker/overlay2/l/XFZFQXJD356SZBUE5NJRTCHXQ3:/var/lib/docker/overlay2/l/BWCQOGQRVOHSZED2MMUPIKVQLX:/var/lib/docker/overlay2/l/HYQZL6IGWSL2ZWZULQ6DHZ732Q:/var/lib/docker/overlay2/l/BXH4YC7ZTZS5MMFBVAYSFJNAX7:/var/lib/docker/overlay2/l/DTPWRTNSO5WAR5NY3GJV6PTWOP:/var/lib/docker/overlay2/l/LXSI5HTAMHSBTK63TUPEGNH6HO:/var/lib/docker/overlay2/l/22QNDQVKDJTCZC63EF7FWRHVPB:/var/lib/docker/overlay2/l/ETJB5Q6QEWK4Q4KNUT6S3GBXOG:/var/lib/docker/overlay2/l/26IYIZLLAN72UKB7K6EYR3FR3D:/var/lib/docker/overlay2/l/EEHO3GNGKDMVKONTLIKOT3EVHU:/var/lib/docker/overlay2/l/MGVC4ZEVMM6QL6YMZQM7Y7LTWF:/var/lib/docker/overlay2/l/SA2DJVIGM53IDHPDLJOOLHGES2:/var/lib/docker/overlay2/l/GN2H5Q6JYE6CK3Z3LMDKG42ZVT:/var/lib/docker/overlay2/l/6XW2PVALMDQRMQQPUCO5WOXZZR:/var/lib/docker/overlay2/l/VMXVXVKSUWKGHJWQDXHLEJ4L7R:/var/lib/docker/overlay2/l/UDPBCAYVT5MF72CM4S2P6IVQW4:/var/lib/docker/overlay2/l/JNBRKRFDRUOMD2SZSRVVSSC2IM:/var/lib/docker/overlay2/l/T2QWLINEQPKWQPFMK3PXYB6FQ4:/var/lib/docker/overlay2/l/I2EOLGIF6DUE6TYZ72Q7DRVYQ5,upperdir=/var/lib/docker/overlay2/72005e2c75d20205f5151728b8deea74d46de088b16e1119b37f68fe146d9bad/diff,workdir=/var/lib/docker/overlay2/72005e2c75d20205f5151728b8deea74d46de088b16e1119b37f68fe146d9bad/work
349 348 0:137 / /proc rw,nosuid,nodev,noexec,relatime - proc proc rw
350 348 0:138 / /dev rw,nosuid - tmpfs tmpfs rw,size=65536k,mode=755
351 350 0:139 / /dev/pts rw,nosuid,noexec,relatime - devpts devpts rw,gid=5,mode=620,ptmxmode=666
352 348 0:140 / /sys ro,nosuid,nodev,noexec,relatime - sysfs sysfs ro
353 352 0:28 / /sys/fs/cgroup ro,nosuid,nodev,noexec,relatime - cgroup2 cgroup rw
354 350 0:136 / /dev/mqueue rw,nosuid,nodev,noexec,relatime - mqueue mqueue rw
355 350 0:141 / /dev/shm rw,nosuid,nodev,noexec,relatime - tmpfs shm rw,size=65536k
357 348 254:1 /docker/containers/c33988ec7651ebc867cb24755eaf637a6734088bc7eef59d5799293a9e5450f7/resolv.conf /etc/resolv.conf rw,relatime - ext4 /dev/vda1 rw,discard
358 348 254:1 /docker/containers/c33988ec7651ebc867cb24755eaf637a6734088bc7eef59d5799293a9e5450f7/hostname /etc/hostname rw,relatime - ext4 /dev/vda1 rw,discard
359 348 254:1 /docker/containers/c33988ec7651ebc867cb24755eaf637a6734088bc7eef59d5799293a9e5450f7/hosts /etc/hosts rw,relatime - ext4 /dev/vda1 rw,discard
363 348 0:18 /host-services/docker.proxy.sock /run/docker.sock rw,relatime - tmpfs tmpfs rw,size=607780k,mode=755
272 349 0:137 /bus /proc/bus ro,nosuid,nodev,noexec,relatime - proc proc rw
273 349 0:137 /fs /proc/fs ro,nosuid,nodev,noexec,relatime - proc proc rw
274 349 0:137 /irq /proc/irq ro,nosuid,nodev,noexec,relatime - proc proc rw
275 349 0:137 /sys /proc/sys ro,nosuid,nodev,noexec,relatime - proc proc rw
281 352 0:143 / /sys/firmware ro,relatime - tmpfs tmpfs ro
'''  # noqa: E501

# The ID should match the above cgroup example.
CONTAINER_ID = 'c33988ec7651ebc867cb24755eaf637a6734088bc7eef59d5799293a9e5450f7'  # noqa: E501

NON_DOCKER_CGROUP_EXAMPLE = b'''\
12:perf_event:/
11:hugetlb:/
10:devices:/
9:blkio:/
8:rdma:/
7:cpuset:/
6:cpu,cpuacct:/
5:freezer:/
4:memory:/
3:pids:/
2:net_cls,net_prio:/
1:name=systemd:/init.scope
0::/init.scope
'''


def test_docker_fallback_user():
    def invalid_attribute():
        raise AttributeError

    with mock.patch.multiple(
            'os', create=True,
            getuid=invalid_attribute,
            getgid=invalid_attribute,
    ):
        assert docker.get_docker_user() == ()


def test__is_in_docker_cgroup_v1_no_file():
    with mock.patch.object(
            builtins,
            'open',
            side_effect=FileNotFoundError,
    ) as m_open:
        assert docker._is_in_docker_cgroup_v1() is False
        m_open.assert_called_once_with('/proc/1/cgroup', 'rb')


def _mock_open(data):
    return mock.patch.object(
        builtins,
        'open',
        new_callable=mock.mock_open,
        read_data=data,
    )


def test_is_in_docker_cgroup_v1_docker_in_file():
    with _mock_open(DOCKER_CGROUP_EXAMPLE) as m_open:
        assert docker._is_in_docker_cgroup_v1() is True
        m_open.assert_called_once_with('/proc/1/cgroup', 'rb')


def test_is_in_docker_cgroup_v1_docker_not_in_file():
    with _mock_open(NON_DOCKER_CGROUP_EXAMPLE) as m_open:
        assert docker._is_in_docker_cgroup_v1() is False
        m_open.assert_called_once_with('/proc/1/cgroup', 'rb')


def test_is_in_docker_dockerenv_exists():
    with mock.patch.object(
            docker.os.path,
            'exists',
            return_value=True,
    ) as m_exists:
        assert docker._is_in_docker_dockerenv() is True
        m_exists.assert_called_once_with('/.dockerenv')


def test_is_in_docker_dockerenv_not_exists():
    with mock.patch.object(
            docker.os.path,
            'exists',
            return_value=False,
    ) as m_exists:
        assert docker._is_in_docker_dockerenv() is False
        m_exists.assert_called_once_with('/.dockerenv')


def test_get_container_id_from_cgroup():
    with _mock_open(DOCKER_CGROUP_EXAMPLE) as m_open:
        assert docker._get_container_id_from_cgroup() == CONTAINER_ID
        m_open.assert_called_once_with('/proc/1/cgroup', 'rb')


def test_get_container_id_from_cgroup_failure():
    with _mock_open(b'') as m_open, pytest.raises(RuntimeError):
        docker._get_container_id_from_cgroup()
        m_open.assert_called_once_with('/proc/1/cgroup', 'rb')


def test_get_container_id_from_mountinfo():
    with _mock_open(DOCKER_MOUNTINFO_EXAMPLE) as m_open:
        assert docker._get_container_id_from_mountinfo() == CONTAINER_ID
        m_open.assert_called_once_with('/proc/self/mountinfo', 'rb')


def test_get_container_id_from_mountinfo_failure():
    with _mock_open(b'') as m_open, pytest.raises(RuntimeError):
        docker._get_container_id_from_mountinfo()
        m_open.assert_called_once_with('/proc/self/mountinfo', 'rb')


def test_get_docker_path_not_in_docker_returns_same():
    with mock.patch.object(
            docker,
            '_is_in_docker_cgroup_v1',
            return_value=False,
    ):
        with mock.patch.object(
                docker,
                '_is_in_docker_dockerenv',
                return_value=False,
        ):
            assert docker._get_docker_path('abc') == 'abc'


@pytest.fixture
def cgroup_v1():
    with mock.patch.object(
            docker,
            '_is_in_docker_cgroup_v1',
            return_value=True,
    ):
        with mock.patch.object(
            docker,
            '_get_container_id_from_cgroup',
            return_value=CONTAINER_ID,
        ):
            yield


@pytest.fixture
def cgroup_v2():
    with mock.patch.object(
            docker,
            '_is_in_docker_dockerenv',
            return_value=True,
    ):
        with mock.patch.object(
            docker,
            '_get_container_id_from_mountinfo',
            return_value=CONTAINER_ID,
        ):
            yield


def _linux_commonpath():
    return mock.patch.object(os.path, 'commonpath', posixpath.commonpath)


def _nt_commonpath():
    return mock.patch.object(os.path, 'commonpath', ntpath.commonpath)


def _docker_output(out):
    ret = (0, out, b'')
    return mock.patch.object(docker, 'cmd_output_b', return_value=ret)


@pytest.mark.parametrize('scenario', ['cgroup_v1', 'cgroup_v2'])
def test_get_docker_path_in_docker_no_binds_same_path(scenario, request):
    request.getfixturevalue(scenario)
    docker_out = json.dumps([{'Mounts': []}]).encode()

    with _docker_output(docker_out):
        assert docker._get_docker_path('abc') == 'abc'


@pytest.mark.parametrize('scenario', ['cgroup_v1', 'cgroup_v2'])
def test_get_docker_path_in_docker_binds_path_equal(scenario, request):
    request.getfixturevalue(scenario)
    binds_list = [{'Source': '/opt/my_code', 'Destination': '/project'}]
    docker_out = json.dumps([{'Mounts': binds_list}]).encode()

    with _linux_commonpath(), _docker_output(docker_out):
        assert docker._get_docker_path('/project') == '/opt/my_code'


@pytest.mark.parametrize('scenario', ['cgroup_v1', 'cgroup_v2'])
def test_get_docker_path_in_docker_binds_path_complex(scenario, request):
    request.getfixturevalue(scenario)
    binds_list = [{'Source': '/opt/my_code', 'Destination': '/project'}]
    docker_out = json.dumps([{'Mounts': binds_list}]).encode()

    with _linux_commonpath(), _docker_output(docker_out):
        path = '/project/test/something'
        assert docker._get_docker_path(path) == '/opt/my_code/test/something'


@pytest.mark.parametrize('scenario', ['cgroup_v1', 'cgroup_v2'])
def test_get_docker_path_in_docker_no_substring(scenario, request):
    request.getfixturevalue(scenario)
    binds_list = [{'Source': '/opt/my_code', 'Destination': '/project'}]
    docker_out = json.dumps([{'Mounts': binds_list}]).encode()

    with _linux_commonpath(), _docker_output(docker_out):
        path = '/projectSuffix/test/something'
        assert docker._get_docker_path(path) == path


@pytest.mark.parametrize('scenario', ['cgroup_v1', 'cgroup_v2'])
def test_get_docker_path_in_docker_binds_path_many_binds(scenario, request):
    request.getfixturevalue(scenario)
    binds_list = [
        {'Source': '/something_random', 'Destination': '/not-related'},
        {'Source': '/opt/my_code', 'Destination': '/project'},
        {'Source': '/something-random-2', 'Destination': '/not-related-2'},
    ]
    docker_out = json.dumps([{'Mounts': binds_list}]).encode()

    with _linux_commonpath(), _docker_output(docker_out):
        assert docker._get_docker_path('/project') == '/opt/my_code'


@pytest.mark.parametrize('scenario', ['cgroup_v1', 'cgroup_v2'])
def test_get_docker_path_in_docker_windows(scenario, request):
    request.getfixturevalue(scenario)
    binds_list = [{'Source': r'c:\users\user', 'Destination': r'c:\folder'}]
    docker_out = json.dumps([{'Mounts': binds_list}]).encode()

    with _nt_commonpath(), _docker_output(docker_out):
        path = r'c:\folder\test\something'
        expected = r'c:\users\user\test\something'
        assert docker._get_docker_path(path) == expected


@pytest.mark.parametrize('scenario', ['cgroup_v1', 'cgroup_v2'])
def test_get_docker_path_in_docker_docker_in_docker(scenario, request):
    request.getfixturevalue(scenario)
    # won't be able to discover "self" container in true docker-in-docker
    err = CalledProcessError(1, (), b'', b'')
    with mock.patch.object(docker, 'cmd_output_b', side_effect=err):
        assert docker._get_docker_path('/project') == '/project'


@xfailif_windows  # pragma: win32 no cover
def test_docker_hook(tmp_path):
    dockerfile = '''\
FROM ubuntu:22.04
CMD ["echo", "This is overwritten by the entry"']
'''
    tmp_path.joinpath('Dockerfile').write_text(dockerfile)

    ret = run_language(tmp_path, docker, 'echo hello hello world')
    assert ret == (0, b'hello hello world\n')
