#!/usr/bin/env python3
"""Entry point: ``python3 tools/version-advisor/run.py <command>``."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from advisor.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
