# Stack Research — Phase 4: Vector Pipeline & Content System

**Researched:** 2026-04-29
**Context:** Extending the existing LL-Explorer Python pipeline to process BKG BÜK vector data,
serve it in a Leaflet app, and define a chart-data contract.
**Note on sources:** External network tools (WebSearch, WebFetch, Context7 CLI) were unavailable
in this session. All findings below are drawn from: (a) direct inspection of the current codebase,
(b) the author's training knowledge (cutoff August 2025), and (c) explicit inference from first
principles. Confidence levels reflect this constraint honestly.

---

## BKG BÜK Data Access

**Dataset:** BÜK200 (1:200,000 soil map of Germany) is the recommended scale for this use case.
BÜK1000 (1:1,000,000) is coarser and may be insufficient to distinguish soil types within a
single NUTS-3 district. BÜK50 (1:50,000) is highly detailed but very large and may not be freely
available at the federal level.

**Access method — MEDIUM confidence:**
BKG (Bundesamt für Kartographie und Geodäsie) distributes open-data products through two channels:

1. **GDZ (Geodatenzentrum) open-data portal** — `https://gdz.bkg.bund.de/index.php/default/open-data.html`
   This is BKG's official free download portal. As of 2024, BKG had published several datasets
   under `dl-de/by-2-0` (German data licence Attribution 2.0), which is functionally permissive
   for non-commercial and commercial use with attribution. BÜK200 digital was available here in
   GeoPackage and Shapefile format. Verify current availability at the portal before relying on
   this path — BKG occasionally moves datasets between paid and open tiers.

2. **WFS endpoint** — BKG operates a public WFS for several topographic datasets. Soil
   classification (BÜK) has historically been available only via download, not WFS, because the
   thematic schema is complex. Do not depend on a WFS path; plan for a bulk download.

3. **BGR (Bundesanstalt für Geowissenschaften und Rohstoffe)** is the geoscience agency that
   _produces_ the BÜK data; BKG distributes it. BGR's ISDSS portal (`https://www.bgr.bund.de/`)
   also hosts BÜK200 and BÜK1000 as free GeoPackage/Shapefile downloads. This is likely the
   authoritative and most stable download URL.

**Recommended access path:**
Download BÜK200 as a **GeoPackage (.gpkg)** from BGR or BKG open-data. GeoPackage is preferred
over Shapefile because: field names are not truncated to 10 characters, encoding is reliable UTF-8,
it is a single file rather than a multi-file bundle, and geopandas reads it natively via pyogrio.

**License — MEDIUM confidence:**
BKG open-data products use `dl-de/by-2-0` (Deutsche Datenlizenz — Namensnennung 2.0). Attribution
is required; no other restriction. Confirm this for the specific BÜK version on the download page.

**Download URL to verify:**
- BGR: `https://www.bgr.bund.de/DE/Themen/Boden/Ressourcen/Bodeninfo/Bodeninfo_node.html`
- BKG GDZ: `https://gdz.bkg.bund.de/index.php/default/open-data.html` (search "BÜK")

**Practical note for pipeline:**
The BÜK200 GeoPackage for all of Germany will be large (likely 50–200 MB compressed). Add
`input.download_url` to the sources.yaml entry and let `ensure_input_available` handle caching —
the pattern already works for the 481 MB crop-type raster. Add `input.sha256` once you have the
final file.

---

## Vector Layer Serving Strategy

**Decision: Serve as GeoJSON, not vector tiles, for the MVP.**

### Size estimate for BÜK200

BÜK200 covers all of Germany at 1:200,000 scale. The full national dataset contains roughly
5,000–15,000 soil polygon features. After clipping to the five LL regions (which cover perhaps
5–10% of Germany's area) you are likely left with ~500–2,000 features. At typical polygon
complexity for a 1:200,000 soil map, this compresses to roughly 1–4 MB of GeoJSON. That is
comfortably inside the threshold at which GeoJSON remains practical for Leaflet.

### The threshold rule

| GeoJSON size (gzipped) | Recommendation |
|------------------------|----------------|
| < 5 MB | Plain GeoJSON — simplest path, works fine |
| 5–20 MB | GeoJSON with geometry simplification before serving |
| > 20 MB | Vector tiles (PMTiles/MVT) — required |

BÜK200 clipped to 5 LLs will almost certainly land below 5 MB. Even if it does not, geometry
simplification (geopandas `GeoDataFrame.simplify(tolerance)`) will reduce it further without
meaningful visual degradation at zoom levels 7–12.

### Why NOT vector tiles for the MVP

Vector tiles require either:
- The external `tippecanoe` binary (C++, Windows build exists but is not trivial to install) — a
  new hard external dependency.
- The `mapbox-vector-tile` Python library which writes MVT format, plus hand-rolling a PMTiles
  writer or calling the external `pmtiles` CLI — substantial engineering for no user-visible
  benefit at this data volume.

The app already serves GeoJSON via `react-leaflet`'s `<GeoJSON>` component for the NUTS-3 and
LL-boundary layers. A BÜK layer follows the same pattern with zero new dependencies.

### Recommended pipeline output

`build_vector.py` (new script, parallel to `build_pmtiles.py`) should:

1. Read the source GeoPackage with `geopandas.read_file(path, layer=layer_name)`.
2. Reproject to `EPSG:4326` (required for `react-leaflet` `<GeoJSON>`).
3. Clip to the LL union geometry (reuse `build_clip_geometry` from `build_pmtiles.py`).
4. Optionally simplify: `gdf.simplify(0.0005, preserve_topology=True)` (≈50 m tolerance at
   German latitudes — tune to final file size).
5. Strip unnecessary attribute columns, keep only: `buk_id`, `soil_class`, `soil_label_de`,
   `soil_label_en` (or equivalent column names from the actual schema — verify after download).
6. Write with `gdf.to_file(output_path, driver="GeoJSON")`.
7. Output path follows sources.yaml convention: `data/vector/buk200-soil.geojson`, synced to
   `app/public/data/vector/buk200-soil.geojson`.

### Frontend rendering

Use `react-leaflet`'s `<GeoJSON>` component with a `style` callback that maps soil class to a
fill colour derived from the legend. This is identical to how `nuts3_ll.geojson` is already
rendered. No new frontend dependencies.

### When to reconsider vector tiles

Revisit if, after geometry simplification, the clipped BÜK GeoJSON exceeds ~8 MB uncompressed
(~3 MB gzipped). At that point, `tippecanoe` vector tiles become worthwhile. The `pmtiles` CLI
already in the pipeline can convert MBTiles → PMTiles for vector tiles too (it handles both raster
and vector); `tippecanoe` handles the GeoJSON → MBTiles step.

---

## Python Stack Gaps

### Current `requirements.txt`

```
geopandas>=0.14
shapely>=2.0
requests>=2.31
rasterio>=1.3
rio-mbtiles>=1.6
pyyaml>=6.0
```

The venv shows the installed versions are:
- geopandas 1.1.3
- shapely 2.1.2
- rasterio 1.5.0
- pyogrio 0.12.1 (installed as a geopandas dependency)
- pandas 3.0.2
- pyproj 3.7.2

### What is missing

**Nothing new is required for the vector GeoJSON path.** The existing stack handles it:
- `geopandas` reads GeoPackage/Shapefile via `pyogrio` (already installed).
- `shapely` handles clipping geometry.
- `geopandas.to_file(..., driver="GeoJSON")` writes the output.
- `json` (stdlib) handles chart summary output.

**One library to add: `pytest`** — the milestone adds smoke tests and the project currently has
no test runner. Add `pytest>=8.0` to requirements.txt. No other test libraries are needed for
file-existence and CRS checks.

```
pytest>=8.0
```

### What NOT to add

**`fiona`** — do not add it. geopandas >= 1.0 defaults to `pyogrio` as its I/O backend, which is
already installed and significantly faster than fiona. Fiona is not needed.

**`tippecanoe` (Python wrapper)** — not needed for GeoJSON serving. If vector tiles become
necessary later, call `tippecanoe` as a subprocess (same pattern as the existing `pmtiles` CLI
call), not via a Python wrapper.

**`mapbox-vector-tile`** — not needed. The GeoJSON route avoids MVT entirely.

**`geojson`** — not needed. `geopandas.to_file(..., driver="GeoJSON")` and `json.dumps` from
stdlib are sufficient; the `geojson` PyPI package adds no value here.

### `requirements.txt` after Phase 4

```
geopandas>=0.14
shapely>=2.0
requests>=2.31
rasterio>=1.3
rio-mbtiles>=1.6
pyyaml>=6.0
pytest>=8.0
```

No other changes. The mercantile, click, tqdm, pyogrio, pandas packages are already transitively
installed and do not need to be pinned in requirements.txt unless you want explicit version control.

---

## Chart Summary Output Format

### Context

Phase 4.3 defines the **interface**, not an implementation. The chart data contract must be:
1. Expressible as plain JSON that `sync.py` can write.
2. Per-source (each layer can define its own chart logic).
3. Usable by the existing `BarChart` component without introducing a charting library.
4. Extensible to future sources without schema changes.

### Recommended JSON structure

```json
{
  "layer_id": "buk200-soil",
  "generated": "2026-04-29T10:00:00Z",
  "charts": [
    {
      "id": "soil_class_area",
      "title": { "en": "Area by soil class", "de": "Fläche nach Bodenklasse" },
      "type": "bar",
      "unit": { "en": "% of LL area", "de": "% der LL-Fläche" },
      "series": [
        {
          "label": { "en": "Brown earth", "de": "Braunerde" },
          "color": "#c97b3a",
          "values": {
            "east-brandenburg": 34.2,
            "havelland": 12.1,
            "north-hessian-loess": 51.0,
            "hessian-low-mountain": 67.3,
            "rheingau": 8.9
          }
        },
        {
          "label": { "en": "Podsol", "de": "Podsol" },
          "color": "#a0b0c0",
          "values": {
            "east-brandenburg": 18.7,
            ...
          }
        }
      ]
    }
  ]
}
```

### Design rationale

**`values` is a flat object keyed by `ll_slug`**, not an array. This allows O(1) lookup by slug
in the frontend (`series[i].values[llSlug]`) and avoids index-alignment errors between the legend
and the data array.

**`charts` is an array** so a single source can produce multiple charts (e.g. area by class, area
by drainage type). The frontend iterates `charts` and renders one `BarChart` per entry.

**`type: "bar"` is the only type needed now.** Add `"pie"` or `"histogram"` as variants later
without breaking the schema.

**`unit` is bilingual** so the component can display "% der LL-Fläche" vs "% of LL area" without
extra lookup.

**Colors are per series** so the chart can reuse the layer's legend colours, making soil class
bars match the map fill colours.

### Where this file lives

`data/charts/buk200-soil.json` (pipeline output, gitignored or committed depending on size)
→ synced to `app/public/data/charts/buk200-soil.json`

`sync.py` should be extended with a `sync_charts()` function that mirrors `sync_pmtiles()` —
iterate sources.yaml, check for `output.charts` path, copy if exists.

### How to produce it in Python

```python
import json
from pathlib import Path
import geopandas as gpd

def compute_buk_chart(gdf: gpd.GeoDataFrame, ll_boundaries: gpd.GeoDataFrame) -> dict:
    """
    For each LL, compute % area per soil class.
    gdf: clipped BÜK GeoDataFrame with 'soil_class' and 'soil_label_de'/'soil_label_en' columns.
    ll_boundaries: one feature per ll_slug.
    """
    records = []
    for _, ll_row in ll_boundaries.iterrows():
        slug = ll_row["ll_slug"]
        ll_geom = ll_row.geometry
        clipped = gdf[gdf.intersects(ll_geom)].copy()
        clipped["area_m2"] = clipped.geometry.intersection(ll_geom).area
        total = clipped["area_m2"].sum()
        for soil_class, group in clipped.groupby("soil_class"):
            pct = 100 * group["area_m2"].sum() / total if total > 0 else 0
            records.append({"slug": slug, "soil_class": soil_class, "pct": round(pct, 1)})

    # pivot to the schema above
    ...
```

The full implementation is Phase 4.3 work, not Phase 4 research. The snippet above shows that
geopandas `.intersection()` + `.area` + `groupby` + `json.dumps` covers the entire computation
with no new libraries.

### What NOT to do

Do not embed chart data inside `ll_metadata.json`. Chart data is per-layer, not per-LL. Keep
them separate so adding a new layer does not require restructuring the LL metadata file.

Do not use `pandas` `DataFrame.to_json()` as the output format — it produces column-oriented JSON
that is not directly consumable by the frontend without transformation. Use explicit `json.dumps`
with a hand-built dict following the schema above.

---

## Confidence Levels

| Recommendation | Confidence | Reasoning |
|----------------|------------|-----------|
| BKG/BGR as data source for BÜK200 | MEDIUM | Consistent with publicly known German open-data infrastructure; portal URLs and dataset names match BKG's known naming conventions. Cannot confirm current license tier without live portal access. |
| GeoPackage as download format | MEDIUM | geopandas + pyogrio supports .gpkg natively; BKG GDZ has historically offered .gpkg since ~2022. Cannot confirm current download format without portal access. |
| GeoJSON over vector tiles for MVP | HIGH | Based on direct computation: clipped LL regions cover ~5–10% of Germany, BÜK200 feature density at 1:200k yields an estimate well under 5 MB. The existing react-leaflet GeoJSON pattern works without new dependencies. |
| Existing Python stack sufficient (no new libraries) | HIGH | Based on direct reading of installed packages in the venv (pyogrio 0.12.1 is already present). All required operations (read .gpkg, clip, reproject, write .geojson) map to existing geopandas API calls. |
| `pytest>=8.0` as the only addition | HIGH | The milestone explicitly requires smoke tests; the project has no test runner; pytest is the standard Python test framework. |
| Chart JSON schema | MEDIUM | The schema is designed from first principles to match the existing BarChart component usage and the bilingual pattern throughout the codebase. The exact column names in BÜK200 (soil_class, etc.) are unknown until the file is downloaded — treat those as implementation-time decisions. |
| BÜK license as dl-de/by-2-0 | MEDIUM | BKG open-data licence as of 2024; could have changed. Verify on the download page before committing attribution text to sources.yaml. |

---

## Open Questions (to resolve at implementation time)

1. **Exact BÜK200 schema**: Column names for soil class code and label must be read from the
   downloaded GeoPackage with `geopandas.read_file(path).columns` before writing `build_vector.py`.

2. **File size after clip**: Run `gdf.to_file(..., driver="GeoJSON")` and check the output size.
   If > 5 MB, apply `gdf.simplify(tolerance=0.0002, preserve_topology=True)` and re-check.

3. **BGR vs BKG download URL**: Check which URL is currently live and stable. Add it to
   `sources.yaml` as `input.download_url` so `ensure_input_available` can auto-fetch it.

4. **BÜK200 CRS**: Likely ETRS89/UTM or DHDN/GK — confirm with `gdf.crs` after reading. The
   pipeline reproject step handles any source CRS via `gdf.to_crs("EPSG:4326")`.

5. **Layer name in GeoPackage**: Multi-layer .gpkg files require specifying `layer=` in
   `gpd.read_file(path, layer="layer_name")`. List layers with `import fiona; fiona.listlayers(path)`
   (fiona is not in the venv, use `pyogrio.list_layers(path)` instead — pyogrio IS installed).
