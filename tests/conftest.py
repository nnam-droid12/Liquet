"""Shared pytest fixtures for Liquet test suite."""

import sys
from pathlib import Path

# Ensure project root is on the path for all tests
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
