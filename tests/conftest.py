"""Test configuration shared across the suite."""

import sys
from pathlib import Path

from hardware_stubs import install_stub_modules

install_stub_modules()

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
