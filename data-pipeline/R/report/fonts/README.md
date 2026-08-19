# Report fonts

Font files placed here are installed into the runner's font path by
`.github/workflows/refresh-data.yml` before `render_reports.py` runs, so CI-rendered PDFs
match locally-rendered ones.

Drop the `.ttf` / `.otf` files for the family named in `data/report_tokens.json`'s `font`
field directly in this directory — no subdirectories, the workflow copies a flat glob.
The workflow verifies with `fc-list` that the family is actually visible to fontconfig
afterwards and fails the run if it is not, rather than letting Typst silently substitute a
fallback and restyle all ten committed PDFs.

Currently `report_tokens.json` names **Satoshi**. Before committing font binaries here,
confirm the foundry's license permits redistribution as part of this repository. If it does
not, the alternative is to point `report_tokens.json`'s `font` at a libre family that is
installable from apt on the runner (e.g. an SIL Open Font License family) and adjust the
workflow's font step accordingly.

Local Windows renders read the font from the system font store, not from this directory —
this directory exists for the CI runner, which has no fonts installed beyond its defaults.
