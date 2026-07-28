"""Bilingual usage-type and development-status semantic contract for BORIS (D-11).

Mirrors the Phase 2.2 soil_semantics.py precedent: both Brandenburg and Hessen publish
their own Bodenrichtwert usage-type vocabularies, and this module is the single place
that harmonizes both into one canonical bilingual (EN/DE) pair before anything reaches
the frontend. It is a pure lookup/transform module -- no network access, no
sources.yaml reads, no filtering of rows (D-05 requires every zone type to survive).

Callers must pass a `state` of "bb" (Brandenburg) or "he" (Hessen) into every resolver
function. The two vocabularies are keyed independently and a code from one state is
never looked up in the other state's table -- 07-RESEARCH.md section 3.2 documents why
a shared-key lookup would silently mis-map (e.g. Hessen's "G" happens to also mean
"commercial" in Brandenburg's scheme, but Hessen's "LW" means nothing in Brandenburg's).

Expected raw input columns for apply_boris_contract(frame, ...), per 07-RESEARCH.md
section 2 (dots in the source WFS field name `nutzung.art` are not valid itertuples
attribute names, so the fetch script producing `frame` is expected to expose it as
`nutzung_art`):
    - bodenrichtwert (float, EUR/m2) -- passed through untouched
    - stichtag (ISO date string) -- passed through untouched, also consulted for
      has_current_value
    - bodenrichtwertNummer (string) -- passed through untouched
    - entwicklungszustand (raw development-status code)
    - nutzung_art (raw usage-type code, or a full GDI-DE codelist href for Brandenburg)
"""

from __future__ import annotations

from datetime import date


CONTRACT_VERSION = "boris-usage-semantics-v1"

# Brandenburg's `nutzung.art` -- GDI-DE national codelist de.adv-online.gid/BR_Art_Nutzung,
# verified live 2026-07-27 (07-RESEARCH.md section 3.1). This is the canonical vocabulary
# target for D-11: both states' raw codes resolve onto this table.
#
# NOTE: 07-RESEARCH.md's prose describes this as a "44-entry" codelist, but the table it
# actually enumerates in section 3.1 has only 42 rows (verified by direct count against the
# live source page). No additional codes could be found elsewhere in the research file, so
# this module transcribes the 42 rows that are actually documented rather than inventing 2
# more to hit the stated round number -- see 07-06-SUMMARY.md Deviations for detail.
BR_ART_NUTZUNG: dict[str, tuple[str, str]] = {
    "1100": ("Residential building land", "Wohnbauflaeche"),
    "1110": ("Small-holdings settlement area", "Kleinsiedlungsgebiet"),
    "1120": ("Pure residential area", "reines Wohngebiet"),
    "1130": ("General residential area", "allgemeines Wohngebiet"),
    "1140": ("Special residential area", "besonderes Wohngebiet"),
    "1200": ("Mixed building land", "gemischte Baufl."),
    "1210": ("Village area", "Dorfgebiet"),
    "1220": ("Village residential area", "Doerfliches Wohngebiet"),
    "1230": ("Mixed-use area", "Mischgebiet"),
    "1240": ("Core/urban-centre area", "Kerngebiet"),
    "1250": ("Urban area", "Urbanes Gebiet"),
    "1300": ("Commercial building land", "gewerbliche Baufl."),
    "1310": ("Commercial area", "Gewerbegebiet"),
    "1320": ("Industrial area", "Industriegebiet"),
    "1400": ("Special-purpose building land", "Sonderbaufl."),
    "1410": ("Special recreation area", "Sondergebiet fuer Erholung"),
    "1420": ("Other special-purpose area", "sonstige Sondergebiete"),
    "1500": ("Public-facility building land", "Baufl. fuer Gemeinbedarf"),
    "2000": ("Agricultural land", "landwirtschaftliche Fl."),
    "2100": ("Arable land", "Acker"),
    "2200": ("Grassland", "Gruenland"),
    "2300": ("Commercial horticulture", "Erwerbsgartenbaufl."),
    "2400": ("Special-crop cultivation", "Anbaufl. f. Sonderkulturen"),
    "2500": ("Vineyard", "Weingarten"),
    "2600": ("Short-rotation coppice / agroforestry", "Kurzumtriebsplantagen, Agroforst"),
    "2700": ("Wasteland / poor land / mountain pasture / moor", "Unland, Geringstland, Bergweide, Moor"),
    "2800": ("Forestry land", "forstwirtschaftliche Fl."),
    "3010": ("Private green space", "private Gruenfl."),
    "3020": ("Allotment garden", "Kleingartenfl."),
    "3030": ("Recreational garden", "Freizeitgartenfl."),
    "3040": ("Campsite", "Campingplatz"),
    "3050": ("Sports facility", "Sportfl."),
    "3060": ("Other private land", "sonstige private Fl."),
    "3070": ("Cemetery", "Friedhof"),
    "3080": ("Water area", "Wasserfl."),
    "3090": ("Airport / airfield", "Flughafen, Flugplaetze"),
    "3100": ("Private parking", "private Parkplaetze"),
    "3110": ("Storage area", "Lagerfl."),
    "3120": ("Extraction land (quarrying/mining)", "Abbauland"),
    "3130": ("Public-facility land (non-buildable)", "Gemeinbedarfsfl., kein Bauland"),
    "3140": ("Special-use area", "Sondernutzungsfl."),
    "9998": ("Not specifiable from source data", "Nach Quellenlage nicht zu spezifizieren"),
}

# Hessen's `nutzung.art` -- approved W-03 map (07-SPIKE.md "Locked Wave-0 Decisions",
# checkpoint answered 2026-07-28). Keyed by the raw Hessen code, valued by the Brandenburg
# canonical code it resolves to. Only the codes the developer explicitly approved appear
# here; nothing is invented. `LW` is deliberately absent -- see the module-level Deviations
# note below and 07-06-SUMMARY.md for why it is NOT mapped to BB 2000 despite
# 07-RESEARCH.md section 3.2's earlier, since-superseded "confirmed" guess.
HE_ART_NUTZUNG: dict[str, str] = {
    "W": "1100",
    "M": "1200",
    "F": "2800",
    "A": "2100",
    "GR": "2200",
    "WA": "1130",
    "G": "1300",
    "KGA": "3020",
    "MI": "1230",
    "FGA": "3030",
    "GB": "1500",
    "GE": "1310",
    "PG": "3010",
    "SO": "1420",
    "MD": "1210",
    "FH": "3070",
    "SPO": "3050",
    "S": "1400",
    "SE": "1410",
    "WR": "1120",
    "GF": "3130",
    "GI": "1320",
    "SN": "3140",
    "SG": "3060",
    "WG": "2500",
    "WB": "1140",
    "MK": "1240",
    "WS": "1110",
    "CA": "3040",
    "FP": "3090",
    "EGA": "2300",
    "LG": "3110",
}

# entwicklungszustand (development status), ImmoWertV taxonomy -- 07-RESEARCH.md section
# 3.3 / 07-SPIKE.md. Keyed by (state, raw_code); both alphabets converge on the same 5
# bilingual pairs. Bauerwartungsland ("E" / "3000") is an ordinary row here, deliberately
# not special-cased -- D-07 shows it like every other zone.
ENTWICKLUNGSZUSTAND: dict[tuple[str, str], tuple[str, str]] = {
    ("bb", "1000"): ("Building-ready land", "Bauland"),
    ("he", "B"): ("Building-ready land", "Bauland"),
    ("bb", "2000"): ("Raw building land", "Rohbauland"),
    ("he", "R"): ("Raw building land", "Rohbauland"),
    ("bb", "3000"): ("Building-expectation land", "Bauerwartungsland"),
    ("he", "E"): ("Building-expectation land", "Bauerwartungsland"),
    ("bb", "4000"): ("Agricultural or forestry land", "Land-/forstwirtschaftliche Flaeche"),
    ("he", "LF"): ("Agricultural or forestry land", "Land-/forstwirtschaftliche Flaeche"),
    ("bb", "5000"): ("Other/special land", "Sonderflaeche"),
    ("he", "SF"): ("Other/special land", "Sonderflaeche"),
}

UNMAPPED_USAGE: tuple[str, str] = ("Unmapped usage type", "Nicht zugeordneter Nutzungstyp")
UNMAPPED_STATUS: tuple[str, str] = ("Unmapped development status", "Nicht zugeordneter Entwicklungszustand")

# W-02 (07-SPIKE.md, checkpoint answered 2026-07-28): rule id "rolling-10-year-window".
# Predicate: max(stichtag) >= (run_year - 10)-01-01, e.g. "2016-01-01" for a 2026 run.
# Maximal map coverage was the stated goal, not alignment to Hessen's biennial vintage
# cadence -- callers must compute `reference` as this rolling cutoff at run time and pass
# it into is_current_value()/apply_boris_contract(), never hardcode a date literal here.
RECENCY_RULE_DOC = (
    "rolling-10-year-window: max(stichtag) >= (run_year - 10)-01-01, "
    "computed fresh at run time (not a hardcoded literal)."
)


def normalise_usage_code(state: str, raw: object) -> str | None:
    """Normalise a raw usage-type code prior to lookup.

    Brandenburg: accepts either a bare numeric code or a full GDI-DE codelist href
    (".../BR_Art_Nutzung/{code}") and returns the trailing path segment.
    Hessen: returns the token uppercased.
    Returns None for empty or None input.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if state == "bb":
        if text.startswith("http://") or text.startswith("https://"):
            return text.rstrip("/").rsplit("/", 1)[-1]
        return text
    if state == "he":
        return text.upper()
    return text


def resolve_usage(state: str, raw: object) -> tuple[str | None, str, str]:
    """Resolve a raw usage-type code to (canonical_code, en, de).

    For "bb", looks the normalised code up directly in BR_ART_NUTZUNG. For "he", maps
    through HE_ART_NUTZUNG first and then into BR_ART_NUTZUNG -- never falls back to
    looking a Hessen code up directly in BR_ART_NUTZUNG, since the two vocabularies share
    letters with different meanings (07-RESEARCH.md section 3.2 anti-pattern). On any
    miss returns (normalised_or_None, *UNMAPPED_USAGE) so the raw code survives as
    provenance. Raises ValueError for a state other than "bb" or "he".
    """
    if state not in ("bb", "he"):
        raise ValueError(f"Unknown BORIS state: {state!r}")

    code = normalise_usage_code(state, raw)
    if code is None:
        return None, UNMAPPED_USAGE[0], UNMAPPED_USAGE[1]

    if state == "bb":
        entry = BR_ART_NUTZUNG.get(code)
        if entry is None:
            return code, UNMAPPED_USAGE[0], UNMAPPED_USAGE[1]
        return code, entry[0], entry[1]

    # state == "he"
    canonical_code = HE_ART_NUTZUNG.get(code)
    if canonical_code is None:
        return code, UNMAPPED_USAGE[0], UNMAPPED_USAGE[1]
    entry = BR_ART_NUTZUNG.get(canonical_code)
    if entry is None:
        return code, UNMAPPED_USAGE[0], UNMAPPED_USAGE[1]
    return canonical_code, entry[0], entry[1]


def resolve_development_status(state: str, raw: object) -> tuple[str, str]:
    """Resolve a raw entwicklungszustand code to (en, de), falling back to UNMAPPED_STATUS.

    Bauerwartungsland ("E" / "3000") is an ordinary row in ENTWICKLUNGSZUSTAND, deliberately
    not special-cased: D-07 includes it like every other zone. Raises ValueError for a
    state other than "bb" or "he".
    """
    if state not in ("bb", "he"):
        raise ValueError(f"Unknown BORIS state: {state!r}")

    if raw is None:
        return UNMAPPED_STATUS
    code = str(raw).strip()
    if not code:
        return UNMAPPED_STATUS
    if state == "he":
        code = code.upper()

    return ENTWICKLUNGSZUSTAND.get((state, code), UNMAPPED_STATUS)


def is_current_value(stichtag: object, reference: object) -> bool:
    """W-02 recency predicate: rolling-10-year-window (see RECENCY_RULE_DOC).

    `stichtag` is the zone's ISO date string (or None). `reference` is the cutoff date the
    caller computed for this run (an absolute rolling cutoff, e.g. "2016-01-01" for a 2026
    run). Returns False for a None, empty, or unparseable stichtag or reference.
    """
    if not stichtag or not reference:
        return False
    try:
        stichtag_date = date.fromisoformat(str(stichtag)[:10])
        reference_date = date.fromisoformat(str(reference)[:10])
    except ValueError:
        return False
    return stichtag_date >= reference_date


def apply_boris_contract(frame, state: str, reference: object):
    """Apply the boris-usage-semantics-v1 contract to `frame` in place, returning it.

    Mirrors soil_semantics.apply_runtime_contract's itertuples-into-parallel-lists-then-
    bulk-assign structure. Never drops a row (D-05: every zone type must be present).
    Preserves the incoming bodenrichtwert, stichtag, and bodenrichtwertNummer columns
    untouched; only adds derived columns.
    """
    if state not in ("bb", "he"):
        raise ValueError(f"Unknown BORIS state: {state!r}")

    usage_type_code: list[str | None] = []
    usage_type_en: list[str] = []
    usage_type_de: list[str] = []
    development_status_en: list[str] = []
    development_status_de: list[str] = []
    has_current_value: list[bool] = []

    for row in frame.itertuples(index=False):
        raw_usage = getattr(row, "nutzung_art", None)
        code, en, de = resolve_usage(state, raw_usage)
        usage_type_code.append(code)
        usage_type_en.append(en)
        usage_type_de.append(de)

        raw_status = getattr(row, "entwicklungszustand", None)
        status_en, status_de = resolve_development_status(state, raw_status)
        development_status_en.append(status_en)
        development_status_de.append(status_de)

        stichtag = getattr(row, "stichtag", None)
        has_current_value.append(is_current_value(stichtag, reference))

    frame["usage_type_code"] = usage_type_code
    frame["usage_type_en"] = usage_type_en
    frame["usage_type_de"] = usage_type_de
    frame["development_status_en"] = development_status_en
    frame["development_status_de"] = development_status_de
    frame["has_current_value"] = has_current_value

    return frame
