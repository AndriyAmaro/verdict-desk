#!/usr/bin/env bash
# RECORD_DEMO.sh - Run all demo commands in sequence for screen recording
# Usage: ./RECORD_DEMO.sh
# 
# Before running:
# 1. Open a terminal with dark theme, large font (16px+)
# 2. Start screen recording (OBS, SimpleScreenRecorder, etc.)
# 3. Run: ./RECORD_DEMO.sh
# 4. Stop recording when done (~4 minutes)

set -e

REPO_DIR="/tmp/verdict-desk-work"
cd "$REPO_DIR"

# The public ledger is appended by the hourly workflow only. The "fresh decision" of the demo goes to a
# scratch copy: dossiers 54 to 68 of the public chain are demo runs that ended up there by mistake.
SCRATCH="$(mktemp -d)/ledger.jsonl"
cp ledger/ledger.jsonl "$SCRATCH"

echo "=========================================="
echo "Verdict Desk: Demo Recording Script"
echo "=========================================="
echo ""

# Scene 0: Setup
echo "📦 Scene 0: Setup"
echo "----------------------------------------"
echo "$ git log --oneline -5"
git log --oneline -5
echo ""
echo "$ wc -l ledger/ledger.jsonl"
wc -l ledger/ledger.jsonl
echo ""
sleep 2

# Scene 1: Fresh decision
echo "🎯 Scene 1: Fresh Decision"
echo "----------------------------------------"
echo "$ python3 -m verdict_desk --ledger scratch-copy.jsonl decide BTCUSDT --no-news --default-feeds"
python3 -m verdict_desk --ledger "$SCRATCH" decide BTCUSDT --no-news --default-feeds
echo ""
sleep 3

# Scene 2: LLM debate deep-dive
echo "💬 Scene 2: LLM Debate (dossier #46)"
echo "----------------------------------------"
python3 -c "
import json
with open('ledger/ledger.jsonl') as f:
    dossiers = [json.loads(l) for l in f if l.strip()]
d = dossiers[45]  # seq 46
llm = d.get('llm')
if llm:
    print(f'Model: {llm[\"model\"]}')
    print(f'Bull accepted: {len(llm[\"bull\"][\"accepted\"])} claims')
    for c in llm['bull']['accepted']:
        print(f'  ✓ {c[\"claim\"][:100]}')
    print(f'Bear accepted: {len(llm[\"bear\"][\"accepted\"])} claims')
    for c in llm['bear']['accepted']:
        print(f'  ✓ {c[\"claim\"][:100]}')
else:
    print('No LLM layer for this dossier')
"
echo ""
sleep 2

# Scene 3: Verify hash chain
echo "🔗 Scene 3: Verify Hash Chain"
echo "----------------------------------------"
echo "$ python3 -m verdict_desk verify"
python3 -m verdict_desk verify
echo ""
sleep 2

# Scene 4: Replay all decisions
echo "🔄 Scene 4: Replay All Decisions"
echo "----------------------------------------"
echo "$ python3 -m verdict_desk replay"
python3 -m verdict_desk replay
echo ""
sleep 3

# Scene 5: Simulated portfolio
echo "💰 Scene 5: Simulated Portfolio"
echo "----------------------------------------"
echo "$ python3 -m verdict_desk portfolio"
python3 -m verdict_desk portfolio
echo ""
sleep 2

# Scene 6: Dashboard
echo "🌐 Scene 6: Dashboard"
echo "----------------------------------------"
echo "Opening dashboard in browser..."
if command -v xdg-open &> /dev/null; then
    xdg-open web/index.html &
    echo "Dashboard opened with xdg-open"
elif command -v open &> /dev/null; then
    open web/index.html &
    echo "Dashboard opened with open"
else
    echo "Open manually: file://$PWD/web/index.html"
fi
sleep 3

# Scene 7: CRE workflow
echo "⛓️ Scene 7: Chainlink CRE"
echo "----------------------------------------"
echo "$ ls cre/"
ls cre/
echo ""
echo "$ cat cre/README.md | head -15"
cat cre/README.md | head -15
echo ""
sleep 2

# Scene 8: Tests
echo "🧪 Scene 8: Tests"
echo "----------------------------------------"
echo "$ python3 -m unittest discover -s tests"
python3 -m unittest discover -s tests
echo ""
sleep 2

echo "=========================================="
echo "✅ Demo recording complete!"
echo "=========================================="
echo ""
echo "Save the video to: web/demo/verdict-desk-demo-v2.mp4"
echo ""
echo "Post-recording checklist:"
echo "  [ ] All commands ran successfully"
echo "  [ ] Dashboard showed 'Every hash recomputed in this browser matches'"
echo "  [ ] Final video 3-5 minutes"
echo "  [ ] Save to web/demo/verdict-desk-demo-v2.mp4"
