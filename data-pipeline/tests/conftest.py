from __future__ import annotations

import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


# Add pipeline modules to path so tests can import _sources, fetch_protected_areas, etc.
sys.path.insert(0, str(repo_root() / "data-pipeline" / "python"))

LL_SLUGS = [
    "east-brandenburg",
    "havellandisches-luch",
    "north-hessian-loess",
    "hessian-low-mountain",
    "rheingau",
]
