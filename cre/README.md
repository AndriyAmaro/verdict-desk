# Chainlink CRE anchor for the Verdict Desk ledger

A Chainlink Runtime Environment (CRE) workflow that makes the decision ledger tamper-evident beyond the operator's word. Once a day it:

1. fetches the published ledger head (`seq`, SHA-256 `hash`, `symbol`) over HTTP, where every node must see the same bytes (identical consensus);
2. reads a Chainlink **Data Feed** price (BTC/USD on Sepolia) as independent cross-check evidence;
3. writes both to the `LedgerAnchor` contract on Sepolia through a CRE report.

`LedgerAnchor` only accepts reports from the CRE forwarder and only with a sequence number higher than the last one, so an anchored head can never be overwritten or rolled back. A judge compares `isAnchored(seq, hash)` on-chain with the head they recompute from the public ledger in their own browser (`../web/index.html`).

```
ledger/head.json (public) --HTTP, identical consensus--> CRE workflow --report--> Forwarder --> LedgerAnchor (Sepolia)
Chainlink Data Feed BTC/USD ------EVM read------------^
```

## What has been verified, and what has not

| Piece | Status | How |
|---|---|---|
| Head format shared by Python and the workflow | Verified | `python -m verdict_desk head`, parsed by `anchor/logic.ts` |
| Workflow logic (HTTP head parsing, Data Feed read, report encoding, failure paths) | Verified with the SDK's test mocks | `cd anchor && bun test` (10 tests), `bunx tsc --noEmit` |
| `LedgerAnchor.sol` | Verified in a real in-memory EVM | `cd contracts/evm && npm install && python -m unittest discover -s test` (6 tests: forwarder-only, append-only, owner check, ERC165, exact custom errors) |
| Deploy script against Sepolia | Dry run done (forwarder code check, gas estimate: about 0.0000006 ETH) | `cd contracts && node scripts/deploy.mjs --dry-run` |
| `cre workflow simulate` | **Not run yet.** The CLI needs a CRE login or API key (API key auth also needs deploy access approval on the account) | [`DEPLOY_SEPOLIA.md`](DEPLOY_SEPOLIA.md) |
| Live deploy on Sepolia and a real report | **Not done.** Needs a funded throwaway testnet key; nothing is claimed until `evidence/` and `deployment.sepolia.json` exist | [`DEPLOY_SEPOLIA.md`](DEPLOY_SEPOLIA.md), `scripts/anchor-sepolia.sh` |

## Run it

```bash
# unit tests, no account needed
cd anchor && bun install && bun test && bunx tsc --noEmit
cd ../contracts/evm && npm install && npm run compile && python -m unittest discover -s test

# simulation, needs a CRE account (https://docs.chain.link/cre/account/creating-account)
export CRE_API_KEY=...            # or: cre login
cre workflow simulate ./anchor -T staging-settings --non-interactive --trigger-index 0
# add --broadcast to send the report for real (needs a funded Sepolia key as CRE_ETH_PRIVATE_KEY in an ignored .env)

# or everything in order (deploy, simulate, broadcast, check) from a funded throwaway key:
SEPOLIA_PRIVATE_KEY=0x... bash scripts/anchor-sepolia.sh
# anyone can check what the contract holds against the public ledger, no key needed:
node contracts/scripts/check-anchor.mjs
```

The full runbook, with the status of each step, is [`DEPLOY_SEPOLIA.md`](DEPLOY_SEPOLIA.md).

`anchor/config.staging.json` already points `headUrl` at the raw `ledger/head.json` of this repository; before a real transaction, set `anchorAddress` to the deployed `LedgerAnchor` (it is the zero address while only simulating). Deploy `LedgerAnchor(forwarder, expectedWorkflowOwner)` with the Sepolia `MockKeystoneForwarder` for simulation or the production CRE forwarder for a deployed workflow; confirm both addresses in the CRE Forwarder Directory first.

| Reference | Value | Source |
|---|---|---|
| BTC/USD Data Feed, Sepolia | `0x1b44F3514812d835EB1BDB0acB33d3fA3351Ee43` | `smartcontractkit/cre-templates`, prediction-market config |
| Sepolia MockKeystoneForwarder (simulation) | `0x15fc6ae953e024d975e77382eeec56a9101f9f88` | same repository, READMEs |
| Sepolia CRE forwarder (deployed workflows) | `0xf8344cfd5c43616a4366c34e3eee75af79a74482` | same repository, sports-resolution README |

## Layout

| Path | What it is |
|---|---|
| `anchor/` | The workflow: `workflow.ts` (handler), `logic.ts` (pure functions), `main.ts` (entry), tests, `config.staging.json` |
| `contracts/evm/src/LedgerAnchor.sol` | Receiver contract, written for this project, no dependencies |
| `contracts/evm/src/abi/*.abi` | ABIs the bindings are generated from (`cre generate-bindings evm --language typescript`) |
| `contracts/evm/ts/generated/` | Generated bindings (do not edit) |
| `contracts/evm/test/` | EVM-level contract tests |
| `contracts/scripts/` | `deploy.mjs` (deploy from a throwaway key held in the environment, never printed) and `check-anchor.mjs` (read-only: verifies the ledger chain, reads the anchor, asks `isAnchored`) |
| `scripts/anchor-sepolia.sh` | Deploy, simulate, broadcast and check in order; saves the outputs in `evidence/` |
| `DEPLOY_SEPOLIA.md` | Runbook and status of each step |
| `project.yaml`, `secrets.yaml` | CRE project settings (no secrets are used) |

## Credits and licenses

Project layout and the use of the CRE SDK follow the MIT-licensed `smartcontractkit/cre-templates`; the workflow, contract and tests are original. `@chainlink/cre-sdk` is BUSL-1.1 and is used as a dependency, not vendored. Developed with AI assistance (Claude Code).
