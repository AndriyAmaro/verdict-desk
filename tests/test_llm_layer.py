import json
import tempfile
import unittest
from pathlib import Path

from tests.test_dossier import packet
from verdict_desk import dossier


def stub(system, user):
    if "bull" in system:
        return json.dumps([{"claim": "Bitcoin rally hits record", "cites": ["E4"]}, {"claim": "Moon soon", "cites": []}])
    return "not json"


class LlmLayerTest(unittest.TestCase):
    def setUp(self):
        self.path = Path(tempfile.mkdtemp()) / "ledger.jsonl"
        self.pkt = packet(0.004, titles=("Bitcoin rally hits record",))

    def test_no_key_keeps_deterministic_core(self):
        d = dossier.build(self.pkt, dossier.GENESIS, 1)
        self.assertNotIn("llm", d)

    def test_llm_output_is_validated_frozen_and_replayed(self):
        d = dossier.append(self.pkt, self.path, ask=stub)
        self.assertEqual(len(d["llm"]["bull"]["accepted"]), 1)
        self.assertEqual(len(d["llm"]["bull"]["rejected"]), 1)
        self.assertEqual(d["llm"]["bear"]["accepted"], [])
        ledger = dossier.read_ledger(self.path)
        self.assertEqual(dossier.verify(ledger), [])
        r = dossier.replay(ledger[0])
        self.assertTrue(r["matches"] and r["llm_citations_valid"])

    def test_replay_flags_citation_that_no_longer_matches_evidence(self):
        d = dossier.append(self.pkt, self.path, ask=stub)
        d["llm"]["bull"]["accepted"][0]["claim"] = "Bitcoin rally hits 99999"
        self.assertFalse(dossier.replay(d)["matches"])

    def test_llm_failure_is_recorded_not_fatal(self):
        def boom(system, user):
            raise OSError("down")
        d = dossier.build(self.pkt, dossier.GENESIS, 1, ask=boom)
        self.assertIn("error", d["llm"]["bull"])
        self.assertTrue(dossier.replay(d)["matches"])
