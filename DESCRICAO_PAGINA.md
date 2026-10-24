# Verdict Desk — descrição final para o DoraHacks (substitui a atual)

## Campo 1 · Short description (a linha sob o título) — 221 chars

Verdict Desk turns an AI agent's decision into evidence a lawyer can file: frozen inputs, a cited bull/bear debate, a deterministic verdict, and a hash-chained record anchored on-chain. Simulated only, never a real order.

## Campo 2 · Corpo (aba Details) — cole substituindo tudo

The featured direction — a multi-KOL narrative agent — is built in and runs every hour. It watches five public market voices (extensible to 20; Telegram channels natively, X through any public bridge), extracts token, stance, conviction and urgency with a literal-quote gate, reports a narrative only when two or more distinct voices agree (254 convergences recorded), and turns each convergence into a practice position by a transparent rule — 0.5 weight per distinct voice plus 0.5 at high conviction, inside a user-set risk limit capped at 25%.

Every decision is then sealed as evidence a lawyer can file. The agent reads public market evidence, freezes it into an immutable packet, and runs a structured debate: a bull agent and a bear agent (Mistral LLM plus a deterministic engine — RSI, MACD, Bollinger, ATR, EMA, funding, news tone, market voices) argue over the same frozen facts. Every claim must cite a specific evidence item by id, and a validator refuses any claim whose cited item does not contain its number — 805 accepted, 101 refused with reasons. The verdict itself is deterministic code (the arguments' weights against a threshold), so it reproduces exactly on replay; the LLM only writes the citation-validated arguments.

Every decision becomes a dossier, hash-chained to the previous one via RFC 8785 canonical JSON and SHA-256. The live dashboard recomputes every hash in the visitor's own browser — edit one character and the row turns red. A GitHub Action runs the desk every hour for BTCUSDT, ETHUSDT and SOLUSDT (167 dossiers and counting), and replay reproduces 100% of published verdicts. The chain head is anchored independently: on Ethereum Sepolia through a Chainlink CRE workflow, and in Bitcoin through OpenTimestamps, hourly, with no wallet.

Key features: frozen evidence packets from keyless public sources (failures recorded as gaps, never faked); citation-enforced debate with rejection logs; per-dossier sensitivity showing which single argument decided the verdict; a cause-and-effect lab where removing one argument flips the verdict live; a printable Certificate of Filing for every decision (each claim beside the evidence text it cites, the recomputed hash, a VERIFIED seal, and an explicit statement of what the record does not prove); a scorecard that scores every position against later prices with sample sizes and caveats printed; and a verify page that checks any record you were handed, in your own browser.

Chainlink CRE: a TypeScript workflow fetches the ledger head under DON consensus, reads the BTC/USD Data Feed on Sepolia, and writes through the CRE forwarder to LedgerAnchor 0x50443D51Db71A61E131B147B1d36aF21d48CDdF7, which only accepts strictly increasing sequence numbers — an anchored head can never be overwritten. Anchor transaction: https://sepolia.etherscan.io/tx/0x53e5a96312ff3f200f7cb1c1abc0b96313272b5fc59c4bf85a136f6a26c2694d (SUCCESS, block 11964023).

Testing: 299 unit tests plus browser page smoke tests, all green in CI. Honest about edge: the published backtest of the v1 rules does not profit after fees, and the scorecard publishes the losing rows too. Simulated only — no real order is ever placed, because a practice trade is the legally-defensible reading, and no funds moved means nobody is liable for an autonomous agent's mistake.

## Links (sidebar / demo)

- Demo: https://andriyamaro.github.io/verdict-desk/
- Repository: https://github.com/AndriyAmaro/verdict-desk
- Video: https://andriyamaro.github.io/verdict-desk/demo/verdict-desk-demo-v4.mp4
