# BUILD_LOG — btc-race-24h-20261123-0511

## Contest
Race a BTC trading bot live for 24 hours. $50 total ($12 1st). Free entry.
Dev gate: final entry races only if its latest dev grade has net PnL > 0
after all fees. Race window: 24h starting 15 min after the deadline
(18:11 WIB 23 Nov 2026). Guardrails: ≥1 trade, max drawdown ≤ 25%.

## Dev window
1,440 one-minute cbBTC bars, 0 gaps. BTC $58,956.59 → $61,102.18 (+3.64%).
First half +3.22%, second half +0.54% (flat chop). Buy-and-hold on the
window: +$32.17 (1 trade, dd 1.98%) — used only to validate the simulator,
not as the strategy (it fails the gate on any falling window).

## Method
No docker on this machine, so I replicated the harness fill model exactly
in Python (from `harness/harness-src.tar.gz`, `sim/bars/engine.ts`):
constant-product impact `M = 1 + a/D`, fee 4 bps, slippage 2 bps, fills at
the next bar's open, flatten at the last close. Validated: buy-and-hold
through the replica gives +$32.17, matching the hand computation (+$31–32).
Every variant below was then run through the same replica, and the final
`main.py` was run end-to-end as a subprocess against it (hello + 1,440
batches, two runs byte-identical).

## Variants tried (full-window dev PnL, trades, max DD; halves in brackets)

Donchian channel breakout + EMA(12/48) filter, exit on channel-low
breakdown or trailing stop. All figures in USDC, after fees.

| Variant | Full PnL | Trades | Max DD | H1 / H2 |
|---|---|---|---|---|
| N=60, 50% size, trail 2–3% | +4.04 | 14 | 1.79% | +5.00 / −0.95 |
| N=30, 50% size | −10.24 | 27 | 2.50% | +4.98 / −15.12 |
| N=120, 50% size | +2.63 | 7 | 1.57% | +8.27 / −3.11 |
| Tight trailing stops 0.5–1% | −0.95 … −10.36 | 10–22 | 1.1–2.2% | worse both halves |
| Regime filter (2h return > 0.5–1%) | −0.32 … −10.78 | 6–16 | 1.4–2.9% | enters late, near tops |
| Take-profit 2% / time exit 30–60 bars | −0.39 … −33.04 | 18–36 | 1.6–4.7% | churns fees |
| Hourly-aggregated signals | −1.33 … −15.87 | 1–3 | 0.8–1.7% | entries too late |
| N=45, 75% size | +8.62 | 12 | 2.17% | +13.48 / −4.75 |
| **N=60, 75% size + drawdown throttle** | **+12.68** | **14** | **1.83%** | **+13.10 / −2.68** |
| + 120-bar cooldown after exit | +14.00 | 10 | 1.65% | +16.47 / −7.00 |

## What the tests taught
- Tight stops and profit targets bleed: on 1-minute bars every extra round
  trip costs ~26 bps at full size, and noise pullbacks trigger them.
- Return-based regime filters enter late, near tops — they made the flat
  half *worse*, not better.
- The drawdown throttle (halve size while equity is >1% below its peak)
  is the one addition that helped everywhere: it cuts size exactly when
  the market is chopping.
- The 120-bar cooldown raised the full-window PnL but doubled the flat
  half's loss, so it was dropped: fewer, later entries are not worth it
  when the market is flat.

## Final strategy (main.py)
- Donchian N=60 breakout, EMA(12) > EMA(48) filter, 121-bar warmup.
- Entry 75% of equity (37.5% while throttled), max slippage 100 bps.
- Exit on 60-bar-low breakdown or 3% trailing stop below peak close.
- No profit target, no cooldown, no regime filter.

## Final results (real main.py, subprocess, exact-fill harness)
- Full dev: **+$12.68**, 14 trades, max DD 1.83% — passes the dev gate.
- First half: +$13.10, 8 trades, dd 1.59%.
- Second half: −$2.68, 6 trades, dd 0.82%.
- Determinism: two runs produce byte-identical replies (1,440 replies).
- Honest note: the flat second half is slightly negative (−$2.68, 0.27%
  of equity). In a flat market any active strategy pays fees to tread
  water; the throttle keeps that cost small, and the full window is
  solidly positive. The strategy was chosen for few parameters and
  level-based triggers, not for the best single-window number.

## Top-10 bar
Not checked live for this slug before building (dev board is public once
entries land; the bot's dev PnL of +$12.68 is the number to beat on the
race window, not on dev — dev only decides who races).

## Files
- `main.py` — the bot (Python 3.13, stdlib only, vendor SDK shim)
- `vendor/makefun_bars.py` — kit SDK shim, byte-for-byte copy
- `README.md`, `LICENSE` (MIT), `.gitignore`
