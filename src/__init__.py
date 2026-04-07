"""Root-level src shim to prioritize this repo's backend/src package.

This avoids importing another project's `src` package when running from repo root.
"""
from pathlib import Path

_backend_src = Path(__file__).resolve().parent.parent / "backend" / "src"

# Make `import src.*` resolve to this project's backend modules first.
if _backend_src.exists() and str(_backend_src) not in __path__:
    __path__.insert(0, str(_backend_src))
