import shutil
import subprocess
import unittest
from pathlib import Path

HERE = Path(__file__).parent
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "node not installed")
class AnchorLookupTest(unittest.TestCase):
    """The anchor check must give its verdict even when a public RPC has pruned the log history (cre/contracts/scripts/anchor-lookup.mjs)."""

    def test_the_log_search_walks_back_in_small_windows_and_never_throws(self):
        run = subprocess.run([NODE, str(HERE / "node_anchor_lookup.mjs")], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("all ok (11 checks)", run.stdout)


if __name__ == "__main__":
    unittest.main()
