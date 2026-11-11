# BTC Race Bot — make.fun bounty entry

Entry for make.fun bounty **"Race a BTC trading bot live for 24 hours"**
(btc-race-24h-20261111-0801), by **Bayu Prasetya (0xby)** —
https://make.fun/bounty/btc-race-24h-20261111-0801

## What it does

`main.py` (Python 3, standard library only) trades CBBTC against USDC in
the bars-replay/v1 protocol, speaking through the kit's Python SDK shim
vendored unchanged at `vendor/makefun_bars.py`. It reads one batch per
1-minute bar (the bar's OHLC and pool depth) and answers with orders that
fill at the next bar's open.

## Strategy

Deep-dip mean reversion with a trend guard:

- A z-score of the latest close over a 240-bar window; a slow EMA's slope
  over 24 bars must not be in a steep slide.
- Buy only a deep dip (z <= -2.4) with 50% of the cash — a round trip pays
  roughly 26 bps in fee, slippage and price impact, so shallow dips are
  deliberately ignored.
- Sell on reversion (z >= 0.25), a 2.5% stop, a 3.5% take profit, or
  after 300 bars; a 15-bar cooldown follows each exit.
- If no order has filled by bar 1000, one relaxed fallback entry
  (z <= -1.0, 25% of cash) guarantees the bot trades at least once on
  the race window.

Graded locally on the kit's dev window with a fill engine mirrored from
the harness source: **net PnL +$5.52 on $1,000, 10 trades, max drawdown
0.57%**, byte-identical across two runs. The full build session is in
`TRANSCRIPT.md`; the structured session export is uploaded with the
submission.

## Run it

The harness runs it as `python3 -P -s main.py`; it reads hello, batch
and done lines on stdin and replies with orders on stdout.

## License

MIT — see `LICENSE`.
