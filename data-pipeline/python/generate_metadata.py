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


def _build_computed_record(
    slug: str,
    authored: dict,
    destatis_ll: dict,
    curated_kpis: list,
    destatis_meta: dict,
    protected_area_kpis: dict | None = None,
) -> dict:
    return {
        "slug": slug,
        "contact": authored.get("contact", ""),
        "nuts3": authored.get("nuts3", []),
        "mock": authored.get("mock", False),
        "kpiByTab": _build_kpi_by_tab(slug, destatis_ll, curated_kpis, protected_area_kpis),
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
