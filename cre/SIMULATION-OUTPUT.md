# CRE simulation and anchor evidence

**Status: PENDING.** No `cre workflow simulate` run, no deployment and no anchor transaction exist yet. This file is where the evidence lands. Every value below stays "pending" until a real run produces it, and nothing may be filled in by hand with a value that did not come from that run ("Where each value comes from" says which command gives which field).

## Summary

When the table is filled, copy it into the root `README.md` (section "Chainlink CRE", between the `cre-evidence` markers).

| Field | Value |
|---|---|
| Date and time of the run (UTC) | pending |
| CRE CLI version | pending |
| Workflow | `vd-anchor-staging` (`cre/anchor`, target `staging-settings`) |
| Ledger head the workflow read (seq, hash) | pending |
| Head anchored in the contract (seq, hash) | pending |
| BTC/USD Data Feed value recorded with it (answer, decimals, feed updated at) | pending |
| `LedgerAnchor` contract on Sepolia | pending |
| Forwarder | pending (`MockKeystoneForwarder` for a simulation) |
| Anchoring transaction | pending |
| `isAnchored(seq, hash)` answer | pending |
| Commit of this repository that the run used | pending |

A simulation without `--broadcast` only proves that the workflow runs end to end against the simulator. Only the broadcast run produces a transaction, so only it can fill the anchor rows.

## Simulation output (dry run, nothing is sent)

```
pending: paste cre/evidence/simulate-output.txt
```

## Broadcast output (the report reaches the contract in a real Sepolia transaction)

```
pending: paste cre/evidence/broadcast-output.txt
```

## Check against the public ledger

```
pending: paste the output of: node cre/contracts/scripts/check-anchor.mjs
```

## Where each value comes from

| Field | Source |
|---|---|
| Date, CLI version | `cre version`, and the timestamps inside the two outputs above |
| Ledger head the workflow read | The line "Anchoring ledger head from ..." and the `seq` and `head` fields of the result line in `evidence/broadcast-output.txt` |
| Head anchored, feed value, contract, transaction, `isAnchored` | `node cre/contracts/scripts/check-anchor.mjs --json`: it reads them from the chain, not from files in this repository |
| Forwarder, deployer, deploy transaction | `cre/deployment.sepolia.json`, written by `contracts/scripts/deploy.mjs` |
| Commit of this repository | `git rev-parse HEAD` when the run started |

The anchored head is the head at the time of the run, not the current one: the ledger grows every hour, and the contract only keeps a strictly increasing sequence number. `check-anchor.mjs` therefore compares the anchored hash with the ledger's dossier at that same sequence number.

## Checklist when the evidence exists

1. Paste the three outputs above and fill the summary table from `check-anchor.mjs --json` and `deployment.sepolia.json`.
2. Copy the summary rows into the root `README.md`, between `<!-- cre-evidence:start -->` and `<!-- cre-evidence:end -->`, and change the status sentence of that section from "have not been run yet" to what ran.
3. Update the status tables of `cre/README.md` and `cre/DEPLOY_SEPOLIA.md`, and item 5 of section 11 of `docs/architecture.md`.
4. Put the transaction link on the DoraHacks build page and in the demo video, and run `python3 scripts/refresh_numbers.py --check` so the other published figures are current.

## How a judge checks it

```bash
node cre/contracts/scripts/check-anchor.mjs
```

No key is needed. It verifies the whole hash chain of the ledger with the code the dashboard runs, reads the latest anchored sequence number and head hash from Sepolia, asks the contract `isAnchored(seq, hash)` for the hash that the ledger has at that sequence number, and prints the anchoring transaction. The exit code is 0 only when the chain is intact and the anchored head is exactly that dossier.

## What this will prove, and what it will not

An anchored head pins the hash of one dossier, and through the chain every dossier before it, at a time the operator cannot move: the Sepolia block time. Rewriting history afterwards produces a different head, and `isAnchored(seq, hash)` answers false for it. It does not show that the evidence was true when it was collected, and the head is only as recent as the last anchoring run.
