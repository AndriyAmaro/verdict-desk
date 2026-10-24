"""Enemy watch: track the direct rivals so a lead is measured, not assumed.

The two builds that copied our idea (Debate Desk, Bull v. Bear) are the real competition for the
$6k Autonomous Agents bounty. This script clones them, measures the things a judge can see, and
diffs against the previous run (stored in research/enemy-watch.json, committed). The scheduled
job runs it every 3 hours, so if a rival ships work, the delta shows up instead of being guessed.

Stdlib only. Never fails the run: a rival that can't be cloned is reported as unreachable, not
as a lead.
"""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCH = Path("/tmp/enemy-watch")
STATE = ROOT / "research" / "enemy-watch.json"

RIVALS = {
    "debate-desk": "https://github.com/NoBanks/debate-desk",
    "bull-v-bear": "https://github.com/Sanchay117/bull-v-bear",
}


def sh(cmd: list[str], cwd=None):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def count_lines(repo: Path) -> int:
    r = sh(["bash", "-c",
            "find . -path ./.git -prune -o -path '*/node_modules' -prune -o -type f "
            "\\( -name '*.py' -o -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.sol' -o -name '*.html' \\) "
            "-print0 | xargs -0 wc -l | tail -1"], cwd=repo)
    try:
        return int(r.stdout.split()[-2]) if r.returncode == 0 else -1
    except (IndexError, ValueError):
        return -1


def count_tests(repo: Path) -> int:
    r = sh(["bash", "-c", "find . -path ./.git -prune -o -path '*/node_modules' -prune -o -name '*.test.*' -print | wc -l"], cwd=repo)
    return int(r.stdout.strip() or 0)


def debate_desk_ledger(repo: Path) -> dict:
    """The one concrete 'real execution' claim: how many cycles actually traded."""
    ledger = repo / "data" / "ledger.jsonl"
    if not ledger.exists():
        return {}
    actions = {"HOLD": 0, "BUY": 0, "SELL": 0}
    for line in ledger.read_text().splitlines():
        if not line.strip():
            continue
        try:
            actions[json.loads(line).get("action", "?")] = actions.get(json.loads(line).get("action", "?"), 0) + 1
        except json.JSONDecodeError:
            continue
    return {"records": sum(actions.values()), **actions}


def measure(name: str, url: str) -> dict:
    repo = WATCH / name
    if not (repo / ".git").exists():
        sh(["rm", "-rf", str(repo)])
        clone = sh(["git", "clone", "-q", url, str(repo)])
        if clone.returncode != 0:
            return {"name": name, "unreachable": True}
    sh(["git", "-C", str(repo), "fetch", "-q", "origin"])
    sh(["git", "-C", str(repo), "reset", "-q", "--hard", "origin/main"])
    commits = int(sh(["git", "-C", str(repo), "rev-list", "--count", "HEAD"]).stdout.strip() or 0)
    last = sh(["git", "-C", str(repo), "log", "-1", "--format=%ci"]).stdout.strip()
    out = {"name": name, "commits": commits, "last_commit": last, "loc": count_lines(repo), "tests": count_tests(repo)}
    if name == "debate-desk":
        out["ledger"] = debate_desk_ledger(repo)
        out["transcripts"] = len(list((repo / "data" / "transcripts").glob("*.json"))) if (repo / "data" / "transcripts").exists() else 0
    return out


def main():
    prev = {}
    if STATE.exists():
        prev = json.loads(STATE.read_text())
    now = {name: measure(name, url) for name, url in RIVALS.items()}
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(now, indent=2, sort_keys=True))

    print("ENEMY WATCH")
    for name, cur in sorted(now.items()):
        if cur.get("unreachable"):
            print(f"  {name}: UNREACHABLE")
            continue
        p = prev.get(name, {})
        def delta(k):
            a, b = p.get(k), cur.get(k)
            if isinstance(a, int) and isinstance(b, int) and a != b:
                return f" (was {a})"
            return ""
        print(f"  {name}: commits={cur['commits']}{delta('commits')} loc={cur['loc']}{delta('loc')} "
              f"tests={cur['tests']}{delta('tests')} last={cur['last_commit']}")
        if "ledger" in cur:
            l = cur["ledger"]
            print(f"    ledger: {l.get('records')} records = {l.get('BUY')} BUY / {l.get('SELL')} SELL / {l.get('HOLD')} HOLD")
            print(f"    transcripts: {cur['transcripts']}")


if __name__ == "__main__":
    main()
