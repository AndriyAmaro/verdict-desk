# Verdict Desk — descrição final para o DoraHacks (substitui a atual)

## Campo 1 · Short description (a linha sob o título) — 221 chars

Verdict Desk turns an AI agent's decision into evidence a lawyer can file: frozen inputs, a cited bull/bear debate, a deterministic verdict, and a hash-chained record anchored on-chain. Simulated only, never a real order.

## Campo 2 · Corpo (aba Details) — cole substituindo tudo

The special-project direction — a multi-KOL narrative agent — runs on every hourly decision. It watches five public market voices (extensible to 20; Telegram channels natively, X through any public bridge), extracts token, stance, conviction and urgency behind a literal-quote gate, and reports a narrative only when two or more distinct voices agree on the same token and stance (263 convergences recorded so far, across 171 of 179 dossiers). Each convergence becomes a practice position through a transparent rule — 0.5 weight per distinct voice plus 0.5 at high conviction — inside a user-set risk limit capped at 25%.

Every decision is then sealed as evidence a lawyer can file. The agent reads public market evidence, freezes it into an immutable packet, and runs a structured debate: a bull agent and a bear agent (Mistral LLM plus a deterministic engine — RSI, MACD, Bollinger, ATR, EMA, funding, news tone, market voices) argue over the same frozen facts. Every claim must cite a specific evidence item by id, and a validator refuses any claim whose cited item does not contain its number — 887 accepted, 115 refused with reasons kept. Crucially, the verdict itself is deterministic code, not a model's proposal: frozen rules weigh the validated arguments against a threshold and compute entry, size, stop and target, so replay reproduces 100% of the 179 published verdicts. The LLM only writes the arguments; the decision is computed.

Every decision becomes a dossier, hash-chained to the previous one via RFC 8785 canonical JSON and SHA-256. The live dashboard recomputes every hash in the visitor's own browser — edit one character and the row turns red. A GitHub Action runs the desk every hour for BTCUSDT, ETHUSDT and SOLUSDT (179 dossiers and counting), and replay reproduces 100% of published verdicts. The chain head is published where the operator cannot quietly rewrite it: in git history, on Ethereum Sepolia through a Chainlink CRE workflow, and — independently and keylessly — in the Bitcoin blockchain through OpenTimestamps, hourly, with no wallet.

Key features: frozen evidence packets from keyless public sources (failures recorded as gaps, never faked); a citation-enforced debate with rejection logs; per-dossier sensitivity showing which single argument decided the verdict; a cause-and-effect lab where removing one argument flips the verdict live; a printable Certificate of Filing for every decision (each claim beside the evidence text it cites, the recomputed hash, a VERIFIED seal, and an explicit statement of what the record does not prove); a scorecard that scores every position against later prices and prints the losing rows with sample sizes and caveats; and a verify page that checks any record you were handed, in your own browser.

Chainlink CRE: a TypeScript workflow fetches the ledger head under DON consensus, reads the BTC/USD Data Feed on Sepolia, and writes through the CRE forwarder to LedgerAnchor 0x50443D51Db71A61E131B147B1d36aF21d48CDdF7, which only accepts strictly increasing sequence numbers — an anchored head can never be overwritten. Anchor transaction: https://sepolia.etherscan.io/tx/0x53e5a96312ff3f200f7cb1c1abc0b96313272b5fc59c4bf85a136f6a26c2694d (SUCCESS, block 11964023).

Testing: 300 unit tests plus browser page smoke tests, all green in CI. Honest about edge: the published backtest of the v1 rules does not profit after fees, and the scorecard publishes the losing rows too. Simulated only — no real order is ever placed. A practice trade is the legally-defensible reading: the product is a reasoning-and-evidence trail, not a trading bot, and no funds moved means nobody is liable for an autonomous agent's mistake.

## Links (sidebar / demo)

- Demo: https://andriyamaro.github.io/verdict-desk/
- Repository: https://github.com/AndriyAmaro/verdict-desk
- Video (MP4 direto hoje): https://andriyamaro.github.io/verdict-desk/demo/verdict-desk-demo-v4.mp4

### ⬇️ AÇÃO DO ANDRI — trocar o vídeo por embed do YouTube

A página hoje linka um `.mp4` direto; os rivais embutem YouTube (embutido renderiza na página, link direto não). Após subir o `verdict-desk-demo-v4.mp4` no YouTube:

1. No campo **"Video"** do build, cole a **URL do YouTube** (não o link do MP4).
2. Descrição pronta para colar no YouTube:

> Verdict Desk turns an AI agent's decision into evidence a lawyer can file. 77-second narrated demo: frozen market evidence, a cited bull/bear debate, a deterministic verdict, the one-click tamper demo, the cause-and-effect lab, a Certificate of Filing with its on-chain anchor, and the scorecard that publishes the losing rows too. Live: https://andriyamaro.github.io/verdict-desk/ · Repo: https://github.com/AndriyAmaro/verdict-desk · Simulated only — never a real order.
