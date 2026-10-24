"""The published figures must equal the ledger, not someone's memory of it.

`scripts/refresh_numbers.py --check` regenerates every count from the ledger and exits 1 when any
document is out of date. This test pins that, so a doc that drifts (a stale dossier count, a claim
count, a narrative coverage line) fails the suite the same way a broken replay would. It skips the
test-count sub-check here because running the suite inside the suite would recurse; that one is
covered by running `python3 scripts/refresh_numbers.py --check` directly.
"""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class NumbersFreshTest(unittest.TestCase):
    def test_published_figures_match_the_ledger(self):
        run = subprocess.run([sys.executable, "scripts/refresh_numbers.py", "--skip-tests", "--check"],
                             cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0,
                         "a doc is out of date with the ledger; run scripts/refresh_numbers.py:\n"
                         + run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
