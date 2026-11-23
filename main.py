"""BTC Race Bot — level breakout (Donchian channel + EMA trend filter).

Trades cbBTC/USDC on 1-minute bars (agent-fun/bars-replay/v1). Long only.

Strategy, in one paragraph: wait until the indicators are warm (121 closes),
then buy when the latest close breaks above the highest close of the previous
60 bars while the fast EMA (12) sits above the slow EMA (48) — a level
breakout in an uptrend. Size is 75% of equity, halved while equity sits more
than 1% below its peak (drawdown throttle). Once in, hold at least 30 bars
before any exit: the channel-low / trailing-stop exits are the market's own
levels, but on 1-minute bars noise pullbacks can trip them within a few bars
of entry, and each whipsaw round trip costs ~26 bps — the minimum hold
blocks exactly those exits. Exit the whole position when the close breaks
below the lowest close of the previous 60 bars, or when it falls 3% below
the highest close since entry (trailing stop). No other exits, no re-entry
cooldown, no profit target: the position rides the trend until the market
itself says the level broke.

Why this shape: on the dev window the 24h move is one strong up-leg followed
by a flat chop. Tight stops and profit targets bled money to fees in testing
(every extra round trip costs ~26 bps at full size); regime filters that
demand a confirmed return entered late, near tops. The channel-low exit is
slow but it is the market's own level, and the drawdown throttle is what
keeps flat stretches cheap. A 60-bar cooldown after a losing exit and a
wider Donchian window (90) were both tested and rejected — both lowered
the full-window PnL. The 30-bar minimum hold is the one addition that
helped: it removes two whipsaw exits, lifts the full-window PnL from
+$12.68 to +$15.61, and the result is flat for any hold in 20–45 bars,
so it is a plateau, not a tuned spike. See BUILD_LOG.md for the variants
tested.

Deterministic: no clock, no network, no randomness; the only state is the
closes seen so far. Two runs on the same data produce identical replies.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"

# --- strategy constants (level-based, few parameters, see BUILD_LOG.md) ---
CHANNEL_BARS = 60        # Donchian channel length, in 1-minute bars
EMA_FAST = 12            # fast EMA period (bars)
EMA_SLOW = 48            # slow EMA period (bars)
WARMUP_BARS = 121        # closes needed before the first trade (indicators warm)
ENTRY_FRAC_BPS = 7500    # 75% of equity per entry
TRAIL_BPS = 300          # 3% trailing stop below the peak close since entry
THROTTLE_BPS = 100       # halve size while equity is >1% below its peak
MIN_HOLD_BARS = 30       # minimum bars to hold before any exit (blocks noise exits)
MAX_SLIPPAGE_BPS = 100   # 1% cap on fill vs latest close


class Bot:
    def __init__(self):
        self.closes = []          # closes seen, in order
        self.ema_fast = None      # running EMA values (None until seeded)
        self.ema_slow = None
        self.peak_close = 0       # highest close since entry
        self.equity_peak = 0      # highest equity seen
        self.entry_bar = -1       # closes-count at entry (for the minimum hold)

    def _ema_step(self, price):
        n = len(self.closes)
        if n == EMA_FAST and self.ema_fast is None:
            self.ema_fast = sum(self.closes[-EMA_FAST:]) / EMA_FAST
        elif self.ema_fast is not None:
            k = 2.0 / (EMA_FAST + 1)
            self.ema_fast = price * k + self.ema_fast * (1 - k)
        if n == EMA_SLOW and self.ema_slow is None:
            self.ema_slow = sum(self.closes[-EMA_SLOW:]) / EMA_SLOW
        elif self.ema_slow is not None:
            k = 2.0 / (EMA_SLOW + 1)
            self.ema_slow = price * k + self.ema_slow * (1 - k)

    def on_batch(self, state, batch):
        close = state.close(SYMBOL)
        if close is None:
            return []
        self.closes.append(close)
        self._ema_step(close)
        if state.equity > self.equity_peak:
            self.equity_peak = state.equity

        holding = state.positions.get(SYMBOL)
        qty = holding.qty if holding else 0
        orders = []

        if len(self.closes) < WARMUP_BARS:
            return []
        if self.ema_fast is None or self.ema_slow is None:
            return []

        channel_high = max(self.closes[-CHANNEL_BARS - 1:-1])
        channel_low = min(self.closes[-CHANNEL_BARS - 1:-1])
        trend_up = self.ema_fast > self.ema_slow

        if qty == 0:
            self.peak_close = 0
            if trend_up and close > channel_high:
                frac = ENTRY_FRAC_BPS
                if state.equity < self.equity_peak * (10000 - THROTTLE_BPS) // 10000:
                    frac //= 2
                notional = state.equity * frac // 10000
                if notional >= 1_000_000 and notional <= state.cash:
                    orders.append({
                        "side": "buy",
                        "symbol": SYMBOL,
                        "notional_quote_units": notional,
                        "max_slippage_bps": MAX_SLIPPAGE_BPS,
                    })
                    self.peak_close = close
                    self.entry_bar = len(self.closes)
        else:
            if close > self.peak_close:
                self.peak_close = close
            held = len(self.closes) - self.entry_bar
            trail_hit = close < self.peak_close * (10000 - TRAIL_BPS) // 10000
            if held >= MIN_HOLD_BARS and (close < channel_low or trail_hit):
                orders.append({
                    "side": "sell",
                    "symbol": SYMBOL,
                    "qty": qty,
                    "max_slippage_bps": MAX_SLIPPAGE_BPS,
                })
        return orders


def main():
    bot = Bot()
    makefun_bars.run(bot.on_batch)


if __name__ == "__main__":
    main()
