"""Monkey patches pre-commit with DinD support with cgroups version 2."""
from __future__ import annotations

import importlib
import sys

import pre_commit.languages.docker  # noqa: F401


def monkey_patch() -> None:
    """Monkey patch pre-commit with DinD support with cgroups version 2."""

    patched_docker_module = importlib.import_module(
        'pre_commit_dind.languages.docker',
    )

    setattr(
        sys.modules['pre_commit.languages'],
        'docker',
        patched_docker_module,
    )
    sys.modules['pre_commit.languages.docker'] = patched_docker_module
