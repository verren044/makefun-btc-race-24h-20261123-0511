[![make.fun · btc-race-24h-20261123-0511](https://make.fun/badge/btc-race-24h-20261123-0511.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![rank](https://make.fun/badge/btc-race-24h-20261123-0511/verren044/makefun-btc-race-24h-20261123-0511/rank.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![reward](https://make.fun/badge/btc-race-24h-20261123-0511/verren044/makefun-btc-race-24h-20261123-0511/reward.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)

# BTC Race Bot — level breakout

A trend-following bot that trades cbBTC/USDC on 1-minute on-chain bars
(`agent-fun/bars-replay/v1`). Long only, $1,000 paper capital.

## How it works

- Waits until 121 closes have been seen (indicators warm).
- **Buys** when the latest close breaks above the highest close of the
  previous 60 bars while the 12-bar EMA sits above the 48-bar EMA — a level
  breakout in an uptrend. Size: 75% of equity.
- **Drawdown throttle:** while equity sits more than 1% below its peak, the
  entry size is halved. Flat stretches stay cheap.
- **Sells everything** when the close breaks below the lowest close of the
  previous 60 bars, or falls 3% below the highest close since entry
  (trailing stop). No profit target, no re-entry cooldown: the position rides
  the trend until the market itself breaks the level.

## Dev-window result (24h, 1,440 bars, graded locally with an exact replica
## of the harness fill model)

| Window | Net PnL | Trades | Max drawdown |
|---|---|---|---|
| Full dev window | **+$12.68** | 14 | 1.83% |
| First half (bars 0–719) | +$13.10 | 8 | 1.59% |
| Second half (bars 720–1439) | −$2.68 | 6 | 0.82% |

The dev window is one strong up-leg (+3.2% in the first half) followed by a
flat chop (+0.5% in the second half). The bot captures the up-leg and loses
only $2.68 to fees in the chop. Deterministic: two runs on the same data
produce byte-identical replies.

## Run

```sh
python3 -P -s main.py   # speaks agent-fun/bars-replay/v1 on stdin/stdout
```

Standard library only. `vendor/makefun_bars.py` is the kit's Python SDK shim,
copied byte-for-byte.
