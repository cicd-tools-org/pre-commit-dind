"""Test the __main__ module."""
from __future__ import annotations

import os
from io import BufferedIOBase
from unittest import mock

from pre_commit_dind import __main__
from pre_commit_dind.__main__ import installer


class TestMonkeyPatch:
    """Test the __main__ module."""

    def create_read_mock(self):
        mock_obj = mock.MagicMock(spec=BufferedIOBase)
        mock_obj.__enter__.return_value.read.return_value = \
            'from pre_commit.main import main'
        return mock_obj

    def create_write_mock(self):
        mock_obj = mock.MagicMock(spec=BufferedIOBase)
        return mock_obj

    def test_installer_file_operations(self):
        """Test the installer function."""

        with mock.patch.object(__main__, 'open') as m_open:
            read_mock1 = self.create_read_mock()
            write_mock1 = self.create_write_mock()
            read_mock2 = self.create_read_mock()
            write_mock2 = self.create_write_mock()
            m_open.side_effect = [
                read_mock1,
                write_mock1,
                read_mock2,
                write_mock2,
            ]

            installer()

        read_mock1.__enter__.return_value.read.assert_called_once_with()
        write_mock1.__enter__.return_value.write.assert_called_once_with(
            'from pre_commit_dind import main',
        )
        read_mock2.__enter__.return_value.read.assert_called_once_with()
        write_mock2.__enter__.return_value.write.assert_called_once_with(
            'from pre_commit_dind import main',
        )

    def test_installer_file_names(self):
        """Test the installer function."""
        mock_site_packages = 'mock/path1/dist-packages'
        mock_executable = 'mock/path2/bin'
        with (
            mock.patch.object(
                __main__.site, 'getsitepackages',
            ) as m_packages,
            mock.patch.object(
                __main__.sys, 'executable',
                os.path.join(mock_executable, 'python'),
            ),
            mock.patch.object(
                __main__,
                '_rewrite_file',
            ) as m_rewrite,
        ):
            m_packages.return_value = [mock_site_packages]

            installer()

        assert m_rewrite.mock_calls == [
            mock.call(f'{mock_site_packages}/pre_commit/__main__.py'),
            mock.call(f'{mock_executable}/pre-commit'),
        ]
