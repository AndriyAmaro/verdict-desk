# SUBMISSÃO — VERDICT DESK — SUPERSEDED

> **Superseded by `SUBMISSAO_DORAHACKS.md`** (the canonical, auto-refreshed submission). The figures below are a historical snapshot and are NOT current — see README.md or run `python3 -m verdict_desk stats --git` for the live numbers.

---

## Onde clicar

1. Abra **https://dorahacks.io/hackathon/legal-hack-2026** logado como `andriamaro`.
2. Clique em **Submit BUIDL** (ou "Apply"). A DoraHacks vai **criar um BUIDL novo** vinculado ao hackathon — o BUIDL 49999 que já existe **não tem como ser vinculado depois**, é por isso que até hoje não estamos na disputa.
3. No formulário, **marque as 2 bounties**: `Autonomous Agents` (US$ 6.000) e `Best workflow with CRE` (2× US$ 1.000). O limite é 10 por build, então as duas cabem.
4. Cole campo por campo o que está abaixo.
5. Publique e me avise — eu confiro pela API se entrou.

---

## CAMPO: Nome do BUIDL

```
Verdict Desk
```

## CAMPO: Slogan / tagline (1 linha)

```
Audit-grade, replayable decisions for autonomous market agents — don't trust it, check it.
```

## CAMPO: Vision (o que é e por que existe)

```
An autonomous agent that trades or advises on a client's money creates a record problem: six months later, when someone asks why it opened that position, the only account of what happened lives inside the operator's own database. Verdict Desk fixes that. Every decision becomes a dossier that freezes the evidence it saw, both sides of the argument, the verdict that followed, and a SHA-256 hash chained to the previous dossier — so the decision trail can be handed to an auditor, a compliance officer or a counterparty and checked without trusting the operator at all.

It runs live: 98 decisions recorded hourly over 130.9 continuous hours on BTCUSDT, ETHUSDT and SOLUSDT, every one of them reproducible from its frozen evidence. The head of the chain is anchored on Ethereum Sepolia by a Chainlink CRE workflow, so the operator cannot quietly rewrite history.
```

## CAMPO: Descrição (o corpo — é isto que o juiz lê)

```
WHAT IT DOES

Three agents read the same frozen evidence packet. A bull agent and a bear agent — both language models — argue opposite cases and must cite evidence IDs. A validator then discards any claim whose numbers do not appear in the item it cites: in the live ledger 333 claims were accepted and 46 rejected for that reason alone (87.9%). A third agent, written as deterministic code and not a model, weighs the arguments and decides action, size, stop and target inside fixed risk limits. Because the judge is code and the evidence is frozen, the same packet always produces the same verdict.

WHAT GETS RECORDED

Each dossier holds the complete evidence packet with the source and timestamp of every item, the deterministic bull and bear arguments, the LLM claims with the evidence ID each one cites, the claims the validator rejected and why, the verdict, and a sensitivity table showing exactly what would have flipped it. Then the whole thing is hashed and chained to the previous dossier.

WHERE THE BOUNTY ASKS FOR CAUSE AND EFFECT

The sensitivity table is the answer. For every argument it records what the verdict would be without that single argument and whether removing it flips the decision. It is derived from the same weights the judge used, so it is deterministic, it replays, and it is not a narrative written after the fact.

WHERE IT ASKS FOR A REPEATABLE REASONING TRAIL

Replay. `python3 -m verdict_desk replay` re-derives every verdict from its own frozen evidence and compares it to what was recorded: 98 of 98 match. The dashboard does the same thing for the hashes in the visitor's own browser, in JavaScript, with the same canonicalization that Python used to write them — shared test vectors keep the two honest.

FAIL-CLOSED ON STALE EVIDENCE

Market evidence carries a two-hour freshness window. The age of the newest candle is computed when the packet is frozen and stored inside it, so the check itself is replayable and never reads the clock later. Older than the window and the judge returns BLOCKED_STALE and sizes no position: the agent refuses to decide on a stale price instead of quietly extrapolating one, and the refusal is written into the dossier so it is as auditable as a decision that was taken.

THE ONE-CLICK TAMPER TEST

Open the dashboard, press "Test the chain". It flips a single character in a copy of one dossier held in your tab: the row turns red, the banner names the dossier, and a three-row table shows the recorded hash next to the one your browser just recomputed. "Tamper and re-hash" plays the cleverer attacker — the edited row looks valid again, but the next row no longer links to it. "Rewrite the whole chain" shows the real limit: everything verifies again, but the head hash is different, which is exactly why the head is published outside the operator's reach (git history, other clones, and the on-chain anchor). The server's file is never touched.

NARRATIVE AGENT

Reads public voices, extracts token, stance, conviction and urgency per headline with an LLM, and only keeps an extraction when it carries a quote that is a literal part of the headline and values from a closed vocabulary. Convergence requires at least two distinct voices on the same token and the same stance. Across the live ledger it has recorded 101 convergences; one example is BTC bullish across CoinDesk, Cointelegraph, Decrypt and The Block at high conviction, and that convergence is a citable item when the judge rules.

CHAINLINK CRE

A CRE workflow fetches the published ledger head over HTTP under DON consensus, reads the BTC/USD Data Feed on Sepolia, and writes both to a receiver contract through the CRE forwarder. The contract accepts reports only from the forwarder and only with a strictly increasing sequence number, so an anchored head can never be overwritten.

Contract: 0x50443D51Db71A61E131B147B1d36aF21d48CDdF7
Transaction: https://sepolia.etherscan.io/tx/0x53e5a96312ff3f200f7cb1c1abc0b96313272b5fc59c4bf85a136f6a26c2694d

EVIDENCE HAND-OFF

`python3 -m verdict_desk export --seq N --out pack.json` writes one dossier as a self-contained file: the recomputed hash next to the recorded one, the replay result, the neighbouring hashes that pin it in the chain, plain-language steps to verify it without trusting the exporter, and a digest over all of it.

WHAT IS SIMULATED AND WHAT IS REAL

Real: the market data, the decisions, the hash chain, the browser verification, the replay, and the Sepolia anchor transaction. Simulated: the money. No funds move, ever. What is being demonstrated is the evidentiary trail, not a trading strategy — the positions exist so that every decision has a cost attached to it, which is what makes the record worth auditing.
```

## CAMPO: "Como isso se aplica" / track / categoria

```
LegalTech & RegTech — verifiable audit trail for autonomous agent decisions.
```

## CAMPO: Team

```
Andriy Amaro — solo builder. Full-stack and smart-contract developer. Built the full pipeline end to end: evidence collection, the three-agent debate, the deterministic judge, the hash-chained ledger, the browser verifier, the Chainlink CRE workflow and its Sepolia deployment.
```

## CAMPO: GitHub

```
https://github.com/AndriyAmaro/verdict-desk
```

## CAMPO: Demo / site

```
https://andriyamaro.github.io/verdict-desk/
```

## CAMPO: Vídeo (narrado, 3min15)

```
https://andriyamaro.github.io/verdict-desk/demo/verdict-desk-demo-narrated.mp4
```

## CAMPO: Tech tags (se pedir)

```
Python, JavaScript, Chainlink CRE, Ethereum Sepolia, Solidity, SHA-256 hash chain, LLM agents, Mistral, GitHub Actions
```

---

## Provas que o juiz pode checar em 2 minutos

| O que | Onde |
|---|---|
| Cadeia íntegra | `python3 -m verdict_desk verify` → `Chain intact: 98 dossiers` |
| Replay 100% | `python3 -m verdict_desk replay` → 98× `MATCHES` |
| Testes | `python3 -m unittest discover -s tests` → `Ran 213 tests ... OK` |
| Números da operação | `python3 -m verdict_desk stats` |
| Pacote de evidência | `python3 -m verdict_desk export --seq 98 --out pack.json` |
| Adulteração | dashboard → botão **Test the chain** |
| Tx on-chain | https://sepolia.etherscan.io/tx/0x53e5a96312ff3f200f7cb1c1abc0b96313272b5fc59c4bf85a136f6a26c2694d |

## Antes de publicar, confira

- [ ] As **duas** bounties marcadas: Autonomous Agents + Best workflow with CRE
- [ ] GitHub público e abrindo
- [ ] Demo (GitHub Pages) abrindo
- [ ] Vídeo abrindo (4,4 MB, 3min15, com voz)
- [ ] Tx do Sepolia abrindo e mostrando SUCCESS
- [ ] Nada de número inventado: todos saem de `python3 -m verdict_desk stats`
