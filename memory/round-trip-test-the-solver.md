---
name: round-trip-test-the-solver
description: c72 — test a numeric solver by round-tripping through its own model, not a hardcoded expected value; and check what's already covered before adding tests
metadata:
  type: feedback
---

c72 closed most of GOAL Phase 3's "tests" line (cover `_iv_from_put`, `iv_history.iv_rank`,
`_compute_changes`, lane-tagging). Two lessons came out of it.

**Round-trip a solver, never hardcode its output.** `_iv_from_put` backs implied vol out of a
real put premium by bisection. The honest test is not "premium X should give IV 0.42" (which just
re-encodes my own arithmetic and rots when `r` or the model changes) — it is: price a put at a
KNOWN vol with the same `_bs_put`, solve it back, assert recovery to <1e-3. The model checks
itself. Same shape works for any invertible numeric (IV, yield, basis).

**Check existing coverage before writing tests.** The roadmap line named four targets, but
lane-tagging (`_merge_lanes`) was ALREADY covered in `universe._selftest`. I only added what was
genuinely uncovered: the IV solver + the `_iv_rank` proxy + `_compute_changes` (all in
`build_site_data._selftest`), and a brand-new `iv_history._selftest` (the module had none).

**Why:** the numbers these guard (prob_otm, VRP/richness, the since-last-scan diff, iv-rank) are
exactly what Michael trades on; a silent regression there misleads an entry.
**How to apply:** new pure function -> add asserts to that module's `_selftest()` (every module
has one, run via `python -m wheelforge.<mod>`); a stateful module (SQLite) -> point its store at a
tempfile in the test, never the real gitignored DB. See [[forward-results-tracker]].
