from __future__ import annotations

import sys
from pathlib import Path

# Allow `python src/main.py ...` without requiring installation
_SRC_DIR = Path(__file__).resolve().parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from legislative_analytics.application.main import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
