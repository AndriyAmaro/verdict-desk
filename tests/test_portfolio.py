import unittest

from verdict_desk import portfolio


def dossier(seq, action, t_entry, candles, entry=100.0, stop=98.0, take=104.0, size=10.0):
    v = {"action": action}
    if action != "FLAT":
        v.update(entry=entry, stop=stop, take_profit=take, size=size)
    return {"seq": seq, "verdict": v, "evidence": {"symbol": "BTCUSDT", "market": {"candles": candles}}}


def c(t, lo, hi, close):
    return {"t": t, "o": close, "h": hi, "l": lo, "c": close, "v": 1}


class PortfolioTest(unittest.TestCase):
    def test_take_profit_hit(self):
        ledger = [dossier(1, "LONG", 1, [c(1, 99, 101, 100)]), dossier(2, "FLAT", 3, [c(1, 99, 101, 100), c(2, 100, 105, 104)])]
        s = portfolio.summarize(ledger)
        self.assertEqual(s["positions"][0]["status"], "TAKE")
        self.assertEqual(s["positions"][0]["pnl"], 40.0)
        self.assertEqual(s["win_rate_pct"], 100.0)

    def test_stop_wins_when_both_in_same_candle(self):
        ledger = [dossier(1, "LONG", 1, [c(1, 99, 101, 100)]), dossier(2, "FLAT", 2, [c(2, 97, 105, 101)])]
        p = portfolio.summarize(ledger)["positions"][0]
        self.assertEqual(p["status"], "STOP")
        self.assertEqual(p["pnl"], -20.0)

    def test_short_open_marked_to_last_close_and_not_realized(self):
        ledger = [dossier(1, "SHORT", 1, [c(1, 99, 101, 100)], stop=102, take=96), dossier(2, "FLAT", 2, [c(2, 98, 101, 99)])]
        s = portfolio.summarize(ledger)
        self.assertEqual(s["positions"][0]["status"], "OPEN")
        self.assertEqual(s["unrealized_pnl"], 10.0)
        self.assertEqual(s["realized_pnl"], 0)
        self.assertIsNone(s["win_rate_pct"])

    def test_no_later_candles_means_open_zero(self):
        s = portfolio.summarize([dossier(1, "LONG", 1, [c(1, 99, 101, 100)])])
        self.assertEqual(s["positions"][0]["pnl"], 0.0)
