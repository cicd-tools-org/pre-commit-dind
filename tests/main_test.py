"""Test the __main__ module."""
from __future__ import annotations

from io import BufferedIOBase
from unittest import mock

from pre_commit_dind import __main__
from pre_commit_dind.__main__ import install


class TestMonkeyPatch:
    """Test the __main__ module."""

    def test_install(self):
        """Test the install function."""

        with mock.patch.object(__main__, 'open') as m_open:
            read_mock = mock.MagicMock(spec=BufferedIOBase)
            read_mock.__enter__.return_value.read.return_value = \
                'from pre_commit.main import main'
            write_mock = mock.MagicMock(spec=BufferedIOBase)
            m_open.side_effect = [
                read_mock,
                write_mock,
            ]

            install()

        read_mock.__enter__.return_value.read.assert_called_once()
        write_mock.__enter__.return_value.write.assert_called_once_with(
            'from pre_commit_dind.main import main',
        )
