"""Shared writer for the CHARTS-01 chart_type-discriminated JSON envelope.

This module is the single writer for every per-(layer, Living Lab) chart JSON file
committed under `data/charts/`. It defines two payload shapes that share one envelope:

- ``write_bar_chart`` writes ``chart_type: "bar"`` payloads carrying a ``series`` list.
- ``write_line_chart`` writes ``chart_type: "line"`` payloads carrying ``x_axis`` and
  ``lines`` lists.

``chart_type`` remains an open string at the schema level (D-01) -- nothing prevents a
future producer from writing a third variant -- but only these two values have producers
after Phase 9. No chart-computation script may call ``json.dumps`` directly; every script
must route through ``write_bar_chart`` or ``write_line_chart`` so the envelope's
``sort_keys=True`` serialization (CLAUDE.md) and field shape can never drift between the
five layers.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def write_bar_chart(
    *,
    output_path: Path,
    ll_slug: str,
    layer_id: str,
    unit: dict,
    series: list[dict],
    source: str,
    mock: bool = False,
) -> None:
    payload = {
        "ll_slug": ll_slug,
        "layer_id": layer_id,
        "chart_type": "bar",
        "unit": unit,
        "series": series,
        "mock": mock,
        "source": source,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"[ok] wrote {output_path}")


def write_line_chart(
    *,
    output_path: Path,
    ll_slug: str,
    layer_id: str,
    unit: dict,
    x_axis: list[dict],
    lines: list[dict],
    source: str,
    mock: bool = False,
) -> None:
    payload = {
        "ll_slug": ll_slug,
        "layer_id": layer_id,
        "chart_type": "line",
        "unit": unit,
        "x_axis": x_axis,
        "lines": lines,
        "mock": mock,
        "source": source,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"[ok] wrote {output_path}")
