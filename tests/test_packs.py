"""Evidence packs on the site: a lawyer who opens an exhibit can download the file that proves it.

The site only carries packs for the newest dossiers and the anchored one (about 90 KB each), so the
exhibit offers the download only where the file exists, and says how to produce the rest otherwise.
"""

import argparse
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from verdict_desk import __main__ as cli
from verdict_desk import dossier, exhibit

ROOT = Path(__file__).resolve().parents[1]
LEDGER = dossier.read_ledger(ROOT / "ledger" / "ledger.jsonl")


def run(outdir, recent, anchored=False):
    opts = argparse.Namespace(ledger=ROOT / "ledger" / "ledger.jsonl", recent=recent, outdir=outdir, anchored=anchored)
    with contextlib.redirect_stdout(io.StringIO()):
        return cli.cmd_packs(opts)


class PacksCommandTest(unittest.TestCase):
    def test_it_writes_one_pack_per_recent_dossier_named_by_its_seq(self):
        out = Path(tempfile.mkdtemp())
        self.assertEqual(run(out, 3), 0)
        names = sorted(p.name for p in out.glob("*.json"))
        self.assertEqual(names, sorted(f"{d['seq']}.json" for d in LEDGER[-3:]))

    def test_each_pack_recomputes_to_the_hash_it_records(self):
        out = Path(tempfile.mkdtemp())
        run(out, 2)
        for path in out.glob("*.json"):
            pack = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(pack["recomputed_hash"], pack["recorded_hash"])
            self.assertEqual(pack["format"], "verdict-desk/evidence-pack/v1")

    def test_the_anchored_dossier_is_included_even_when_it_is_not_recent(self):
        from verdict_desk import scoreboard
        anchored = scoreboard._sepolia(ROOT, LEDGER, None)["seq"]  # the newest anchor the evidence folder records; it changes whenever one is made
        out = Path(tempfile.mkdtemp())
        run(out, 1, anchored=True)
        self.assertTrue((out / f"{anchored}.json").exists(), sorted(p.name for p in out.glob("*.json")))

    def test_without_a_ledger_it_fails_instead_of_writing_nothing_silently(self):
        opts = argparse.Namespace(ledger=Path(tempfile.mkdtemp()) / "none.jsonl", recent=3, outdir=Path(tempfile.mkdtemp()), anchored=False)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli.cmd_packs(opts), 1)


class ExhibitPackLinkTest(unittest.TestCase):
    def test_with_a_pack_the_exhibit_offers_the_download_and_how_to_check_it(self):
        page = exhibit.render(LEDGER[-1], pack_href="../pack/77.json")
        self.assertIn('href="../pack/77.json"', page)
        self.assertIn("download", page)
        self.assertIn("verify.html", page)

    def test_without_a_pack_it_says_how_to_make_one_instead_of_a_dead_link(self):
        page = exhibit.render(LEDGER[-1])
        self.assertNotIn("../pack/", page)
        self.assertIn("python3 -m verdict_desk export --seq", page)

    def test_the_page_stays_self_contained_for_printing(self):
        page = exhibit.render(LEDGER[-1], pack_href="../pack/77.json")
        self.assertNotIn("<script src=", page)


if __name__ == "__main__":
    unittest.main()
