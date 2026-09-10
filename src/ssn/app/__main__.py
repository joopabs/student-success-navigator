"""`python -m ssn.app` entry point."""

from __future__ import annotations

import sys

from ssn.app.app import main

if __name__ == "__main__":
    sys.exit(main())
