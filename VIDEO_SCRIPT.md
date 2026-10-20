# Verdict Desk — Demo Recording Script (3–5 min)

> **Goal:** Show the full pipeline — evidence collection → bull/bear debate → deterministic verdict → hash-chain verification → replay → live dashboard. All real, nothing mocked.
>
> **Target runtime:** ~4 min
> **Recording format:** Screen capture with terminal + browser. Voiceover optional.
> **Prerequisites:** `git clone` done, `python3` 3.10+, ledger at 53 dossiers (commit `be470c2` or later).

---

## Scene 0 — Setup (0:00 – 0:15)

**Screen:** Terminal, clean prompt at the repo root (`/tmp/verdict-desk-work` or wherever cloned).

```bash
cd verdict-desk          # or cd ~/verdict-desk
git log --oneline -5     # show you're on a real commit
wc -l ledger/ledger.jsonl   # "53" — the living ledger
```

**Narration (optional):**
> "Verdict Desk is a tool that makes audit-grade, replayable simulated trading decisions. It freezes public market evidence, lets a bull and a bear argue, and a deterministic judge sizes a position. Every decision is hash-chained so any judge or lawyer can verify it in their own browser."

---

## Scene 1 — Run a fresh decision (0:15 – 1:00)

**Command:**

```bash
python3 -m verdict_desk decide BTCUSDT --no-news --default-feeds
```

> Use `--no-news` if you want to skip GDELT (slow in demos). Keep `--default-feeds` to pull the 5 RSS voices and show the narrative layer. If you want the LLM debate to fire, set `MISTRAL_API_KEY` first (takes ~10-15s for API call).

**Expected output (example):**

```
narrative (llm): 8 headlines from 5 voices, 2 convergences
#54 BTCUSDT SHORT edge=-2.25 hash=a3c91d4f8b2e...
  Bear wins 2.25 to 0: edge reaches entry threshold
  [bear] Short-term trend below long-term trend (features.ema_fast<ema_slow)
  [bull] RSI oversold — bounce likely (features.rsi_14)
  to flip: +2.0 net edge for LONG
```

**Narration:**
> "I run `decide BTCUSDT`. The system fetches 72 hourly candles from Binance's public mirror, OKX funding rate, and five public crypto news feeds. The bull and bear agents each argue from this evidence. The judge — pure deterministic code — weighs arguments, picks SHORT, and writes a new dossier to the ledger with a SHA-256 hash chained to the previous one."

**What to point at:**
- The hash at the end of the line (first 16 chars)
- The `[bear]` and `[bull]` lines showing cited evidence
- The "to flip" sensitivity line

---

## Scene 2 — LLM debate deep-dive (1:00 – 1:45)

**Screen:** Terminal. Open dossier #46 (the first with accepted LLM claims) in a Python one-liner or just `jq`:

```bash
# Show the LLM layer for seq 46
python3 -c "
import json
with open('ledger/ledger.jsonl') as f:
    dossiers = [json.loads(l) for l in f]
d = dossiers[45]  # seq 46
llm = d['llm']
print(f\"Model: {llm['model']}\")
print(f\"Bull accepted: {len(llm['bull']['accepted'])} claims\")
for c in llm['bull']['accepted']:
    print(f'  {c[\"claim\"][:120]}')
print(f\"Bear accepted: {len(llm['bear']['accepted'])} claims\")
"
```

**Narration:**
> "From dossier 46 onwards, Mistral LLM agents join the debate. Each claim must cite an evidence ID — the validator rejects any claim without a real citation. Here, the bull had 3 accepted claims about consolidation patterns and institutional adoption, each tied to a specific headline or indicator."

**What to point at:**
- The model name (`mistral-small-latest`)
- The claim text
- The fact that claims are frozen — replay never calls the API again

---

## Scene 3 — Verify the hash chain (1:45 – 2:15)

**Command:**

```bash
python3 -m verdict_desk verify
```

**Expected output:**

```
Chain intact: 53 dossiers, head a2bf56f89a114e8c
```

**Narration:**
> "`verify` walks the entire ledger — every dossier's hash recomputed, every `prev_hash` checked against the previous dossier's hash. All 53 dossiers pass. If you alter even one character of any past entry, the chain breaks from that point forward."

**Optional demo (10 seconds):** Show the tamper detection:

```bash
# In another tab, or skip this if short on time:
cp ledger/ledger.jsonl /tmp/ledger-backup.jsonl
python3 -c "
import json
lines = open('ledger/ledger.jsonl').readlines()
d = json.loads(lines[0])
d['verdict']['edge'] += 0.01
lines[0] = json.dumps(d) + '\n'
open('ledger/ledger.jsonl','w').writelines(lines)
"
python3 -m verdict_desk verify   # shows the break
mv /tmp/ledger-backup.jsonl ledger/ledger.jsonl  # restore
```

---

## Scene 4 — Replay all decisions (2:15 – 2:45)

**Command:**

```bash
python3 -m verdict_desk replay
```

**Expected output (abbreviated):**

```
#1 replay MATCHES: FLAT
#2 replay MATCHES: FLAT
...
#24 replay MATCHES: SHORT
...
#46 replay MATCHES: SHORT
...
#53 replay MATCHES: FLAT
```

**Narration:**
> "`replay` re-derives every single verdict from the frozen evidence packet — no API calls, no randomness. All 53 match. The same frozen evidence always produces the same verdict because the judge is deterministic code. The LLM arguments are frozen in the dossier too, and the replay validates that each stored citation is still valid."

---

## Scene 5 — Simulated portfolio (2:45 – 3:15)

**Command:**

```bash
python3 -m verdict_desk portfolio
```

**Expected output:**

```
Decisions 53 (flat 51), positions 2: closed 2, open 0
  #24 ETHUSDT SHORT entry 2373.78 -> TAKE exit 2332.27 pnl +200.0
  #46 ETHUSDT SHORT entry 2384.07 -> STOP exit 2404.62 pnl -100.0
Win rate 50.0%  realized 100.0  unrealized 0  max drawdown 0.98%  (simulated, start 10000.0)
```

**Narration:**
> "The portfolio marks each simulated position against later candles from the ledger. Two positions taken, one hit the target for a $200 gain, one hit the stop for a $100 loss — both on ETH. This is not a trading system; it's a reasoning-trail tool. The numbers are published so anyone can reproduce them."

---

## Scene 6 — The dashboard (3:15 – 4:00)

**Action:** Open `web/index.html` in a browser:

```bash
# Option A: simple HTTP server
python3 -m http.server 8080 &
# Then open: http://localhost:8080/web/index.html

# Option B: just open the file directly
open web/index.html          # macOS
xdg-open web/index.html      # Linux
```

**What to show on screen (pan through slowly):**

1. **Banner at top:** "Every hash recomputed in this browser matches" — highlight that the hashing runs in JavaScript, not trusting any server.
2. **Cadence panel:** Show the gaps between decisions (the real GitHub Actions schedule, not a fabricated timeline).
3. **Portfolio panel:** Same $100 net gain, recomputed in-browser.
4. **Click a row** (pick dossier #46 or #24): Show the expandable detail with:
   - Bull and bear arguments with their evidence citations
   - LLM analyst claims (for seq 46+) with accepted/rejected markers
   - Rejected claims and why they failed
   - The sensitivity table (what would flip the verdict)

**Narration:**
> "The dashboard loads the ledger and recomputes every SHA-256 hash in your browser using the same RFC 8785 canonical JSON as the Python code. It doesn't trust a server — the math runs locally. Click any dossier and you see the full reasoning trail: every argument, every citation, every rejected claim with the reason, and the sensitivity analysis showing what would flip the verdict."

---

## Scene 7 — Chainlink CRE (optional, 4:00 – 4:30)

**Screen:** Terminal, `cre/` directory:

```bash
ls cre/
cat cre/README.md | head -20
```

**Narration (optional):**
> "For the second bounty, there's a Chainlink CRE workflow that anchors the ledger head on-chain. It fetches the public ledger, reads the BTC/USD Data Feed on Sepolia, and writes both to a contract that only accepts reports from the CRE forwarder with increasing sequence numbers. The workflow and contract are tested; a live deployment is the next step."

---

## Scene 8 — Tests (optional, 4:30 – 4:45)

**Command:**

```bash
python3 -m unittest discover -s tests
```

**Expected output:**

```
..........................................................
----------------------------------------------------------------------
Ran 129 tests in 3.646s

OK
```

**Narration:**
> "129 tests, standard library only — no pip install needed. The canonical JSON hash is verified against shared test vectors between Python and JavaScript."

---

## Quick Reference Card

| Step | Command | Runtime | Notes |
|---|---|---|---|
| Decide | `python3 -m verdict_desk decide BTCUSDT --no-news --default-feeds` | ~5-15s | Needs `MISTRAL_API_KEY` for LLM debate |
| Verify | `python3 -m verdict_desk verify` | ~0.5s | "Chain intact: 53 dossiers" |
| Replay | `python3 -m verdict_desk replay` | ~1s | All 53 match |
| Portfolio | `python3 -m verdict_desk portfolio` | ~0.5s | 2 positions shown |
| Dashboard | `open web/index.html` or `xdg-open web/index.html` | instant | Hash recomputed in-browser |
| Tests | `python3 -m unittest discover -s tests` | ~4s | 129 tests, stdlib only |
| CRE | `ls cre/` | instant | Tests written, deploy pending |

## Recording tips

- **Terminal:** Use a dark theme, large font (16px+), good contrast.
- **Browser:** Show the full window, not zoomed in. Use Chrome or Firefox.
- **Pacing:** Pause 1-2 seconds after each command before speaking.
- **Voice:** If adding voice, record it separately and overlay in editing — don't narrate while typing.
- **Edit points:** Each scene is a clean cut. Record each command separately, then splice.
- **Aspect ratio:** 16:9. Terminal 60% left, browser 60% right in split-screen for Scene 6.
- **Previous demo:** `web/demo/verdict-desk-demo.mp4` (2 min, no voice) — use as a pacing reference but this one should be longer with narration.

## Post-recording checklist

- [ ] All commands ran successfully with real output (no fakes)
- [ ] Ledger restored if you did the tamper demo
- [ ] Dashboard shows "Every hash recomputed in this browser matches"
- [ ] Audio levels balanced if voiceover added
- [ ] Final video 3-5 minutes
- [ ] Save to `web/demo/` for the GitHub Pages site
