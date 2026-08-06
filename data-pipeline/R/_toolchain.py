"""R and Quarto executable discovery for the report-rendering pipeline.

Mirrors `data-pipeline/python/_sources.py::find_rio_bin()`: explicit env-var
override first (only when it actually resolves to something on disk), then
`shutil.which`, then a known-good fallback path, and finally a `RuntimeError`
with an actionable message naming the override.

`sync.py` never imports this module (D-04) — it is only ever imported by
`data-pipeline/R/render_reports.py`, the manual report-render entry point.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def find_quarto_bin() -> str:
    """Locate the Quarto CLI executable.

    Resolution order:
    1. `QUARTO_BIN` env var, when set and the path exists.
    2. `shutil.which("quarto")`.
    3. The known Positron-bundled Windows path.

    Raises `RuntimeError` naming the `QUARTO_BIN` override on failure.
    """
    env_bin = os.environ.get("QUARTO_BIN")
    if env_bin:
        if Path(env_bin).exists():
            return env_bin
        raise RuntimeError(
            f"QUARTO_BIN is set to '{env_bin}' but that path does not exist. "
            "Fix or unset QUARTO_BIN."
        )

    found = shutil.which("quarto")
    if found:
        return found

    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        positron_bundled = (
            Path(local_appdata)
            / "Programs"
            / "Positron"
            / "resources"
            / "app"
            / "quarto"
            / "bin"
            / "quarto.exe"
        )
        if positron_bundled.exists():
            return str(positron_bundled)

    raise RuntimeError(
        "Could not find the Quarto CLI. Install it standalone from "
        "https://quarto.org/docs/get-started/, or set QUARTO_BIN to an "
        "existing quarto executable (e.g. the copy bundled with Positron)."
    )


def find_r_home() -> str:
    """Locate the R installation directory (R_HOME).

    Resolution order:
    1. `R_HOME` env var, when set and the directory exists.
    2. The parent directory of `shutil.which("Rscript")`'s directory.
    3. The highest-versioned `C:/Program Files/R/R-*` directory on Windows.

    A set-but-nonexistent `R_HOME` raises rather than silently falling
    through to a different R. Raises `RuntimeError` naming `R_HOME` on
    failure.
    """
    env_home = os.environ.get("R_HOME")
    if env_home:
        if Path(env_home).is_dir():
            return env_home
        raise RuntimeError(
            f"R_HOME is set to '{env_home}' but that directory does not exist. "
            "Fix or unset R_HOME."
        )

    found = shutil.which("Rscript")
    if found:
        # Rscript lives at <R_HOME>/bin/Rscript(.exe)
        return str(Path(found).resolve().parent.parent)

    program_files_r = Path("C:/Program Files/R")
    if program_files_r.is_dir():
        candidates = sorted(
            (p for p in program_files_r.iterdir() if p.is_dir() and p.name.startswith("R-")),
            key=lambda p: p.name,
            reverse=True,
        )
        if candidates:
            return str(candidates[0])

    raise RuntimeError(
        "Could not find an R installation. Install R >= 4.5 from "
        "https://cran.r-project.org/bin/windows/base/, then either add its "
        "bin directory to PATH or set R_HOME (e.g. "
        "R_HOME=C:\\Program Files\\R\\R-4.5.0)."
    )


def require_toolchain() -> dict:
    """Resolve both Quarto and R, and build a subprocess-ready environment.

    Returns a dict with keys:
    - "quarto": path to the quarto executable
    - "r_home": path to the R installation directory
    - "env": os.environ.copy() with `<r_home>/bin` prepended to PATH and
      R_HOME set, so a subprocess `quarto render` call finds R through knitr
      even when the interactive shell's own PATH does not include it
      (RESEARCH.md Pitfall 1).
    """
    quarto_bin = find_quarto_bin()
    r_home = find_r_home()

    env = os.environ.copy()
    r_bin_dir = str(Path(r_home) / "bin")
    env["PATH"] = r_bin_dir + os.pathsep + env.get("PATH", "")
    env["R_HOME"] = r_home

    return {"quarto": quarto_bin, "r_home": r_home, "env": env}
