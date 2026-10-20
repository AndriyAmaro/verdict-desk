# Verdict Desk · Improvement Plan · 2026-10-20

Status: SUBMITTED to BLI Legal Tech Hackathon 2 on 2026-10-20, under review.
The build stays editable until judging. Deadline: 2026-10-31 22:01 (UTC-3).
Field today: 2 submitted builds (PocketChange and us). Main prize: US$ 6,000.
Plus 2 x US$ 1,000 Chainlink CRE prizes (see the decision gate at the end).

Verified state (checked 2026-10-20, from a clean clone at commit 35803e7):
- Ledger chain intact: 50 dossiers, head seq 50; `verify` passes; `replay` 50/50 matches.
- Python test suite: 129 tests, all passing.
- Public dashboard serves the current ledger head and re-verifies hashes in the browser.
- LLM debate works from seq 46 onward (post citation fix). Before that: 30 dossiers with an empty debate (NVIDIA era) and 11 with 100% rejected claims (numeric evidence ids).

Work split: Agent A takes Track A (product), Agent B takes Track B (presentation and docs). The CRE gate is the owner's decision and is not part of either track until he says go.

## Track A · Product substance (Agent A)

### A1. Analyst prompts: copy numbers at full precision, never round
Problem: in the latest dossier (seq 50) the bear side had 0 of 4 claims accepted. The model rounds numbers (writes 3.16% where the evidence says 3.1596; 0.00453% where the evidence has 4.53e-05) and the strict grounding validator rejects them. Dossiers 47-49 show the model succeeds when it copies numbers exactly.
Steps:
1. In the analyst prompts (bull and bear), add a hard rule: every number in a claim must be copied character-for-character from the cited evidence item, at full precision, never rounded, never reformatted (keep scientific notation as-is).
2. Add 2 worked examples to the prompt: one accepted claim (number copied exactly) and one rejected claim (rounded number), using real evidence formats.
3. If the harness supports it, add a pre-validation retry: when a claim is rejected for "number not in cited evidence", re-ask once with the rejection reason before discarding the claim.
Acceptance: over the next 10 dossiers, no dossier has a side with 0 accepted claims; acceptance rate per side is visible in the dossier as today.

### A2. Ledger bot: never lose an hour to a racing merge
Problem: `.github/workflows/hourly.yml` commits and pushes with no `git pull --rebase` first. A human merge landing between checkout and push fails the push and the hour is lost (3 human merges happened today between bot runs). Real cadence is already ~1 dossier per 1.6 h because the GitHub scheduler skips runs; do not add self-inflicted losses.
Steps:
1. Before the commit/push step, add `git pull --rebase origin main` (with a retry loop of up to 3 attempts around pull+push).
2. Note: editing workflow files requires the repo owner's own credentials (the connector app has no workflow permission). Owner or an agent running as the owner must apply this change.
Acceptance: a bot run that races a human merge still lands its dossier commit (test by merging a trivial PR while a run is in flight, or simulate locally).

### A3. Source-gap watch (low priority)
Problem: in seq 50 the news source (GDELT) returned HTTP 429 and the gap was honestly recorded. Fine once; a pattern would thin the evidence base.
Steps:
1. Count source errors per source over the last 20 dossiers.
2. Only if one source errors in more than ~30% of dossiers, space out or cache its queries.
Acceptance: a short note in this file with the measured rates and the decision taken.

## Track B · Presentation and docs (Agent B)

### B1. Fix the numbers and claims the docs make
Problems: the README says "67 tests" (the suite has 129); the comment in `hourly.yml` and the `NIM_MODEL` variable still reference NVIDIA/NIM while the model is Mistral; `docs/architecture.md` section 11 states the LLM layer "never ran against the real API" (it runs since seq 35), that the public repo "does not exist yet" (it does) and that the on-chain anchor "was not built" (the code exists; simulation/deployment is what is missing).
Steps:
1. README: 67 -> 129 tests (or drop the exact count and link the test command).
2. `hourly.yml` comment and variable naming: NVIDIA/NIM references -> Mistral.
3. `docs/architecture.md` section 11: correct the three stale claims above; state the CRE status precisely (code written and mock-tested; simulation and Sepolia deployment pending).
Acceptance: no statement in README or architecture docs contradicts the observable repo state.

### B2. Guide the judge to the working debate
Problem: the ledger is immutable by design, so a judge scrolling it sees the empty/rejected LLM history before the working era (seq 46+). That history is honest and stays; the narrative must point at the present.
Steps:
1. README: where the LLM debate is described, cite recent dossiers explicitly (seq 46 onward) as the live examples, with one honest sentence about the earlier eras.
2. Build page on DoraHacks: same pointer in the description (owner edits the build; it stays editable until judging).
3. Optional, small: make the dashboard highlight the latest dossier row by default in `web/index.html`.
Acceptance: a first-time reader following the README reaches a dossier with accepted bull and bear claims in under 2 minutes.

### B3. Build page completeness pass
Steps:
1. On the DoraHacks build page, confirm field by field: logo, the 256-character vision text, links to the GitHub repo, the live demo and the demo video (Pages URL), team and milestones sections filled.
2. Record in this file what was missing and what was filled.
Acceptance: no empty field on the build page.

## Decision gate · Chainlink CRE (owner only, decide by 2026-10-23)

What is at stake: 2 x US$ 1,000 CRE prizes, plus the differentiation claim of an on-chain anchor.
Current state: CRE workflow and the `LedgerAnchor` contract are written and mock-tested (`cre/`), but `cre workflow simulate` has never run, there is no Sepolia deployment and no anchor transaction, and the demo video does not show the CRE workflow. The Chainlink standard for these prizes expects: a successful simulation via the CRE CLI or a live deployment integrating an external API/agent, a public 3-5 minute video showing the CRE workflow running, public code, and a README pointing to the Chainlink files (the last two are already done).
If GO, the sequence is:
1. Owner creates the CRE account (his act; cannot be delegated).
2. Run `cre workflow simulate` with the MockKeystoneForwarder.
3. Deploy `LedgerAnchor` on Sepolia (faucet-funded testnet key) and anchor the current ledger head in one real transaction.
4. Record a video segment showing the CRE workflow executing (extend the demo to 3-5 minutes or add a CRE chapter).
5. Link the transaction in the README and on the build page.
Estimated effort after the account exists: half a day to one focused day.
Cost of waiting: every day compresses the part that depends on third parties (the account). Not deciding by 2026-10-23 is effectively deciding no.

## Source

Full audit (Portuguese, internal): kalme's end-to-end analysis of 2026-10-20 (repo, ledger, dashboard, build, CRE gap), run against commit 35803e7 with the verifier, replay and test suite executed for real.
