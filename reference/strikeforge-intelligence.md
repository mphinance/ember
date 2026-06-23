# reference: StrikeForge intelligence worth porting (premium-sell only)

Michael asked what in StrikeForge helps WheelForge. Answer: a short, selective list.
StrikeForge does a LOT that is NOT WheelForge's job (full-chain X-ray, payoff calc,
multi-leg, buy/LEAPS/directional lenses, deep dealer-gamma). Leave that there. Port only
what makes a CSP SELLER's read better. READ-ONLY scripture; port the logic into my own
clean modules. Paths under `…/GitHub/StrikeForge/scanner/`.

## 1. Put skew — a real premium-sell signal I lack (surface.py)
`surface.py::_compute_skew_slope` = 25-delta PUT IV minus 25-delta CALL IV (a single
chain scalar). Rich put skew = the market is paying up for downside = good for a put
SELLER. Also `_iv_percentile_per_side` (where this put's IV sits within the put side).
- PORT: pull a ~25-delta CALL too (I already pull a put), compute put-skew, and let it
  lift the richness/setup when puts are bid up vs calls. Cheap (one extra chain point).

## 2. Tail / gap risk — the put seller's actual danger (tail_risk.py)
`compute_tail_risk(row, ohlcv, em, spot)` -> `gap_risk_score [0,100]`, `tail_percentile`.
The read: "if you sold this, what does a single ATR-sized gap DOWN do." My `safety` factor
is only a lognormal prob-OTM (N(d2)) which assumes thin tails. Real names gap. A
disciplined seller cares about the tail, not the average.
- PORT: an `atr_proximity` / gap-risk haircut on the safety factor from the OHLCV I
  already pull (ATR vs the cushion to the strike, plus the worst historical gap). Names
  that gap hard should score LESS safe even at the same prob-OTM.

## 3. OI walls + max pain — real support + the chart walls Michael wanted (structure.py)
`structure.py::max_pain(chain_oi)` and `oi_walls(chain_oi, spot)`: heaviest PUT OI below
spot = support wall, heaviest CALL OI above = resistance, plus spot-vs-walls / spot-vs-max-
pain reads. This is the UPGRADE to the chart "walls" Michael asked about: I told him I
could not do gamma walls because I pull one put, but if I pull the chain's OI (all strikes,
one cheap call per name) I CAN do OI walls, which are the useful version.
- PORT: pull the chain's open interest per name, compute the put-wall support + max pain,
  (a) DRAW them on the chart as real walls next to the Keltner ones, and (b) prefer selling
  the put just UNDER the put-wall support. Highest payoff, most data work (pull more chain).

## 4. Market regime gate — "is today a day to sell premium" (market_weather.py)
`market_weather.py`: VIX vs VIX3M term structure. Backwardation (VIX > VIX3M) = stress =
maybe do not sell into it today. StrikeForge uses it ONLY as a non-blocking 0DTE-avoid
gate; per-name math never depends on it.
- PORT (optional, last): one cached VIX/VIX3M pull -> a small market-regime banner on the
  page ("calm, sell" vs "stressed, be picky"). Fail-open, never gates a per-name score.

## What to SKIP (StrikeForge's lane, not mine)
Full-chain X-ray grading, the payoff calculator, multi-leg structures, the buy/LEAPS/
directional lenses, the deep GEX dealer-positioning (gamma flip etc.). Different product.
The OI walls (3) are the only slice of the structure/gex machinery a CSP seller needs.
