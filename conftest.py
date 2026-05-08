"""Project-level pytest configuration.

Currently provides a single fail-loud check: warn (loudly, on every session
start) when pytest is invoked outside the project's pinned `.venv`. This is
deliberately a warning, not a hard fail, so contributors who knowingly run
on a different interpreter are not blocked — but the drift is impossible to
miss.

Rationale: prior rounds of work silently ran `python3 -m pytest` against the
default shell `python3` (brew 3.14 on this machine), which is a different
interpreter than the project's `.venv` (3.11). The tests passed only because
they did not import `mlx_lm`. As soon as the native MLX backend lifecycle
smoke needs the runtime extra, the silent drift becomes a real bug. See
``docs/source-of-truth/python-environment.md`` and
``docs/source-of-truth/python-environment-research.md`` for the rationale
and recommended workflow.
"""

from __future__ import annotations

import sys
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parent
_EXPECTED_VENV = _PROJECT_ROOT / ".venv"


def _running_inside_project_venv() -> bool:
    expected = _EXPECTED_VENV.resolve()
    try:
        prefix = Path(sys.prefix).resolve()
    except OSError:
        prefix = None
    if prefix == expected:
        return True
    try:
        prefix.relative_to(expected)  # type: ignore[union-attr]
    except (AttributeError, ValueError, OSError):
        pass
    else:
        return True
    try:
        executable = Path(sys.executable)
        executable.relative_to(_EXPECTED_VENV)
    except (ValueError, OSError):
        return False
    return True


def pytest_configure(config) -> None:  # type: ignore[no-untyped-def]
    if _running_inside_project_venv():
        return
    msg = (
        "pytest is running outside .venv "
        f"(sys.executable = {sys.executable}). "
        "owlmlx pins Python 3.11 via `.python-version`; native MLX backend "
        "tests that require the optional `runtime` extra will skip. Run "
        "`uv run pytest ...` or `.venv/bin/python -m pytest ...` for the "
        "supported workflow. See "
        "docs/source-of-truth/python-environment.md."
    )
    # Use pytest's own warning channel so it shows in the summary line and
    # is suppressible via `-W ignore::UserWarning` if a contributor really
    # wants the off-venv path.
    config.issue_config_time_warning(UserWarning(msg), stacklevel=2)
