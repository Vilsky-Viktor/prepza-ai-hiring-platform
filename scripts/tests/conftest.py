"""The scripts' tests find the services' code with the shared library's tests' helper
(`packages/common/tests/service_code.py`), so both see the same files in either layout."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages" / "common" / "tests"))
