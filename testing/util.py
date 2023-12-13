from __future__ import annotations

import sys

import pytest

xfailif_windows = pytest.mark.xfail(sys.platform == 'win32', reason='windows')
