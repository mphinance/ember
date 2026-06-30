# empirical flywheel feeds the score (c73)

Closed the loop the results_tracker ([[forward-results-tracker]], c55) exists for. `build_one`
now reads each name's OWN settled forward record (`results_tracker.by_ticker` ->
`empirical_lift`) and nudges its score by the gap between actual forward hit rate and the
prob_otm the model PREDICTED, bounded to +/- 5 points, never on an AVOID, and surfaced
(`pick.empirical_lift` + `pick.empirical`) so it is auditable, not silent.

**Why this is different from the rescores I refuse.** My standing rule (see
[[critics-dont-override-settled-calls]], [[flag-dont-silently-drop]]) is: do NOT silently
rescore the board on a contestable call (iv-vs-rv in prob_otm, the RoC denominator, the
earnings DTE+1 buffer). Those are measure-theory / policy judgments that belong to Michael. An
empirical lift is NOT that kind of call: it is grounded in the name's OWN realized outcomes vs
its OWN forecasts, it is bounded, it is visible, and GOAL Phase 3 explicitly sanctioned "grade
ADJUSTMENTS." Grounding a score in reality is the opposite of an arbitrary unilateral measure
swap. That is the line: a score change earns the right to ship when it is data-grounded AND
bounded AND visible, not when it is a contestable choice dressed as a fix.

**How to apply:** wire a feedback loop FAIL-OPEN and DORMANT. Today the store has 303 picks but
0 settled, so every lift is 0.0 and the board is unchanged; the flywheel engages on its own as
expiries settle. A loop that needs `>= N` real observations and returns 0 until then ships
safely the day you build it and turns on by itself later, with no second deploy. Open follow-on:
surface the empirical record + lift as a frontend chip on the card (engine + fields ship now;
the page guards on the new fields so a pre-data scan renders unchanged).
