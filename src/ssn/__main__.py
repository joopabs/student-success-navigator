"""Entry point for `python -m ssn`."""

from __future__ import annotations

import sys

from ssn.cli import main

if __name__ == "__main__":
    sys.exit(main())
