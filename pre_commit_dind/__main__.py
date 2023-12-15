from __future__ import annotations

import os
import site


def install() -> None:
    """Installs pre-commit with DinD support with cgroups version 2."""
    target = os.path.join(
        site.getsitepackages()[
            0
        ], 'pre_commit', '__main__.py',
    )

    with open(target, encoding='utf-8') as f:
        content = f.read()

    with open(target, 'w', encoding='utf-8') as f:
        f.write(
            content.replace(
                'from pre_commit.main import main',
                'from pre_commit_dind.main import main',
            ),
        )

    print('pre-commit-dind was installed successfully!')


if __name__ == '__main__':
    install()
