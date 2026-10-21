#!/usr/bin/env bash
# GENERATE_DEMO.sh - Cria video demo automatizado do Verdict Desk
# Usa asciinema para gravar terminal + ffmpeg para juntar com dashboard

set -e

REPO="/tmp/verdict-desk-work"
OUTPUT="$REPO/web/demo/verdict-desk-demo-v3.mp4"
CAST_FILE="/tmp/verdict-desk-demo.cast"

cd "$REPO"

# The public ledger is appended by the hourly workflow only. The "fresh decision" of the demo goes to a
# scratch copy: dossiers 54 to 68 of the public chain are demo runs that ended up there by mistake.
SCRATCH="$(mktemp -d)/ledger.jsonl"
cp ledger/ledger.jsonl "$SCRATCH"

# Source Mistral key
source ~/.hermes/.env 2>/dev/null
export MISTRAL_API_KEY="${HERMES_CUSTOM_API_MISTRAL_AI_API_KEY:-}"
export PATH="$HOME/.cre/bin:$HOME/.bun/bin:$PATH"

echo "🎬 Gerando Verdict Desk Demo v3..."
echo ""

# Check if asciinema is available
if ! command -v asciinema &> /dev/null; then
    echo "⚠️ asciinema not found. Installing via pip..."
    pip3 install asciinema --quiet 2>/dev/null || pip install asciinema --quiet 2>/dev/null
fi

if ! command -v asciinema &> /dev/null; then
    echo "❌ asciinema still not available. Falling back to text capture..."
    # Fallback: capture outputs to file
    {
        echo "=== Verdict Desk Demo v3 ==="
        echo "Date: $(date -u)"
        echo "Commit: $(git log --oneline -1)"
        echo "Dossiers: $(wc -l < ledger/ledger.jsonl)"
        echo ""
        echo "$ git log --oneline -5"
        git log --oneline -5
        echo ""
        echo "$ python3 -m verdict_desk verify"
        python3 -m verdict_desk verify
        echo ""
        echo "$ python3 -m verdict_desk --ledger scratch-copy.jsonl decide-v2 BTCUSDT --no-news"
        python3 -m verdict_desk --ledger "$SCRATCH" decide-v2 BTCUSDT --no-news 2>&1
        echo ""
        echo "$ python3 -m verdict_desk replay"
        python3 -m verdict_desk replay 2>&1 | tail -10
        echo ""
        echo "$ python3 -m verdict_desk portfolio"
        python3 -m verdict_desk portfolio
        echo ""
        echo "$ python3 -m verdict_desk learn"
        python3 -m verdict_desk learn
        echo ""
        echo "$ python3 -m unittest discover -s tests"
        python3 -m unittest discover -s tests 2>&1 | tail -5
        echo ""
        echo "$ ls cre/"
        ls cre/
        echo ""
        echo "=== Demo Complete ==="
    } > /tmp/verdict-desk-demo-output.txt
    echo "✅ Demo output saved to /tmp/verdict-desk-demo-output.txt"
    echo "📁 Copy this text into a screen recorder for the video."
    exit 0
fi

# Test count from a real run, not a constant
TESTS="$(python3 -m unittest discover -s tests 2>&1 | sed -n 's/^Ran \([0-9]*\) tests.*/\1/p')"

# Record with asciinema
echo "📹 Recording terminal session..."
asciinema rec "$CAST_FILE" -c "bash -c '
cd $REPO
source ~/.hermes/.env 2>/dev/null
export MISTRAL_API_KEY=\"\${HERMES_CUSTOM_API_MISTRAL_AI_API_KEY:-}\"

echo \"=== Verdict Desk - Audit-Grade AI Decisions ===\"
echo \"\"
echo \"\$(git log --oneline -1)\"
echo \"\$(wc -l < ledger/ledger.jsonl) dossiers | $TESTS tests | LIVE\"
echo \"\"

echo \"1️⃣  Verify hash chain...\"
python3 -m verdict_desk verify
echo \"\"

echo \"2️⃣  Fresh v2 decision (recorded in a scratch copy of the ledger)...\"
python3 -m verdict_desk --ledger $SCRATCH decide-v2 BTCUSDT --no-news
echo \"\"

echo \"3️⃣  Replay all decisions...\"
python3 -m verdict_desk replay 2>&1 | tail -5
echo \"\"

echo \"4️⃣  Portfolio...\"
python3 -m verdict_desk portfolio
echo \"\"

echo \"5️⃣  Learning report...\"
python3 -m verdict_desk learn
echo \"\"

echo \"6️⃣  Tests...\"
python3 -m unittest discover -s tests 2>&1 | tail -3
echo \"\"

echo \"7️⃣  CRE workflow...\"
ls cre/anchor/*.ts cre/anchor/*.yaml
echo \"\"

echo \"✅ Demo complete - all systems operational\"
'" --overwrite 2>&1

echo ""
echo "🎞️  Converting to MP4..."

# Convert asciinema to MP4 using agg (asciinema gif generator) or python
if command -v agg &> /dev/null; then
    agg "$CAST_FILE" /tmp/verdict-desk-demo.gif
    ffmpeg -y -i /tmp/verdict-desk-demo.gif -vf "scale=1280:720" -c:v libx264 -pix_fmt yuv420p "$OUTPUT" 2>/dev/null
else
    # Use python-based converter or just copy the cast
    python3 -c "
import json, sys

# Read the cast file and generate a simple HTML that can be screen-recorded
cast = json.load(open('$CAST_FILE'))
html = '''<!DOCTYPE html>
<html><head><meta charset=utf-8><title>Verdict Desk Demo</title>
<style>
body { background: #1a1b26; color: #a9b1d6; font: 16px/1.4 'JetBrains Mono', monospace; margin: 0; padding: 20px; }
pre { white-space: pre-wrap; word-wrap: break-word; }
.cursor { animation: blink 1s infinite; }
@keyframes blink { 50% { opacity: 0; } }
</style></head><body><pre id=\"output\"></pre>
<script>
const events = ''' + json.dumps(cast.get('events', cast if isinstance(cast, list) else [])) + ''';
let i = 0, text = '';
const el = document.getElementById('output');
function show() {
    if (i < events.length) {
        const [time, type, data] = events[i];
        if (type === 'o') text += data;
        el.textContent = text;
        i++;
        setTimeout(show, Math.min(events[i < events.length ? i : i-1][0] * 1000 - (i > 1 ? events[i-1][0] * 1000 : 0), 200));
    }
}
show();
</script></body></html>'''
with open('/tmp/verdict-desk-demo.html', 'w') as f:
    f.write(html)
print('HTML demo generated at /tmp/verdict-desk-demo.html')
print('Open in browser and screen-record it.')
"
fi

echo ""
echo "✅ Demo files generated:"
echo "   📹 Cast: $CAST_FILE"
echo "   🎬 Output: $OUTPUT (if conversion succeeded)"
echo ""
echo "📋 To record manually:"
echo "   1. Open: file:///tmp/verdict-desk-demo.html"
echo "   2. Screen record for ~3 minutes"
echo "   3. Save as: $OUTPUT"
echo "   4. Push to repo: git add $OUTPUT && git commit -m 'demo v3' && git push"
