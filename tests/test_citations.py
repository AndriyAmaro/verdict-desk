import unittest

from tests.test_dossier import packet
from verdict_desk import citations, llm


class CitationsTest(unittest.TestCase):
    def setUp(self):
        self.items = citations.index(packet(0.004, titles=("Bitcoin rally hits record",)))

    def test_index_has_stable_ids(self):
        self.assertIn("E1", self.items)
        self.assertTrue(any("rally" in v for v in self.items.values()))

    def test_drops_uncited_unknown_and_invented_numbers(self):
        claims = [
            {"claim": "Bitcoin rally hits record", "cites": ["E4"]},
            {"claim": "Moon soon", "cites": []},
            {"claim": "Whales buying", "cites": ["E99"]},
            {"claim": "Funding rate is 0.77", "cites": ["E3"]},
        ]
        result = citations.validate(claims, self.items)
        self.assertEqual([c["claim"] for c in result["accepted"]], ["Bitcoin rally hits record"])
        reasons = [c["rejected_because"] for c in result["rejected"]]
        self.assertEqual(reasons[:2], ["no citation", "unknown evidence id"])
        self.assertTrue(reasons[2].startswith("number not in cited evidence"))

    def test_accepts_number_present_in_cited_item(self):
        claims = [{"claim": "Funding rate is 0.0001", "cites": ["E3"]}]
        self.assertEqual(len(citations.validate(claims, self.items)["accepted"]), 1)


class FeatureEvidenceTest(unittest.TestCase):
    def test_features_become_citable_items_after_the_market_items(self):
        from verdict_desk import features

        pkt = packet(0.004, titles=("Bitcoin rally hits record",))
        base = citations.index(pkt)
        with_feats = citations.index(pkt, features.compute(pkt))
        self.assertEqual({k: v for k, v in with_feats.items() if k in base}, base)
        extra = [v for k, v in with_feats.items() if k not in base]
        self.assertEqual(len(extra), 5)
        self.assertTrue(any(v.startswith("Trend: fast EMA") for v in extra))

    def test_claim_citing_a_feature_item_passes_the_number_check(self):
        from verdict_desk import features

        pkt = packet(0.004, titles=("Bitcoin rally hits record",))
        feats = features.compute(pkt)
        items = citations.index(pkt, feats)
        trend_id = next(k for k, v in items.items() if v.startswith("Trend: fast EMA"))
        ok = {"claim": f"Fast EMA {feats['ema_fast']} versus slow EMA {feats['ema_slow']}", "cites": [trend_id]}
        bad = {"claim": "Fast EMA 123456.7 leads", "cites": [trend_id]}
        result = citations.validate([ok, bad], items)
        self.assertEqual(len(result["accepted"]), 1)
        self.assertTrue(result["rejected"][0]["rejected_because"].startswith("number not in cited evidence"))


class LlmTest(unittest.TestCase):
    def test_parse_claims_tolerates_noise(self):
        self.assertEqual(llm.parse_claims('ok [{"claim":"a","cites":["E1"]}] done'), [{"claim": "a", "cites": ["E1"]}])
        self.assertEqual(llm.parse_claims("no json"), [])
        self.assertEqual(llm.parse_claims("[broken"), [])
        self.assertEqual(llm.parse_claims(None), [])

    def test_sides_get_opposite_stances_and_may_return_nothing(self):
        seen = {}

        def capture(system, user):
            seen[len(seen)] = system
            return "[]"

        llm.argue("bull", {"E1": "x"}, ask=capture)
        llm.argue("bear", {"E1": "x"}, ask=capture)
        self.assertIn("LONG position now", seen[0])
        self.assertIn("against a long entry", seen[1])
        self.assertIn("return fewer claims or an empty list", seen[0])

    def test_argue_uses_injected_ask(self):
        out = llm.argue("bull", {"E1": "x"}, ask=lambda s, u: '[{"claim":"x","cites":["E1"]}]')
        self.assertEqual(out[0]["cites"], ["E1"])
