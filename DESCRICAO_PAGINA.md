# Verdict Desk — descrição completa para o build do DoraHacks

## Campo 1 · Short description (a linha sob o título) — 221 chars

Verdict Desk turns an AI agent's decision into evidence a lawyer can file: frozen inputs, a cited bull/bear debate, a deterministic verdict, and a hash-chained record anchored on-chain. Simulated only, never a real order.

## Campo 2 · Corpo (aba Details) — substitui os 4 parágrafos atuais

**Every autonomous agent now makes consequential decisions and leaves no trail a court can rely on. Verdict Desk fixes that: each decision becomes evidence a lawyer can file.**

It reads public market evidence, freezes it into an immutable packet, and runs a structured debate: a bull agent and a bear agent (Mistral LLM plus a deterministic engine — RSI, MACD, Bollinger, ATR, EMA, funding, news tone, and market voices) argue over the same frozen facts. Every claim must cite a specific evidence item by id, and a validator refuses any claim whose cited item does not contain its number. So far the validator has accepted **572 claims and rejected 71 (89% accepted)** — every rejection kept with its reason.

Every decision becomes a dossier, hash-chained to the previous one via RFC 8785 canonical JSON and SHA-256. The live dashboard recomputes every hash in the visitor's own browser; edit one character and the row turns red. A GitHub Action runs the desk every hour for BTCUSDT, ETHUSDT and SOLUSDT — **134 dossiers and counting**, all re-derivable (replay reproduces 100% of published verdicts). The chain head is anchored independently: on Ethereum Sepolia through a Chainlink CRE workflow, and in Bitcoin through OpenTimestamps, hourly, with no wallet.

Key features: frozen evidence packets from keyless public sources (Binance candles, OKX funding, GDELT news, RSS voices; failures recorded as gaps, never faked); citation-enforced debate with rejection logs; per-dossier sensitivity showing which single argument decided the verdict; a **cause-and-effect lab** where removing one argument flips the verdict live; a **printable exhibit for every decision** (evidence custody, each claim beside the evidence text it cites, the recomputed hash, and an explicit statement of what the record does not prove); a **scorecard** that scores every position against later prices with sample sizes and caveats printed; and a **verify page** that checks any record you were handed, in your own browser.

Chainlink CRE: a TypeScript workflow fetches the ledger head under DON consensus, reads the BTC/USD Data Feed on Sepolia, and writes through the CRE forwarder to LedgerAnchor `0x50443D51Db71A61E131B147B1d36aF21d48CDdF7`, which only accepts strictly increasing sequence numbers — an anchored head can never be overwritten. Anchor transaction: https://sepolia.etherscan.io/tx/0x53e5a96312ff3f200f7cb1c1abc0b96313272b5fc59c4bf85a136f6a26c2694d (SUCCESS, block 11964023).

Testing: **283 unit tests** plus browser page smoke tests, all green in CI. Honest about edge: the published backtest of the v1 rules does not profit after fees, and the scorecard publishes the losing rows too. Verdict Desk is a reasoning-and-evidence tool, not a trading edge — a decision becomes a piece of evidence, not a log line. Simulated only; no real order is ever placed.

## Links (sidebar / demo)

- Demo: https://andriyamaro.github.io/verdict-desk/
- Repository: https://github.com/AndriyAmaro/verdict-desk
- Video: https://andriyamaro.github.io/verdict-desk/demo/verdict-desk-demo-narrated.mp4
