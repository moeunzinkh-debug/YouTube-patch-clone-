"""Allows ``python3 -m advisor`` from the tool directory."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
