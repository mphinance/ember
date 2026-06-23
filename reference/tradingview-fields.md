# reference: TradingView screener fields (for widening the universe)

Source Michael handed me: https://shner-elmo.github.io/TradingView-Screener/fields/stocks.html
The full menu of columns I can filter/sort on via tradingview-screener (no auth).
`wheelforge/universe.py` uses a slice of these; this is the catalog to widen it.

## Liquidity & volume
- `volume`, `average_volume_10d_calc` / `_30d` / `_60d` / `_90d` — share volume
- `relative_volume_10d_calc` — today vs its 10d average (unusual activity)
- `AvgValue.Traded_10d` / `_30d` / `_60d` / `_90d` — average DOLLAR volume (best liquidity gate)

## Price & size
- `close` — price; `market_cap_basic` / `market_cap_calc` — market cap

## Volatility (matters a lot for premium selling)
- `ATR`, `ATRP` — average true range (abs / %)
- `Volatility.D` / `.W` / `.M` — realized volatility daily/weekly/monthly
- `beta_1_year` — beta vs market

## Trend / technical
- `ADX` — trend strength; `Recommend.All` — TV technical consensus rating

## Classification & events
- `sector`, `industry`, `country`, `exchange`
- `earnings_release_date` (last), `earnings_release_next_date` (next — useful to pre-screen
  out names with a print inside my DTE window, before I even pull their chain)

## Ideas for widening universe.py (queued for a future cycle)
- Add a high-IV lane: sort a slice by `Volatility.M` desc to surface rich-premium names.
- Add an unusual-activity lane: `relative_volume_10d_calc` high.
- Use `earnings_release_next_date` to pre-tag the earnings-avoid gate at the universe stage.
- Let Michael pass screen criteria via INBOX (e.g. "scan only high-IV mid-caps").
