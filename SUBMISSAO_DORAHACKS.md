# Verdict Desk: DoraHacks Submission Draft

> **Project name:** Verdict Desk
> **Track:** BLI Legal Tech Hackathon 2, Bounty "Autonomous Agents" (RYO-CHAN)
> **Also submitted for:** Chainlink CRE bounty

---

## Short Description (256 chars)

Audit-grade, replayable AI decisions for market agents. Verdict Desk freezes public market evidence, lets a bull and bear agent argue with citations, and records a simulated position with a hash-chained reasoning trail anyone can verify in their browser.

---

## Links

| Field | URL |
|---|---|
| **Repository** | https://github.com/AndriyAmaro/verdict-desk |
| **Live Demo (GitHub Pages)** | https://andriyamaro.github.io/verdict-desk/ |
| **Demo Video (2 min, no voice)** | https://andriyamaro.github.io/verdict-desk/demo/verdict-desk-demo.mp4 |
| **CRE Documentation** | https://github.com/AndriyAmaro/verdict-desk/tree/main/cre |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.10+ (stdlib only, zero runtime dependencies) |
| **LLM** | Mistral API (free tier, `mistral-small-latest`) via `http.client`, no SDK |
| **Browser verifier** | Vanilla JavaScript (SHA-256 + RFC 8785 canonical JSON in-browser) |
| **Dashboard** | Single-page static HTML, served on GitHub Pages |
| **CI/CD** | GitHub Actions: hourly scheduled workflow appends dossiers, verifies the chain, and redeploys |
| **CRE** | Chainlink CRE SDK (`@chainlink/cre-sdk`), Solidity, MockKeystoneForwarder tests |
| **Data sources** | Binance spot candles (no key), OKX public funding, GDELT news, RSS/Atom feeds |
| **Testing** | 153 unit tests via `unittest`; cross-language canonical JSON test vectors; a Python versus JavaScript check of the live-operation counts |

---

## What Verdict Desk Does

Verdict Desk reads public market evidence, freezes it into an immutable packet, and runs a structured debate: a **bull agent** and a **bear agent** argue over the same frozen facts. Each argument must cite specific evidence items by ID, and a citation validator rejects any claim that does not match the cited data. A **deterministic judge** then sizes a *simulated* position (entry, stop-loss, take-profit) inside declared risk limits.

Every decision becomes a **dossier**, a self-contained record with all evidence, arguments, citations, verdict, and position details, hash-chained to the previous one via RFC 8785 canonical JSON and SHA-256. The resulting ledger is a public, tamper-evident audit trail that anyone can verify.

The live dashboard loads the ledger and recomputes every hash in the viewer's own browser. Its first screen is a tamper lab: press the red button "Tamper with dossier #N" and the row turns red with `ALTERED` and the banner names it; "Tamper and re-hash" shows the next link breaking; "Rewrite the whole chain" shows the limit (the chain verifies again but the head hash changes, which is why the head is published and anchored). Nothing leaves the viewer's browser, and the downloaded tampered copy is rejected by the Python `verify` in the same way.

---

## Key Features

### 1. Frozen Evidence Packets
Every decision starts from the same immutable packet: hourly candles, funding rates, news headlines, and public RSS voices, each stamped with its source and collection time. Sources that fail are recorded as gaps, never faked.

### 2. LLM Debate with Citation Enforcement
Bull and bear analysts (Mistral) must cite evidence items by ID. A validator checks each claim against the frozen packet: wrong IDs, fabricated numbers, and uncited arguments are rejected and logged. The LLM's output is stored in the dossier and frozen, so replay re-validates citations without re-generating text.

### 3. Deterministic, Replayable Verdicts
The judge is pure deterministic code (no randomness, no LLM). Given the same frozen evidence and the same arguments, it always produces the same verdict, position size, stop, and target. The `replay` command re-derives every verdict from its frozen packet and confirms it matches the recorded one.

### 4. Cause-and-Effect Sensitivity Analysis
Each dossier includes a sensitivity table: how much more net edge would flip the verdict, and what the verdict would be if each individual argument were removed, answering "which single argument decided this?" from the same weights the judge used.

### 5. Tamper-Evident Hash Chain
Every dossier carries `prev_hash` and its own `hash` over canonical JSON. The same canonicalization runs in Python (ledger writer) and JavaScript (browser verifier), with shared test vectors. `verify` checks the chain: editing a dossier flags that dossier, re-hashing it breaks the link of the next one, and rewriting every later hash leaves the chain consistent but changes the head, which only a copy outside the operator's control (git history, other clones, an on-chain anchor) can expose.

### 6. Auditing Third-Party Agent Journals
`audit-journal` takes the journal of any autonomous agent, cross-checks its recorded candles and prices against public Binance data, and replays each symbol-hour in shadow, reporting what Verdict Desk would have recorded next to what the agent actually did. Free-text reasoning is never copied into the audit output.

### 7. Live, Append-Only History
GitHub Actions is scheduled every hour: each run appends decisions for BTCUSDT, ETHUSDT, and SOLUSDT, verifies the chain, commits, and redeploys the dashboard. Scheduled runs are best effort, so the cadence has gaps, and they are published (dashboard cadence panel, README "Live operation"). The commit log serves as an independent clock.

---

## How Verdict Desk Meets the RYO-CHAN Bounty Criteria

### Criterion 1: Agents that interpret market evidence and record practical (simulated) operations

Verdict Desk does exactly this end-to-end. It collects public market data (candles from Binance, funding from OKX, news from GDELT, RSS voices), freezes it into an evidence packet, and feeds it to two LLM analyst agents who produce arguments grounded in specific evidence items. The judge then records a simulated position with entry price, size, stop-loss, and take-profit, plus a portfolio tracker that marks positions against subsequent candles.

**Evidence in the repo:**
<!-- numbers:start -->
- 71 dossiers in `ledger/ledger.jsonl` as of dossier 71 (2026-10-20 22:18 UTC), over a window of 84.9 h; from dossier 46 on, the citation validator accepted 140 claims and rejected 24 (85.4% accepted). Counted by `python3 -m verdict_desk stats --git`; the chain keeps growing
<!-- numbers:end -->
- `verdict_desk/evidence.py`, `verdict_desk/narrative.py`: evidence collection and narrative extraction
- `verdict_desk/agents.py`, `verdict_desk/portfolio.py`: agents and portfolio tracking
- LLM layer working since dossier seq 46 (Mistral API); the earlier dossiers stay as recorded (no LLM layer, then HTTP 403 from the first provider, then claims the validator rejected)

### Criterion 2: Show cause and effect

Every argument in every dossier names the specific evidence item it rests on. The citation validator enforces this: an LLM claim that references a non-existent ID or quotes a number not present in the cited item is rejected. The sensitivity analysis in each dossier shows which arguments were decisive ("remove this one and the verdict flips"), computed deterministically from the judge's own weights.

**Evidence in the repo:**
- `verdict_desk/citations.py`: citation validation logic
- Each dossier's `llm.bull` and `llm.bear` blocks: `accepted` claims with the evidence ids they cite (`cites`) and `rejected` claims with `rejected_because`
- Sensitivity tables showing verdict impact per argument
- Dashboard row details showing the full debate with citations

### Criterion 3: A repeatable reasoning trail

Every dossier is hash-chained to the previous one via RFC 8785 canonical JSON. The `replay` command re-derives every verdict from its frozen evidence packet without touching the LLM: the analysts' text is stored and re-validated against the frozen packet, not regenerated. `verify` checks the entire hash chain. An auditor can load the ledger into the dashboard and see every SHA-256 recomputed in their own browser.

**Evidence in the repo:**
- `verdict_desk/dossier.py`: dossier creation, canonicalization, hashing
- `web/canonical.js`: identical canonical JSON implementation in JavaScript
- `tests/canonical_vectors.json`: shared cross-language test vectors
- 153 passing unit tests, all verifiable with `python3 -m unittest discover -s tests`

---

## Chainlink CRE Workflow

Verdict Desk includes a Chainlink CRE workflow that:
1. Fetches the published ledger head with identical consensus
2. Reads the BTC/USD Data Feed price on Sepolia
3. Writes both to a `LedgerAnchor` contract through a CRE report

The workflow code and the Solidity receiver contract are written and covered by tests (10 SDK mock tests + 6 in-memory EVM tests).

**Current CRE status, stated honestly:** The workflow simulation (`cre workflow simulate`) and a live Sepolia deployment have not been run yet. No on-chain anchor transaction exists. The code is complete, tested, and documented; the remaining steps are execution (account setup, simulation, deployment, recording a transaction), which the team is working on.

See `cre/README.md` and `cre/DEPLOY_SEPOLIA.md` for full details.

---

## Honest Backtest Results

Verdict Desk ran a walk-forward backtest (rules v1, latest 4,000 hourly candles as of 2026-10-17, 0.05% fee per side) on three symbols:

| Symbol | Net Return | Profit Factor | Buy & Hold |
|---|---|---|---|
| BTCUSDT | −18.66% | 0.85 | −0.10% |
| ETHUSDT | −9.98% | 0.92 | +3.13% |
| SOLUSDT | +1.31% | 1.01 | +17.98% |

**These are tests on past data, not live trading results.** Verdict Desk is a reasoning-trail tool, not a money machine. The backtest numbers are published precisely because the project prioritizes transparency over marketing.

A tuned set of v1 parameters was also searched (train on first 60%, judge on last 40%, 36 candidate settings). It beat v1 out-of-sample on all 3 symbols but was net positive on only 1 of 3 and never beat buy-and-hold, so it was not adopted.

**Which rules record the live dossiers:** the backtest above is for v1, which recorded dossiers 1 to 53. The hourly workflow now records with the v2 rules in `agents_v2.py` (the v1 arguments plus RSI, MACD and Bollinger arguments, entry threshold 1.5); each dossier says which rules recorded it in `verdict.rules_version`. These v2 rules are not covered by the backtest table.

Each backtest run prints the SHA-256 of its candle series so the numbers can be reproduced on the same data.

---

## What to Look at First (Judge Path)

1. **Open the dashboard** → https://andriyamaro.github.io/verdict-desk/
   It loads the ledger and recomputes every hash in your browser.

2. **Press the red button "Tamper with dossier #N"** → the tamper lab on the first screen: the row turns red in your own browser, and nothing is sent anywhere.

3. **Click on dossier seq 46 or later** → These are the first dossiers where the Mistral LLM agents produce accepted claims on both sides of the debate. Earlier dossiers (seq 1-4: no LLM layer; seq 5-34: HTTP 403 from the first model provider; seq 35-45: 0 of 48 claims passed the validator) are honest history showing how the system evolved.

4. **Watch the 2-minute demo** → https://andriyamaro.github.io/verdict-desk/demo/verdict-desk-demo.mp4
   Recorded from real command output and the real dashboard. Nothing is mocked.

5. **Run it yourself:**
   ```bash
   git clone https://github.com/AndriyAmaro/verdict-desk.git
   cd verdict-desk
   python3 -m unittest discover -s tests     # 153 tests
   python3 -m verdict_desk verify             # hash chain
   python3 -m verdict_desk replay             # re-derive every verdict
   python3 -m verdict_desk portfolio          # simulated positions
   python3 -m verdict_desk stats --git         # live-operation numbers counted from the ledger
   ```

---

## Limits (Disclosed)

- The hash chain proves **integrity after recording**, not **authenticity at collection time**. Independent witnesses (source timestamps, git history, and eventually the CRE anchor) narrow that gap.
- A literal headline can still be wrong or manipulative. The grounding gate proves the headline says it, not that it is true.
- One voice never creates a narrative convergence: at least two distinct voices on the same token and stance are required.
- LLM-generated text is frozen and not re-producible on replay by design; it is stored and re-validated against the evidence.
- Simulated fills use the last close with fees. One exchange mirror. One rule set. This is a trail of reasoning, not a trading edge.

---

## Team

- **Andri Amaro**: Builder
- **AI Coding Agent**: Claude Code (disclosed)

---

## License

MIT. The CRE project layout follows the MIT-licensed `smartcontractkit/cre-templates`; `@chainlink/cre-sdk` (BUSL-1.1) is used as a dependency. Everything else is original.

---

*Built for the BLI Legal Tech Hackathon 2, October 2026.*
