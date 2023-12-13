"""Test the monkey_patch function."""
from __future__ import annotations

import importlib
import sys


class TestMonkeyPatch:
    """Test the monkey_patch function."""

    def setup_method(self):
        sys.modules.pop('pre_commit', None)
        sys.modules.pop('pre_commit.all_languages', None)
        sys.modules.pop('pre_commit.languages.docker', None)
        sys.modules.pop('pre_commit_dind', None)

    def test_docker_module_without_monkey_patch(self):
        module = importlib.import_module('pre_commit.languages.docker')

        assert getattr(module, '_is_in_docker_dockerenv', None) is None
        assert getattr(
            module, '_get_container_id_from_mountinfo', None,
        ) is None

    def test_all_languages_module_without_monkey_patch(self):
        module = importlib.import_module('pre_commit.all_languages')

        assert getattr(module.docker, '_is_in_docker_dockerenv', None) is None
        assert getattr(
            module.docker, '_get_container_id_from_mountinfo', None,
        ) is None

    def test_docker_module_with_monkey_patch(self):
        pre_commit_dind = importlib.import_module('pre_commit_dind.patch')
        pre_commit_dind.monkey_patch()

        module = importlib.import_module('pre_commit.languages.docker')

        assert getattr(module, '_is_in_docker_dockerenv', None) is not None
        assert getattr(
            module, '_get_container_id_from_mountinfo', None,
        ) is not None

    def test_all_languages_module_with_monkey_patch(self):
        pre_commit_dind = importlib.import_module('pre_commit_dind.patch')
        pre_commit_dind.monkey_patch()

        module = importlib.import_module('pre_commit.all_languages')

        assert getattr(
            module.docker, '_is_in_docker_dockerenv',
            None,
        ) is not None
        assert getattr(
            module.docker, '_get_container_id_from_mountinfo', None,
        ) is not None
