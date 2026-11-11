# Build transcript — btc-race-24h-20261111-0801 entry

How this entry was made, in order. The user is Bayu Prasetya (make.fun
@0xby, GitHub xbaystore); the builder is his AI agent "bay" (Muse). The
structured session export (make.fun's documented agent self-export JSON)
is uploaded with the submission; this file is the human-readable summary
of the same session.

1. 2026-11-11 15:13 WIB — The user sent the bounty link and asked the
   agent to continue with it. The agent verified the bounty on its
   official page: $200 in prizes (1st $100, then $27/$15/$13/$10 and
   $7 x5), entries close 11 Nov 2026 12:01 UTC, the bot trades cbBTC on
   1-minute bars with $1,000 of paper money, only entries profitable on
   the frozen dev window race the live 24 hours, and the race window
   alone decides the prizes (guardrails: at least 1 trade, max drawdown
   25%). This bounty is not escrowed; prizes are paid by transfer.
2. The agent downloaded the official kit from make.fun (public, no
   account needed) and read RULES.txt, the protocol schema, the Python
   SDK shim, the competition bundle and the harness source. Protocol:
   newline JSON — a hello (universe, capital, caps, fees, seed), then
   one batch per bar carrying the fills of the previous batch's orders
   and the account, then done; each batch gets exactly one reply with
   its orders. Orders fill at the next bar's open with a 4 bps fee,
   2 bps slippage and constant-product price impact against the bar's
   open depth.
3. With no Docker on the machine, the agent wrote its own grader that
   mirrors the harness fill engine line for line from the kit's harness
   source (integer math, BarsPool chain per open, end-of-window flatten
   at the last close) and drives the real bot process over the dev
   window's 1,440 bars.
4. Bot v1 (frequent mean reversion: z over 90 bars, buy at -1.5, 65%
   size) graded at net PnL -$9.06 over 20 trades: shallow dips do not
   cover the ~26 bps round-trip cost in this choppy, slightly falling
   window (BTC fell about 1.1% across it; buy-and-hold loses ~$13).
5. A parameter sweep over window, entry depth, exit, stop and size
   found a plateau, not a spike: rare deep dips pay. Final parameters:
   W=240, buy z <= -2.4, sell z >= 0.25, stop -2.5%, take profit +3.5%,
   size 50%, plus an EMA trend guard, a 300-bar max hold, a 15-bar
   cooldown, and a participation fallback (one relaxed entry after bar
   1000 if nothing has filled, so the race window always sees a trade;
   it never triggers on the dev window).
6. Bot v2 with those parameters graded through the real subprocess
   grader twice: net PnL +$5.52, 10 trades, max drawdown 0.57%,
   byte-identical results — the dev gate passes with margin.
7. The repository (main.py, vendor/makefun_bars.py unchanged from the
   kit, README.md, LICENSE (MIT), TRANSCRIPT.md, .makefun/owner.json
   naming the account wallet) was published under the user's GitHub
   account; the user submits from his own signed-in browser session.
