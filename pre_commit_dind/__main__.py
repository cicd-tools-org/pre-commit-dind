from __future__ import annotations

import os
import site
import sys


def installer() -> None:
    """Patches pre-commit with pre-commit-dind."""

    target1 = os.path.join(
        site.getsitepackages()[0],
        'pre_commit',
        '__main__.py',
    )
    target2 = os.path.join(
        os.path.dirname(sys.executable),
        'pre-commit',
    )

    _rewrite_file(target1)
    _rewrite_file(target2)

    print('pre-commit-dind was installed successfully!')


def _rewrite_file(target: str) -> None:
    """Rewrites the file at the given target to use pre-commit-dind."""

    with open(target, encoding='utf-8') as f:
        content = f.read()

    with open(target, 'w', encoding='utf-8') as f:
        f.write(
            content.replace(
                'from pre_commit.main import main',
                'from pre_commit_dind import main',
            ),
        )


if __name__ == '__main__':
    installer()
