# Deferred Items — Phase 10

## Repo-wide `npm run format:check` failure (pre-existing, out of scope)

**Found during:** Plan 10-01, Task 1 verification.

**Issue:** `cd app && npm run format:check` reports formatting drift across all 36
tracked files in `app/`, not just the files this plan modified. Root cause: this
Windows checkout has `core.autocrlf=true` and no `.gitattributes`, so every
tracked file has CRLF line endings on disk while Prettier's default
`endOfLine: 'lf'` expects LF. This predates this plan — verified by running
Prettier against files this plan never touched (e.g. `app/src/App.jsx`,
`app/vite.config.js`) and finding the same class of failure there.

**Scope decision:** Per the executor's scope-boundary rule, this is a
pre-existing, repo-wide environmental issue unrelated to plan 10-01's changes
and was not fixed. Every line this plan added or modified was individually
verified against Prettier's expected output (with line endings normalized for
comparison) and found compliant — two DE `compareEmptyBody` strings that
initially exceeded the 100-char printWidth were wrapped to match Prettier's
own line-wrapping convention before commit.

**Recommendation:** A future cleanup task should either add a
`.gitattributes` with `* text=auto eol=lf` (or set `core.autocrlf=false` for
this repo) and then run `npm run format -- --write .` once, in its own
commit, so `npm run format:check` becomes a meaningful gate again. Out of
scope for Phase 10.
