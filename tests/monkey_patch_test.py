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
        sys.modules.pop('pre_commit_dind.languages.docker', None)

    def test_docker_module_without_monkey_patch(self):
        original = importlib.import_module('pre_commit.languages.docker')
        patched = importlib.import_module('pre_commit_dind.languages.docker')

        assert original != patched

    def test_all_languages_module_without_monkey_patch(self):
        languages = importlib.import_module('pre_commit.all_languages')
        patched = importlib.import_module('pre_commit_dind.languages.docker')

        assert languages.docker != patched

    def test_docker_module_with_monkey_patch(self):
        pre_commit_dind = importlib.import_module('pre_commit_dind.patch')
        pre_commit_dind.monkey_patch()

        original = importlib.import_module('pre_commit.languages.docker')
        patched = importlib.import_module('pre_commit_dind.languages.docker')

        assert original == patched

    def test_all_languages_module_with_monkey_patch(self):
        pre_commit_dind = importlib.import_module('pre_commit_dind.patch')
        pre_commit_dind.monkey_patch()

        languages = importlib.import_module('pre_commit.all_languages')
        patched = importlib.import_module('pre_commit_dind.languages.docker')

        assert languages.docker == patched
