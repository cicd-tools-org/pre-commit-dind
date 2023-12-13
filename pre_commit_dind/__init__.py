"""Monkey patches pre-commit with DinD support with cgroups version 2."""
from __future__ import annotations

from .patch import monkey_patch

monkey_patch()

from pre_commit import all_languages  # noqa: F401, E402
from pre_commit.languages import docker  # noqa: F401, E402
from pre_commit.main import main  # noqa: F401, E402
