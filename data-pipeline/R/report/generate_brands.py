"""Generates the five per-Living-Lab brand YAML files from _brand.yml + ll_metadata.json (D-07).

Each output is a FULL copy of _brand.yml with only the ll-primary / ll-primary-dark / ll-outline
palette values replaced by that Living Lab's own color / colorDark / outlineColor. RESEARCH.md
Pitfall 4 is the reason for a full copy rather than a sparse override: Quarto's document-level
brand: key REPLACES the extension's default brand wholesale, it does not merge field by field,
so a sparse per-LL file risks silently losing logo/typography/footer keys the base brand would
otherwise have supplied.

Callable standalone (`python data-pipeline/R/report/generate_brands.py`) for development and for
this plan's own Task 2 verification, and imported by render_reports.py (Task 3) so every real
render regenerates a fresh, in-sync set of brand files rather than trusting stale committed
output. sync.py never imports this module (D-04) -- report generation is a manual developer step.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

REPORT_DIR = Path(__file__).resolve().parent
EXTENSION_DIR = REPORT_DIR / "_extensions" / "ll-explorer-typst"
BASE_BRAND_PATH = EXTENSION_DIR / "_brand.yml"
BRANDS_DIR = EXTENSION_DIR / "brands"


def repo_root() -> Path:
    return REPORT_DIR.parents[2]


def generate_brand_files(ll_metadata_path: Path | None = None) -> list[Path]:
    """(Re)writes brands/<slug>.yml for every Living Lab in ll_metadata.json.

    Returns the list of written paths, one per slug, sorted. Overwrites unconditionally --
    these files are machine-generated and must never be hand-edited (each carries a header
    comment saying so).
    """
    root = repo_root()
    metadata_path = ll_metadata_path or (root / "app" / "public" / "data" / "ll_metadata.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not metadata:
        raise RuntimeError(f"No Living Labs found in {metadata_path}")

    base_text = BASE_BRAND_PATH.read_text(encoding="utf-8")

    BRANDS_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for slug in sorted(metadata):
        ll = metadata[slug]
        # Fresh yaml.safe_load per Living Lab (not a shared dict) so mutating one slug's
        # palette can never leak into another's output.
        brand = yaml.safe_load(base_text)
        brand["color"]["palette"]["ll-primary"] = ll["color"]
        brand["color"]["palette"]["ll-primary-dark"] = ll["colorDark"]
        brand["color"]["palette"]["ll-outline"] = ll["outlineColor"]

        header = (
            "# generated from _brand.yml + ll_metadata.json"
            f"['{slug}'] by data-pipeline/R/report/generate_brands.py -- do not hand-edit.\n"
            "# Regenerate via render_reports.py (D-04) or "
            "`python data-pipeline/R/report/generate_brands.py`.\n"
        )
        body = yaml.safe_dump(brand, sort_keys=False, allow_unicode=True)
        out_path = BRANDS_DIR / f"{slug}.yml"
        out_path.write_text(header + body, encoding="utf-8")
        written.append(out_path)
    return written


if __name__ == "__main__":
    for path in generate_brand_files():
        print(f"[report] generated {path.relative_to(repo_root())}")
