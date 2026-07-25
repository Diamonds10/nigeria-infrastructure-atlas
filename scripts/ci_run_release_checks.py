#!/usr/bin/env python3
"""Run release tests and expose useful failure text as a GitHub annotation."""

from __future__ import annotations

import subprocess
import sys


def github_escape(value: str) -> str:
    return (
        value.replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
    )


def main() -> int:
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr
    print(output, end="")
    if result.returncode:
        detail = output[-6000:] or "Release checks exited without diagnostic output."
        print(
            "::error title=Atlas release checks failed::"
            + github_escape(detail)
        )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
