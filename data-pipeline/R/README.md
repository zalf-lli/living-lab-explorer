# data-pipeline/R/

This directory is a self-contained R + Quarto project. It exists for one purpose: **report
generation** — rendering the per-Living-Lab, per-language PDF factsheets from the same on-disk
JSON/GeoJSON artifacts the rest of `data-pipeline/` already produces. It is not a data-fetching
tier; it never runs `sync.py`'s fetch/build steps, and `sync.py` never invokes anything in here.

`sync.py` does not render reports (D-04). Reports are rendered by hand, on demand, via:

```powershell
python data-pipeline/R/render_reports.py
```

exactly the same manual-invocation contract every `data-pipeline/python/build_*.py` script
already has.

## Required external tools

- **Quarto >= 1.4** (bundles Typst automatically — no separate Typst install needed). Quarto
  orchestrates R chunk execution (via `knitr`), Pandoc, and Typst compilation into the final PDF.
- **R >= 4.5**. Executes the report's code chunks: reads JSON/GeoJSON, builds `ggplot2` maps and
  charts.

`data-pipeline/R/_toolchain.py` discovers both executables and raises an actionable
`RuntimeError` (naming the relevant environment variable) if either is missing or misconfigured.
`render_reports.py` (added in a later plan) imports and calls
`_toolchain.require_toolchain()` before rendering anything.

## The Windows PATH friction point

R is commonly installed on Windows but **not added to PATH** by its own installer, and IDEs like
Positron/RStudio locate it via their own bundled lookup rather than the plain shell PATH. This
means `quarto render` run from a bare PowerShell or Git Bash prompt can fail at the `knitr`
engine step with no R-specific detail, even when R is fully installed
(RESEARCH.md Pitfall 1).

Two fixes, either is sufficient:

1. Set `R_HOME` to your R installation directory, e.g.:
   ```powershell
   $env:R_HOME = "C:\Program Files\R\R-4.5.0"
   ```
2. Or add R's `bin` directory to PATH:
   ```powershell
   $env:PATH = "C:\Program Files\R\R-4.5.0\bin;$env:PATH"
   ```

Similarly, if Quarto is not on PATH (e.g. only the copy bundled with Positron is installed), set
`QUARTO_BIN` to point at it directly:

```powershell
$env:QUARTO_BIN = "$env:LOCALAPPDATA\Programs\Positron\resources\app\quarto\bin\quarto.exe"
```

## Setting up a fresh machine

This project uses [`renv`](https://rstudio.github.io/renv/) to pin exact package versions,
mirroring `data-pipeline/requirements.txt` on the Python side. `data-pipeline/R/renv.lock`
is the committed, reviewable record of every package version the report render needs.

On a fresh machine, with R and Quarto both discoverable (see above), restore the pinned
package library from the project directory:

```r
renv::restore()
```

This installs every package pinned in `renv.lock` at its exact recorded version — no manual
`install.packages()` follow-up is needed.
