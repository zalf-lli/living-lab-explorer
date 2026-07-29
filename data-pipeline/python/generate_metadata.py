"""Generate app/public/data/ll_metadata.json (computed half) merged with authored
data/ll_content.json (human-owned half).

This module READS data/ll_content.json (CONTENT_FILE) but must NEVER write it -- it is
human-owned per CLAUDE.md's critical rules. All write paths in this module target
METADATA_FILE only.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"
CONTENT_FILE = DATA / "ll_content.json"
METADATA_FILE = DATA / "ll_metadata.json"
DESTATIS_LL_FILE = DATA / "destatis_ll.json"
CURATED_KPIS_FILE = DATA / "destatis_curated_kpis.json"
DESTATIS_META_FILE = DATA / "destatis_meta.json"
PROTECTED_AREA_KPIS_FILE = DATA / "protected_area_kpis.json"

# Layer tab ids that can carry authored narrative text (mirrors app/src/data/layers.js
# LAYERS[].id). "protected-areas" is an OVERLAYS entry, never a tab, and gets no slot.
NARRATIVE_TABS = ("agriculture", "climate", "economic", "landscape", "soil")
NARRATIVE_SLOTS = ("about", "focus")
NARRATIVE_LANGS = ("de", "en")


def load_ll_content(path: Path = CONTENT_FILE) -> dict[str, dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_json_or_empty(path: Path) -> dict | list:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _deep_merge(computed: object, authored: object) -> object:
    if isinstance(computed, dict) and isinstance(authored, dict):
        merged = {key: deepcopy(value) for key, value in computed.items()}
        for key, value in authored.items():
            merged[key] = _deep_merge(merged.get(key), value) if key in merged else deepcopy(value)
        return merged
    return deepcopy(authored)


def _build_kpi_by_tab(slug: str, destatis_ll: dict, curated_kpis: list, protected_area_kpis: dict | None = None) -> dict:
    """Build the kpiByTab field for a single LL's computed metadata record.

    For KPIs sourced from protected area data (source_host: bfn_wfs), prefer values from
    protected_area_kpis over destatis_ll.
    """
    if protected_area_kpis is None:
        protected_area_kpis = {}

    by_tab: dict[str, list] = {}
    slug_protected = protected_area_kpis.get(slug, {})

    for entry in curated_kpis:
        tab = entry["tab"]
        variable_key = entry["variable_key"]
        # Use protected area KPIs if source is bfn_wfs, otherwise use destatis_ll
        if entry.get("source_host") == "bfn_wfs":
            value = slug_protected.get(variable_key)
        else:
            value = destatis_ll.get(slug, {}).get(variable_key)

        by_tab.setdefault(tab, []).append(
            {
                "key": variable_key,
                "value": value,
                "unit": {"en": entry["unit_en"], "de": entry["unit_de"]},
                "genesisTable": entry["genesis_table"],
                "sourceHost": entry.get("source_host"),
            }
        )
    return by_tab


def _clean_narrative_text(value: object) -> str | None:
    """Normalize an authored narrative string: strip whitespace, map empty/whitespace-only
    or non-string values to None. Never returns "" or the legacy "-" sentinel (D-04)."""
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _build_narrative_by_tab(authored: dict) -> dict:
    """Normalize authored['en'|'de']['narrative'][tab][slot] into the inline-pair contract
    narrativeByTab[tab][slot][lang], matching the region:{en,de} / KPI unit:{en,de} idiom.

    Always emits all five NARRATIVE_TABS and both NARRATIVE_SLOTS for every LL, each with
    both NARRATIVE_LANGS keys, defaulting to None where unauthored (D-03). Iterates the
    module-level constants (not the authored dict's keys) so an unknown authored tab id is
    dropped by construction rather than propagated.
    """
    by_tab: dict[str, dict] = {}
    for tab in NARRATIVE_TABS:
        by_tab[tab] = {}
        for slot in NARRATIVE_SLOTS:
            by_tab[tab][slot] = {}
            for lang in NARRATIVE_LANGS:
                lang_block = authored.get(lang) if isinstance(authored, dict) else None
                narrative = lang_block.get("narrative") if isinstance(lang_block, dict) else None
                tab_block = narrative.get(tab) if isinstance(narrative, dict) else None
                raw_value = tab_block.get(slot) if isinstance(tab_block, dict) else None
                by_tab[tab][slot][lang] = _clean_narrative_text(raw_value)
    return by_tab


def _build_computed_record(
    slug: str,
    authored: dict,
    destatis_ll: dict,
    curated_kpis: list,
    destatis_meta: dict,
    protected_area_kpis: dict | None = None,
) -> dict:
    manager = authored.get("manager") or {}
    return {
        "slug": slug,
        # Regional network manager (name + email). `contact` stays in the output as the
        # flat email alias so existing consumers keep working; manager.email is the
        # single authored source of truth in ll_content.json.
        "manager": {"name": manager.get("name", ""), "email": manager.get("email", "")},
        "contact": manager.get("email") or authored.get("contact", ""),
        "nuts3": authored.get("nuts3", []),
        "kpiByTab": _build_kpi_by_tab(slug, destatis_ll, curated_kpis, protected_area_kpis),
        "narrativeByTab": _build_narrative_by_tab(authored),
        "destatisRetrievedAt": destatis_meta.get("fetched_at"),
    }


def build_metadata(ll_content: dict[str, dict] | None = None) -> dict[str, dict]:
    content = load_ll_content() if ll_content is None else ll_content
    destatis_ll = _load_json_or_empty(DESTATIS_LL_FILE)
    curated_kpis = _load_json_or_empty(CURATED_KPIS_FILE) or []
    destatis_meta = _load_json_or_empty(DESTATIS_META_FILE)
    protected_area_kpis = _load_json_or_empty(PROTECTED_AREA_KPIS_FILE)
    metadata: dict[str, dict] = {}
    for slug, authored in content.items():
        computed = _build_computed_record(slug, authored, destatis_ll, curated_kpis, destatis_meta, protected_area_kpis)
        metadata[slug] = _deep_merge(computed, authored)
    return metadata


def write_metadata(output_path: Path = METADATA_FILE, ll_content: dict[str, dict] | None = None) -> dict[str, dict]:
    metadata = build_metadata(ll_content)
    output_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )
    return metadata


def main() -> None:
    write_metadata()
    print(f"[ok] wrote {METADATA_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
