# Verdict Desk

**Audit-grade, replayable decisions for AI market agents. Simulated only: no order is ever placed.**

Verdict Desk reads public market evidence, freezes it, lets a bull agent and a bear agent argue over the same facts, and lets a deterministic judge size a *simulated* position inside declared risk limits. Every decision becomes a **dossier** that is hash-chained to the one before it. A judge, an auditor or a lawyer can open the dashboard, drop in the ledger, and see every SHA-256 recomputed in their own browser. They can re-run the reasoning from the frozen evidence and see the same verdict, or see exactly where it differs.

Built for the BLI Legal Tech Hackathon 2 (bounty "Autonomous Agents", with a Chainlink CRE workflow for the second bounty).

## What the bounty asks, and where to look

| The bounty asks for | Verdict Desk | Look here |
|---|---|---|
| Interpret market evidence | One frozen evidence packet per decision: candles, funding, news, and the narrative of public voices, each with source and time | `verdict_desk/evidence.py`, `narrative.py` |
| Record the simulated operation | Entry, size, stop, target and the portfolio marked against later candles | `verdict_desk/agents.py`, `portfolio.py` |
| Cause and effect | Every argument names the evidence item it rests on; LLM claims must cite item ids and numbers that really appear there | `verdict_desk/citations.py`, dashboard row details |
| A repeatable reasoning trail | `replay` re-derives the verdict from the frozen packet; `verify` checks the hash chain | `verdict_desk/dossier.py` |
| Chainlink CRE (second bounty) | A CRE workflow plus a receiver contract that anchor the ledger head and a Data Feed price on Sepolia | `cre/` (status table inside) |

## Five-minute judge path

1. Open the dashboard (the GitHub Pages site of this repository). It loads `ledger/ledger.jsonl` and shows the banner "Every hash recomputed in this browser matches". It does not trust the server: the hashing runs locally in `web/canonical.js`.
2. Read the two panels above the table: the **cadence** of the live history (every gap between runs, nothing filled in) and the **simulated portfolio** (recomputed in your browser from the ledger with the same rule as `portfolio.py`). Then click a row. You see the deterministic bull and bear arguments with the exact indicator behind each one, then the LLM analysts' claims with the evidence id each one cites, and the claims the citation validator **rejected**, with the reason.
3. Edit one character of the ledger in a text editor, load it with the file picker, and watch the row turn red (`ALTERED`) and the chain break from there on.
4. Run it yourself:

```bash
python3 -m unittest discover -s tests          # 67 tests, standard library only
python3 -m verdict_desk verify                 # hash chain of ledger/ledger.jsonl
python3 -m verdict_desk replay                 # re-derive every verdict from its frozen evidence
python3 -m verdict_desk portfolio              # simulated positions marked against later candles
```

## How it works

```
public data ──> frozen evidence packet ──> bull agent ┐
(candles, funding,   (source + time on     bear agent ├─> deterministic judge ──> dossier (hash-chained)
 news, RSS voices)    every item)          narrative  ┘     size, stop, target        │
                                                                                      └─> ledger/ledger.jsonl ──> dashboard, replay, CRE anchor
```

- **Evidence.** Binance public spot mirror (candles), OKX public funding, GDELT news, and public RSS or Atom feeds. No API key is needed for any of them. A source that fails reduces the evidence and is recorded as a gap; it never fakes a decision.
- **Agents.** The bull and bear analysts are LLM agents (Mistral API, free tier) that must cite evidence ids. A validator discards any claim with no citation, an unknown id, or a number that is not in the cited items. The judge that decides action, size, stop and target is deterministic code, so the same frozen packet always yields the same verdict.
- **Cause and effect.** Each dossier also freezes a sensitivity table: how much more net edge would flip the verdict to LONG or SHORT, and, for each argument, what the verdict would be without it (and whether that single argument decides it). It comes from the same arguments and weights the judge used, so it is deterministic and replayed too.
- **Narrative agent.** Reads up to 20 public voices. The LLM extracts token, stance, conviction and urgency per headline. Headlines are untrusted input, so each extraction must carry a quote that is a literal part of the headline, a voice id that exists and values from a closed vocabulary; anything else is dropped and logged in the packet. Convergence needs at least two distinct voices on the same token and stance. If the model is down the packet says `keywords` and uses a plain word-list fallback.
- **Ledger.** JSONL, one dossier per line, each with `prev_hash` and its own `hash` over RFC 8785 canonical JSON. The same canonicalization runs in Python and JavaScript, with shared test vectors, which is what lets the browser recompute the exact hash Python wrote.
- **Frozen LLM output.** The model's words are stored in the dossier and are not regenerated on replay. Replay re-derives everything deterministic and re-checks that each stored citation is still valid against the frozen evidence.

## Auditing someone else's agent

`audit-journal` takes the journal of an autonomous agent (one turn per line, with the evidence it saw) and does two things. First it checks every candle and price the journal recorded against public Binance data, counting only candles that had already closed at the turn time and comparing prices within a small tolerance because the agent reads perpetual futures while the public mirror is spot (volume is not compared). Second it replays each symbol-hour in shadow: the desk builds a packet from candles closed at that moment plus the funding the journal recorded, applies the same rules, and reports what it would have recorded next to what the agent did. The output is labeled as a shadow replay and never as a trade result, and the journal's free-text reasoning is never copied into it.

## Honest results

These numbers are tests on past data, not live trading results, and they are published because the system is a reasoning-trail tool, not a money machine.

| Walk-forward backtest, rules v1, latest 4,000 hourly candles on 2026-10-17, 0.05% fee per side | Net return | Profit factor | Buy and hold |
|---|---|---|---|
| BTCUSDT | -18.66% | 0.85 | -0.1% |
| ETHUSDT | -9.98% | 0.92 | +3.13% |
| SOLUSDT | +1.31% | 1.01 | +17.98% |

Each `backtest` run prints the sha256 of its candle series so the numbers can be reproduced on the same data. The window rolls, so a later run on newer candles will differ.

Rules v2 were searched with a fixed protocol (choose on the first 60%, judge on the last 40%, 36 candidate settings). v2 beat v1 out of sample on 3 of 3 symbols but was net positive on only 1 of 3 and never beat buy and hold, so **v1 stays the live rule set**. Details and caveats: [`research/README.md`](research/README.md).

## Live history

The workflow [`.github/workflows/hourly.yml`](.github/workflows/hourly.yml) appends decisions for BTCUSDT and ETHUSDT every hour, verifies the chain, writes `ledger/head.json`, commits, and redeploys the dashboard. Git commit times are an independent clock. GitHub scheduled runs are best effort and can be delayed or skipped, so read the commit log for the real cadence and the gaps.

## Chainlink CRE

[`cre/`](cre/README.md) holds a workflow that fetches the published ledger head with identical consensus, reads the BTC/USD Data Feed on Sepolia, and writes both to `LedgerAnchor` through a CRE report. The contract accepts reports only from the CRE forwarder and only with a higher sequence number than the last one.

Status, stated plainly: the workflow is covered by 10 tests with the SDK mocks and type-checks; the contract is covered by 6 tests in an in-memory EVM. `cre workflow simulate` and a live Sepolia deployment **have not been run yet**. Nothing here claims an anchored head until a transaction exists.

## Limits

- The hash chain proves **integrity after recording**, not **authenticity at collection time**. Independent witnesses narrow the gap: sources and timestamps are in every packet (anyone can refetch the candles), git history timestamps each commit, and the CRE anchor would pin the head on-chain.
- A literal headline can still be wrong or manipulative. The grounding gate proves the headline says it, not that it is true. One voice never creates a convergence.
- The model-written text is not reproducible on replay by design; it is frozen and re-validated.
- One exchange mirror, one rule set, simulated fills at the last close with fees. This is a trail of reasoning, not a trading edge.

## Run it

Python 3.10 or newer, standard library only. Optional: Node (cross-language hash test), Bun (CRE workflow tests).

```bash
export MISTRAL_API_KEY=...         # optional, free Mistral API key; without it the LLM layers are off and labeled so
export MISTRAL_MODEL=mistral-small-latest   # optional
python3 -m verdict_desk decide BTCUSDT ETHUSDT --default-feeds
python3 -m verdict_desk decide SOLUSDT --feed "My voice=https://example.com/feed.xml"
python3 -m verdict_desk backtest BTCUSDT
python3 -m verdict_desk research BTCUSDT ETHUSDT SOLUSDT
python3 -m verdict_desk audit-journal path/to/agent_journal.jsonl --out audit.json   # check a third-party agent journal against public data, replay it in shadow
python3 -m verdict_desk head --out ledger/head.json
```

The key is read from the environment only and is never written to a dossier or a log.

## Layout

| Path | What it is |
|---|---|
| `verdict_desk/` | The engine: evidence, narrative, features, agents, citations, llm, dossier, portfolio, backtest, research, canonical JSON, CLI |
| `web/` | Static dashboard and the browser verifier |
| `ledger/` | The public ledger and its head |
| `cre/` | Chainlink CRE workflow, receiver contract and tests |
| `docs/architecture.md` | Architecture, decisions and risks |
| `research/` | Rules v2 train and test study |
| `tests/` | Unit tests, cross-language vectors |

## License and credits

MIT, see [`LICENSE`](LICENSE). The CRE project layout follows the MIT-licensed `smartcontractkit/cre-templates`; `@chainlink/cre-sdk` (BUSL-1.1) is used as a dependency and is not vendored. Everything else is original.

Built by Andri Amaro with the help of an AI coding agent (Claude Code). The AI assistance is disclosed here on purpose.
