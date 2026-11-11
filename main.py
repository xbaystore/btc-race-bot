#!/usr/bin/env python3
"""BTC race bot for make.fun (bars-replay/v1): two-tranche dip buyer.

The bot speaks agent-fun/bars-replay/v1 through the vendored SDK shim
(vendor/makefun_bars.py) and trades one asset, CBBTC, long only.

Strategy (deterministic, standard library only):
- Track the last W=240 closes: their mean and standard deviation give a
  z-score of the latest close; a slow EMA's slope over 24 bars gauges the
  trend so the bot does not catch a falling knife.
- Flat: buy a dip (z <= -2.3) while the trend guard passes, spending 55%
  of the cash. A full round trip pays ~26 bps in fee, slippage and impact,
  so shallow dips are not worth trading; the parameters were chosen by
  stress-testing this exact rule family across synthetic up, sideways and
  crash windows derived from the dev window, not by maximising the dev
  window alone.
- If the dip deepens much further while holding (z <= -3.6), add a second
  tranche of 40% of the starting cash, once per position. In the stress
  tests the late, deep add raised returns in falling and sideways windows
  without hurting the rising one; adding earlier (z <= -3.4) was fragile
  in crashes, so the trigger sits deep.
- Long: sell everything when the price reverts (z >= 0.25), on a 2.0% stop
  below the average entry, on a 3.0% take profit, or after 300 bars.
- Participation fallback: if no order has filled by bar 1000, relax the
  entry once (z <= -1.0, 25% of cash) so the bot is never a no-trade entry
  on the race window; the same exit rules apply. This never triggers on
  the dev window, where the main rule trades early.
- A 15-bar cooldown after each exit keeps the bot from churning.
Every order carries max_slippage_bps=400 against wild jumps. No clock, no
network, no randomness: the same bars always produce the same orders.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
W = 240               # z-score window (bars)
Z_BUY = -2.3          # buy a dip this deep
Z_SELL = 0.25         # sell when reverted to here
EMA_SPAN = 48         # slow trend EMA
SLOPE_SPAN = 24       # bars over which the EMA slope is measured
SLOPE_MIN = -0.006    # do not buy if the EMA fell more than this over the span
SIZE_FRAC = 0.55      # share of cash spent on the first tranche
ADD_Z = -3.6          # add a second tranche if the dip deepens to here
ADD_FRAC = 0.40       # second tranche size, as a share of the starting cash
STOP = -0.020         # stop loss vs average entry
TAKE_PROFIT = 0.030   # take profit vs average entry
MAX_HOLD = 300        # bars
COOLDOWN = 15         # bars after an exit before the next entry
FALLBACK_BAR = 1000   # relax the entry after this bar if nothing has filled
FALLBACK_Z = -1.0
FALLBACK_FRAC = 0.25
MAX_SLIP_BPS = 400

closes = []
ema = None
ema_hist = []
in_pos_since = -1
cooldown_until = -1
bar_no = -1
any_fill = False
start_cash = None
added = False
prev_qty = 0


def on_batch(state, batch):
    global ema, in_pos_since, cooldown_until, bar_no, any_fill
    global start_cash, added, prev_qty
    bar_no += 1
    for f in batch.get("fills", []):
        if f.get("status") == "filled":
            any_fill = True
    if start_cash is None:
        start_cash = state.cash
    close = state.close(SYMBOL)
    if close is None:
        return []
    closes.append(close)
    alpha = 2.0 / (EMA_SPAN + 1)
    ema = close if ema is None else ema + alpha * (close - ema)
    ema_hist.append(ema)

    held = state.positions.get(SYMBOL)
    qty = held.qty if held is not None else 0
    if qty > prev_qty and prev_qty > 0:
        added = True  # a second buy filled while already holding
    prev_qty = qty
    orders = []

    if held is not None and held.qty > 0:
        if in_pos_since < 0:
            in_pos_since = bar_no
            added = False
        entry = held.cost * 10**7 / held.qty  # average entry price (price units)
        pnl = close / entry - 1.0
        z = _zscore()
        if (z is not None and z >= Z_SELL) or pnl <= STOP or pnl >= TAKE_PROFIT \
                or bar_no - in_pos_since >= MAX_HOLD:
            orders.append({"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                           "max_slippage_bps": MAX_SLIP_BPS})
            in_pos_since = -1
            cooldown_until = bar_no + COOLDOWN
            return orders
        if not added and z is not None and z <= ADD_Z:
            notional = int(start_cash * ADD_FRAC)
            if notional > state.cash:
                notional = state.cash
            if notional >= 1_000_000:  # the 1 USDC minimum buy
                orders.append({"side": "buy", "symbol": SYMBOL,
                               "notional_quote_units": notional,
                               "max_slippage_bps": MAX_SLIP_BPS})
        return orders

    in_pos_since = -1
    if bar_no < cooldown_until or len(closes) < W or len(ema_hist) <= SLOPE_SPAN:
        return orders
    z = _zscore()
    if z is None:
        return orders
    slope = ema_hist[-1] / ema_hist[-1 - SLOPE_SPAN] - 1.0
    if slope < SLOPE_MIN:
        return orders
    if z <= Z_BUY:
        frac = SIZE_FRAC
    elif not any_fill and bar_no >= FALLBACK_BAR and z <= FALLBACK_Z:
        frac = FALLBACK_FRAC
    else:
        return orders
    notional = int(state.cash * frac)
    if notional < 1_000_000:  # the 1 USDC minimum buy
        return orders
    orders.append({"side": "buy", "symbol": SYMBOL, "notional_quote_units": notional,
                   "max_slippage_bps": MAX_SLIP_BPS})
    return orders


def _zscore():
    if len(closes) < W:
        return None
    window = closes[-W:]
    mean = sum(window) / W
    var = sum((c - mean) ** 2 for c in window) / W
    std = var ** 0.5
    if std <= 0:
        return None
    return (closes[-1] - mean) / std


if __name__ == "__main__":
    makefun_bars.run(on_batch)
