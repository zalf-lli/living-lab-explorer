"""Standalone contract checker for data/climate_color_breaks.json.

Runnable on its own (`python data-pipeline/tests/check_color_breaks.py`) so 08-06 Task 1's
`<automated>` verify can call it directly, and so 08-08's build gate can re-run it after
the breaks are recomputed against final data. Also wrapped by
`test_pipeline_outputs.py::test_climate_color_breaks_contract` so the standing pytest
suite enforces the same contract on every run.

The producer of the artifact this checks is
`data-pipeline/python/compute_climate_color_breaks.py`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from _sources import repo_root  # noqa: E402

# The nine hex stops 08-UI-SPEC.md's Ramp contract locks: four heat, four water, plus the
# diverging ramp's near-zero neutral (C.bg). Transcribed here as the allow-list; no other
# hex value may ever appear in a `colors` list.
PERMITTED_HEX_STOPS = frozenset(
    {
        # heat family (theme.js orangeGhost / orange / orangeDark / orangeDeep)
        "#fce3da",
        "#eb5b25",
        "#dc4b14",
        "#bb3f11",
        # water family (theme.js tealLight / tealMid / teal / tealBg)
        "#00b3ad",
        "#008581",
        "#005754",
        "#00413f",
        # diverging near-zero neutral (theme.js C.bg)
        "#f9fef9",
    }
)

EXPECTED_VARIABLES = {"gdd", "bio1", "bio12", "bio18"}


def check_color_breaks(path: Path) -> None:
    assert path.exists(), (
        f"Missing {path} -- run data-pipeline/python/compute_climate_color_breaks.py first"
    )
    data = json.loads(path.read_text(encoding="utf-8"))

    assert "_meta" in data, "Missing _meta block in climate_color_breaks.json"

    variable_entries = {key: value for key, value in data.items() if key != "_meta"}
    assert set(variable_entries) == EXPECTED_VARIABLES, (
        f"Expected exactly {sorted(EXPECTED_VARIABLES)} variable entries, "
        f"got {sorted(variable_entries)}"
    )

    summary_lines = []
    for variable_id, entry in variable_entries.items():
        assert set(entry) == {"baseline", "change"}, (
            f"{variable_id}: expected 'baseline' and 'change' blocks, got {sorted(entry)}"
        )

        for mode, block in entry.items():
            ramp = block.get("ramp")
            assert ramp in ("sequential", "diverging"), (
                f"{variable_id}/{mode}: ramp must be 'sequential' or 'diverging', got {ramp!r}"
            )
            if mode == "baseline":
                assert ramp == "sequential", (
                    f"{variable_id}/baseline: ramp must always be 'sequential', got {ramp!r}"
                )

            breaks = block.get("breaks")
            colors = block.get("colors")
            assert isinstance(breaks, list) and len(breaks) >= 2, (
                f"{variable_id}/{mode}: breaks must be a list of at least 2 values, got {breaks!r}"
            )
            for index in range(1, len(breaks)):
                assert breaks[index] > breaks[index - 1], (
                    f"{variable_id}/{mode}: breaks not strictly increasing at index {index}: {breaks}"
                )

            assert isinstance(colors, list), f"{variable_id}/{mode}: colors must be a list, got {colors!r}"
            assert len(colors) == len(breaks) - 1, (
                f"{variable_id}/{mode}: len(colors)={len(colors)} must equal "
                f"len(breaks)-1={len(breaks) - 1}"
            )

            expected_band_count = 4 if ramp == "sequential" else 5
            assert len(colors) == expected_band_count, (
                f"{variable_id}/{mode}: expected {expected_band_count} colors for a "
                f"{ramp!r} ramp, got {len(colors)}"
            )

            per_ll_means = block.get("per_ll_means")
            assert isinstance(per_ll_means, dict) and len(per_ll_means) == 5, (
                f"{variable_id}/{mode}: per_ll_means must have exactly 5 entries, got {per_ll_means!r}"
            )

            if mode == "change":
                means = list(per_ll_means.values())
                has_negative = any(value < 0 for value in means)
                has_positive = any(value > 0 for value in means)
                expected_ramp = "diverging" if (has_negative and has_positive) else "sequential"
                assert ramp == expected_ramp, (
                    f"{variable_id}/change: ramp={ramp!r} inconsistent with per_ll_means sign "
                    f"spread {per_ll_means} (expected {expected_ramp!r})"
                )

            for hex_value in colors:
                assert hex_value in PERMITTED_HEX_STOPS, (
                    f"{variable_id}/{mode}: color {hex_value!r} is not one of the nine "
                    "permitted stops locked in 08-UI-SPEC.md"
                )

        summary_lines.append(
            f"{variable_id}: baseline={entry['baseline']['ramp']} change={entry['change']['ramp']}"
        )

    print("[ok] " + "; ".join(summary_lines))


def main() -> None:
    path = repo_root() / "data" / "climate_color_breaks.json"
    check_color_breaks(path)


if __name__ == "__main__":
    main()
