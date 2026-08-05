"""Manual driver: renders all ten per-Living-Lab, per-language PDF reports.

sync.py NEVER invokes this script (D-04) -- exactly like `python/build_pmtiles.py`, this is a
manual developer step run by hand (see CLAUDE.md's Development Quick Start). Nothing in this
module is imported by sync.py, and no call site exists there.

Usage:
    python data-pipeline/R/render_reports.py                  # all 5 slugs x 2 languages
    python data-pipeline/R/render_reports.py --slug rheingau --lang de
    python data-pipeline/R/render_reports.py --keep-temp       # keep the per-render temp .qmd
"""

from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

R_DIR = Path(__file__).resolve().parent
REPORT_DIR = R_DIR / "report"
TEMPLATE_PATH = REPORT_DIR / "template.qmd"
EXTENSION_DIR = REPORT_DIR / "_extensions" / "ll-explorer-typst"
BRANDS_DIR = EXTENSION_DIR / "brands"

sys.path.insert(0, str(R_DIR.parent / "python"))
sys.path.insert(0, str(REPORT_DIR))

from _sources import repo_root, resolve  # noqa: E402  (path set up above)
from _toolchain import require_toolchain  # noqa: E402
from generate_brands import generate_brand_files  # noqa: E402

LL_LANGS = ("en", "de")
REPORT_PATTERN = "data/reports/report-{slug}-{lang}.pdf"


def load_ll_metadata() -> dict:
    return json.loads(resolve("app/public/data/ll_metadata.json").read_text(encoding="utf-8"))


def load_report_tokens() -> dict:
    return json.loads(resolve("data/report_tokens.json").read_text(encoding="utf-8"))


def cover_metadata(slug: str, lang: str, *, ll_metadata: dict, report_tokens: dict) -> dict[str, str]:
    """Resolves the cover-page title/subtitle/generated-date strings for one (slug, lang)
    render -- the Living Lab's own localized name (title), report_tokens.json's report.subtitle
    (subtitle), and report.generated with {{date}} substituted for today's date (generated).
    Threaded into `quarto render` as plain-string --metadata overrides (D-16, D-11): unlike
    the `brand:` object field (Task 2's Open Question 3 finding), simple string metadata DOES
    thread through this CLI flag correctly -- confirmed live.
    """
    if slug not in ll_metadata:
        raise RuntimeError(f"Unknown Living Lab slug '{slug}' in ll_metadata.json")
    ll = ll_metadata[slug]
    strings = report_tokens["strings"][lang]["report"]

    today = datetime.date.today().isoformat()
    generated = strings["generated"].replace("{{date}}", today)

    return {
        "title": ll[lang]["name"],
        "subtitle": strings["subtitle"],
        "generated": generated,
        "lang": lang,
    }


def default_slugs() -> list[str]:
    """The five Living Lab slugs, read from data/ll_boundaries.geojson -- the same source
    sync.py's sync_charts() uses -- rather than a hardcoded list, so a sixth Living Lab
    added upstream is picked up here automatically."""
    boundaries_path = resolve("data/ll_boundaries.geojson")
    boundaries = json.loads(boundaries_path.read_text(encoding="utf-8"))
    slugs = sorted({feature["properties"]["ll_slug"] for feature in boundaries["features"]})
    if not slugs:
        raise RuntimeError(f"No ll_slug values found in {boundaries_path.relative_to(repo_root())}")
    return slugs


def render_one(
    slug: str,
    lang: str,
    *,
    toolchain: dict,
    ll_metadata: dict,
    report_tokens: dict,
    keep_temp: bool = False,
) -> Path:
    """Renders one (slug, lang) PDF via `quarto render`, returning the output path.

    Brand injection (RESEARCH.md Open Question 3, empirically resolved in Task 2): a bare
    `--metadata brand:<path>` CLI flag does NOT thread into Quarto's brand resolution (live
    error: "attempt to index a string value (field 'brand')"). The working mechanism is a
    document-level `brand:` YAML key, so this function materializes a per-render temporary
    copy of template.qmd with that key inserted, renders the copy, then deletes it (unless
    --keep-temp is set).
    """
    brand_path = BRANDS_DIR / f"{slug}.yml"
    if not brand_path.exists():
        raise RuntimeError(
            f"No brand file for slug '{slug}' at {brand_path}. "
            "generate_brand_files() should have created it -- was it skipped?"
        )

    template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    brand_rel = brand_path.relative_to(REPORT_DIR).as_posix()
    # Insert `brand: "<path>"` as the first line of the YAML frontmatter (right after the
    # opening `---`), leaving every other YAML key untouched.
    lines = template_text.splitlines(keepends=True)
    if lines[0].strip() != "---":
        raise RuntimeError(f"{TEMPLATE_PATH} does not start with a YAML '---' frontmatter fence")
    temp_lines = [lines[0], f'brand: "{brand_rel}"\n', *lines[1:]]
    temp_doc = REPORT_DIR / f"_render-{slug}-{lang}.qmd"
    temp_doc.write_text("".join(temp_lines), encoding="utf-8")

    reports_dir = resolve("data/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    output_name = f"report-{slug}-{lang}.pdf"
    output_path = reports_dir / output_name

    cover = cover_metadata(slug, lang, ll_metadata=ll_metadata, report_tokens=report_tokens)

    # Never a shell string -- an explicit argument list, so a slug/lang value can never be
    # interpreted as anything other than a literal parameter value (T-12-21).
    #
    # Deliberately NO `--to typst`: that flag forces Quarto's plain built-in typst format,
    # silently bypassing the document's own `format: ll-explorer-typst-typst: default` YAML
    # key and therefore this extension's template-partials entirely (confirmed live: with
    # `--to typst`, the compiled .typ source contains zero references to
    # ll-explorer-typst/ll-report, even though Quarto's generic brand-color support still
    # makes the output LOOK plausibly branded -- a false negative this project's first
    # render nearly shipped with). Omitting `--to` lets Quarto resolve the format from the
    # document's own frontmatter, which still produces a PDF (the extension's one
    # contributed format's default output).
    #
    # title/subtitle/generated/lang are plain string --metadata overrides (unlike `brand:`,
    # confirmed live to thread through correctly) -- these localize the cover banner to the
    # Living Lab's own name and the render's language, so the German renders don't show an
    # English cover title/subtitle (D-16).
    args = [
        toolchain["quarto"],
        "render",
        str(temp_doc),
        "-P",
        f"slug:{slug}",
        "-P",
        f"lang:{lang}",
        "--metadata",
        f"title:{cover['title']}",
        "--metadata",
        f"subtitle:{cover['subtitle']}",
        "--metadata",
        f"generated:{cover['generated']}",
        "--metadata",
        f"lang:{cover['lang']}",
        "--output",
        output_name,
    ]

    env = dict(toolchain["env"])
    env["LL_REPO_ROOT"] = str(repo_root())

    result = subprocess.run(args, cwd=str(REPORT_DIR), env=env, check=False)

    rendered_at = REPORT_DIR / output_name
    if not keep_temp:
        temp_doc.unlink(missing_ok=True)

    if result.returncode != 0 or not rendered_at.exists():
        raise RuntimeError(
            f"quarto render failed for slug='{slug}' lang='{lang}' "
            f"(exit code {result.returncode}). Command: {' '.join(args)}"
        )

    reports_dir.mkdir(parents=True, exist_ok=True)
    rendered_at.replace(output_path)

    with output_path.open("rb") as handle:
        header = handle.read(5)
    if header != b"%PDF-":
        raise RuntimeError(
            f"Rendered file for slug='{slug}' lang='{lang}' is not a valid PDF "
            f"(expected %PDF- magic bytes, got {header!r}): {output_path}"
        )

    return output_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render all per-Living-Lab, per-language PDF reports (manual step, D-04)."
    )
    parser.add_argument(
        "--slug",
        action="append",
        dest="slugs",
        help="Living Lab slug to render (repeatable). Defaults to all slugs in "
        "data/ll_boundaries.geojson.",
    )
    parser.add_argument(
        "--lang",
        action="append",
        dest="langs",
        choices=LL_LANGS,
        help="Language to render (repeatable: en, de). Defaults to both.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the per-render temporary .qmd copy (debugging only).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # Fail fast, before any work, if R or Quarto is missing (RESEARCH.md Pitfall 1).
    toolchain = require_toolchain()

    slugs = args.slugs or default_slugs()
    langs = args.langs or list(LL_LANGS)

    generated = generate_brand_files()
    print(f"[report] regenerated {len(generated)} brand file(s) from ll_metadata.json")

    ll_metadata = load_ll_metadata()
    report_tokens = load_report_tokens()

    rendered: list[Path] = []
    for slug in slugs:
        for lang in langs:
            path = render_one(
                slug,
                lang,
                toolchain=toolchain,
                ll_metadata=ll_metadata,
                report_tokens=report_tokens,
                keep_temp=args.keep_temp,
            )
            size = path.stat().st_size
            print(f"[report] rendered {path.relative_to(repo_root())} ({size} bytes)")
            rendered.append(path)

    total_bytes = sum(path.stat().st_size for path in rendered)
    print(f"[report] {len(rendered)} file(s) rendered, {total_bytes} bytes total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
