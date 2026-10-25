"""The scheduled workflows must call commands that exist.

The hourly bot is the heartbeat of the ledger. A typo in a subcommand or a flag fails only when the
schedule fires, so a lost hour is the first sign. This reads every `python -m verdict_desk ...` line
in .github/workflows and checks, against the real command line parser, that the subcommand exists
and that each flag on the line is one it accepts. It also checks that the files the line names exist.
"""

import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
CALL = re.compile(r"python3? -m verdict_desk((?:\s+(?:--?[\w-]+(?:\s+(?!-)[^\s;|&]+)?|[A-Za-z][\w-]*(?:\s+[A-Z]{3,}USDT)*))+)")


def calls():
    found = []
    for wf in WORKFLOWS:
        for line in wf.read_text(encoding="utf-8").splitlines():
            if "python" not in line or "verdict_desk" not in line or line.lstrip().startswith("#"):
                continue
            m = CALL.search(line)
            if m:
                found.append((wf.name, line.strip(), m.group(1).split()))
    return found


def help_of(*argv):
    return subprocess.run([sys.executable, "-m", "verdict_desk", *argv, "--help"], cwd=ROOT, capture_output=True, text=True, timeout=60)


class WorkflowCallsTest(unittest.TestCase):
    def test_there_are_calls_to_check(self):
        self.assertGreaterEqual(len(calls()), 6)

    def test_every_subcommand_and_flag_used_by_a_workflow_exists(self):
        for wf, line, tokens in calls():
            # global options come before the subcommand: --ledger PATH
            rest, i = [], 0
            while i < len(tokens):
                if tokens[i] == "--ledger":
                    i += 2
                    continue
                rest.append(tokens[i])
                i += 1
            sub = next((t for t in rest if not t.startswith("-")), None)
            self.assertIsNotNone(sub, f"{wf}: no subcommand in {line!r}")
            out = help_of(sub)
            self.assertEqual(out.returncode, 0, f"{wf}: `{sub}` is not a verdict_desk command ({line!r})")
            for flag in (t for t in rest if t.startswith("--")):
                self.assertIn(flag, out.stdout, f"{wf}: `{sub}` has no {flag} option ({line!r})")

    def test_the_files_a_workflow_names_exist(self):
        for wf, line, tokens in calls():
            for i, t in enumerate(tokens):
                if t == "--config":
                    self.assertTrue((ROOT / tokens[i + 1]).is_file(), f"{wf}: {tokens[i + 1]} does not exist")

    def test_the_hourly_decision_uses_the_current_rules_and_the_users_config(self):
        hourly = (ROOT / ".github" / "workflows" / "hourly.yml").read_text(encoding="utf-8")
        self.assertIn("decide-v5", hourly)
        self.assertIn("--config config/voices.json", hourly)
        self.assertNotIn("decide-v4", hourly, "the hourly run moved to rules v5")


if __name__ == "__main__":
    unittest.main()
