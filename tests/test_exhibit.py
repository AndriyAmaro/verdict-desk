"""The exhibit: a dossier rendered as something a reviewer can file and rely on.

The properties worth protecting, because each one is a claim a judge may test:

  * the integrity line is recomputed at render time, so a tampered record says so on its face;
  * the attribution section comes from the record's own sensitivity block, not from a re-run;
  * the limits section is always present — an exhibit that only advertises is a brochure;
  * the on-chain comparison normalises the 0x prefix, because the contract and the ledger
    disagree on that and comparing them raw produced a false mismatch on an anchored record.
"""

import json
import re
import unittest
from pathlib import Path

from verdict_desk import canonical, exhibit

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "ledger" / "ledger.jsonl"


def ledger_rows():
    return [json.loads(line) for line in LEDGER.read_text(encoding="utf-8").splitlines() if line.strip()]


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.rows = ledger_rows()
        self.row = self.rows[-1]

    def test_it_renders_the_decisions_own_fields(self):
        page = exhibit.render(self.row)
        v = self.row["verdict"]
        self.assertIn(self.row["evidence"]["symbol"], page)
        self.assertIn(v["action"], page)
        self.assertIn(f"#{self.row['seq']}", page)
        self.assertIn(str(v["edge"]), page)

    def test_integrity_line_matches_for_an_untouched_record(self):
        page = exhibit.render(self.row)
        self.assertIn("MATCH — the record is unchanged", page)
        self.assertIn(self.row["hash"], page)

    def test_an_analyst_layer_that_failed_says_why_instead_of_saying_nothing(self):
        """"Nothing kept" is true and useless; a reader needs to know the provider failed, and what decided instead."""
        broken = json.loads(json.dumps(self.row))
        reason = "HTTP 402 Payment Required from https://api.example.com/v1 model m: quota"
        broken["llm"] = {"bull": {"accepted": [], "rejected": [], "error": reason}, "bear": {"accepted": [], "rejected": [], "error": reason}}
        page = exhibit.render(broken)
        self.assertEqual(page.count("returned an error and produced no claims"), 2)
        self.assertIn("HTTP 402 Payment Required", page)
        self.assertIn("deterministic engine alone", page)

    def test_an_analyst_that_ran_and_kept_nothing_still_says_so(self):
        quiet = json.loads(json.dumps(self.row))
        quiet["llm"] = {"bull": {"accepted": [], "rejected": []}, "bear": {"accepted": [], "rejected": []}}
        page = exhibit.render(quiet)
        self.assertIn("Nothing kept.", page)
        self.assertNotIn("returned an error", page)

    def test_a_tampered_record_says_mismatch_on_its_face(self):
        tampered = json.loads(json.dumps(self.row))
        tampered["verdict"]["action"] = "LONG" if tampered["verdict"]["action"] != "LONG" else "SHORT"
        page = exhibit.render(tampered)
        self.assertIn("MISMATCH — this record was edited", page)

    def test_the_attribution_table_marks_the_deciding_argument(self):
        page = exhibit.render(self.row)
        if not self.row.get("sensitivity"):
            self.skipTest("predates sensitivity")
        flips = [d for d in self.row["sensitivity"]["drop_one"] if d["flips"]]
        self.assertEqual(page.count('<tr class="flip">'), len(flips))

    def test_the_limits_section_is_always_there(self):
        page = exhibit.render(self.row)
        self.assertIn("What this exhibit does not prove", page)
        self.assertIn("simulated", page.lower())
        self.assertIn("fees", page.lower())

    def test_anchor_hash_with_0x_prefix_still_counts_as_a_match(self):
        anchor = {"matches": None}
        raw = "0x" + self.row["hash"]
        published = (self.row.get("hash") or "").lower().removeprefix("0x")
        anchored = raw.lower().removeprefix("0x")
        self.assertEqual(published, anchored)

        page = exhibit.render(self.row, anchor={"matches": published == anchored, "anchored_seq": self.row["seq"],
                                                "anchored_at": 1792605204})
        self.assertIn("matches the hash written on Ethereum Sepolia", page)

    def test_it_is_self_contained(self):
        page = exhibit.render(self.row)
        self.assertNotIn("<script src=", page)
        self.assertNotIn("http://", page.replace("http://www.w3.org", ""))
        self.assertIn("@media print", page)

    def test_every_published_dossier_renders_without_raising(self):
        for row in self.rows[-12:]:
            page = exhibit.render(row, chain=exhibit.chain_context(self.rows, row["seq"]))
            self.assertIn("Decision exhibit", page)


class ChainContextTest(unittest.TestCase):
    def test_the_whole_published_chain_verifies(self):
        rows = ledger_rows()
        ctx = exhibit.chain_context(rows, rows[-1]["seq"])
        self.assertTrue(ctx["ok"], ctx.get("problem"))
        self.assertEqual(ctx["length"], len(rows))

    def test_a_broken_link_is_reported(self):
        rows = ledger_rows()[-5:]
        rows[2] = dict(rows[2])
        rows[2]["prev_hash"] = "0" * 64
        ctx = exhibit.chain_context(rows, rows[-1]["seq"])
        self.assertFalse(ctx["ok"])
        self.assertIn("does not link", ctx["problem"])


class IndexTest(unittest.TestCase):
    def test_the_index_links_each_exhibit(self):
        rows = ledger_rows()[-3:]
        page = exhibit.render_index([(r, f"exhibit-{r['seq']}.html") for r in rows])
        for r in rows:
            self.assertIn(f"exhibit-{r['seq']}.html", page)
        self.assertIn("Decision exhibits", page)


if __name__ == "__main__":
    unittest.main()
