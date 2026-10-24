"""Bitcoin timestamps: the third-party clock that needs no wallet.

The Sepolia anchor proves custody through a contract we deployed. This is independent of us in a
different way: the published head is submitted to OpenTimestamps calendars, which commit the digest
into a Bitcoin block. No key, no funds, no account — which matters, because the on-chain cadence
pauses whenever the CI secrets are missing and this does not.

The trap this file guards against: a `.ots` proof proves *the exact bytes that were stamped*. If
each hourly run overwrote one proof file, every earlier proof would stop verifying with no error
anywhere. So proofs are archived per record, and the tests below pin that down.
"""

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAMPS = ROOT / "ledger" / "timestamps"
OTS = shutil.which("ots")
MAGIC = b"\x00OpenTimestamps\x00\x00Proof\x00"


def ledger():
    return {d["seq"]: d for d in
            (json.loads(l) for l in (ROOT / "ledger" / "ledger.jsonl").read_text().splitlines() if l.strip())}


@unittest.skipUnless(STAMPS.is_dir() and any(STAMPS.glob("*.ots")), "no archived timestamp proofs yet")
class TimestampTest(unittest.TestCase):
    def proofs(self):
        return sorted(STAMPS.glob("*.json.ots"))

    def test_proofs_are_archived_per_record_not_overwritten(self):
        self.assertGreaterEqual(len(self.proofs()), 1)
        for proof in self.proofs():
            snapshot = proof.with_suffix("")
            self.assertTrue(snapshot.exists(), f"{proof.name} has no snapshot next to it")

    def test_each_proof_is_a_real_opentimestamps_file(self):
        for proof in self.proofs():
            self.assertTrue(proof.read_bytes().startswith(MAGIC), f"{proof.name} is not an OTS proof")

    def test_each_snapshot_is_the_head_of_that_record(self):
        rows = ledger()
        for snapshot in STAMPS.glob("*.json"):
            seq = int(snapshot.stem)
            head = json.loads(snapshot.read_text())
            self.assertIn(seq, rows, f"snapshot {snapshot.name} names a seq the ledger does not contain")
            self.assertEqual(head["seq"], seq)
            self.assertEqual(head["hash"], rows[seq]["hash"],
                             f"snapshot {snapshot.name} does not match the published hash for that record")

    @unittest.skipUnless(OTS, "the ots client is not installed")
    def test_the_ots_client_accepts_the_proofs(self):
        """Offline, node-free, and stricter than "Bitcoin blockchain".

        Plain `ots verify` needs a bitcoind to confirm the header and the calendars over the
        network, so on a bare host (or a rate-limited one) it exits 1 without ever printing the
        block — the check used to fail for the host's reasons, not the proof's. Disabling both
        (--no-bitcoin, --no-default-whitelist) keeps what actually matters and is instant: the
        client reads the proof and names the Bitcoin block whose merkle root commits our digest.
        A pending proof must still say so out loud; anything else is a proof we cannot date.
        """
        BLOCK = re.compile(r"Bitcoin block (\d+) has merkleroot ([0-9a-f]{64})")
        confirmed = []
        for proof in self.proofs():
            run = subprocess.run(
                [OTS, "--no-bitcoin", "--no-default-whitelist", "verify", str(proof)],
                capture_output=True, text=True, timeout=60)
            text = run.stdout + run.stderr
            self.assertNotIn("Error", text, f"the client errored on {proof.name}:\n{text[:400]}")
            blocks = BLOCK.findall(text)
            if blocks:
                confirmed.append((proof.name, blocks))
            else:
                self.assertIn("Pending confirmation in Bitcoin blockchain", text,
                              f"the client neither confirmed nor dated {proof.name}:\n{text[:400]}")
        self.assertTrue(confirmed, "no archived proof is committed to a Bitcoin block yet")
        for name, blocks in confirmed:
            for height, _root in blocks:
                self.assertGreater(int(height), 800_000, f"{name} names an implausible block height")




if __name__ == "__main__":
    unittest.main()
