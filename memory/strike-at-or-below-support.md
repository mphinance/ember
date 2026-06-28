---
name: strike-at-or-below-support
description: a sold put's strike must sit AT or BELOW the support you trust to hold, never the closer-but-higher strike above it
metadata:
  type: project
---

When picking the put strike off a live chain, "nearest to target" is not enough: an
abs-nearest sort over `strike <= spot` can land on a strike ABOVE the computed support
(e.g. support $461.50, listed $460/$462.50 -> picks $462.50, the closer one). That sells
above the level you are trusting to hold. The rule: filter to `strike <= target * 1.002`
(0.2% tol so a strike right at target rounds through), pick nearest within that, and only
fall back to the nearest sub-spot strike when nothing lists at/below a deep target.

**Why:** selling a CSP is a bet price holds your strike; a strike above support is a worse
bet than the support pick Michael actually wants. On-thesis correctness, not cosmetics.

**How to apply:** `build_site_data._strike_at_or_below(strikes, target, spot)` is the pure,
tested helper (c51). Reuse it for any strike pick; keep the at/below-then-fallback shape so
a sparse/deep chain never blanks a name (the site-never-blank invariant). See
[[critics-dont-override-settled-calls]] — this one was a real bug, acted on; ticked calls
like the RoC denominator are not.
