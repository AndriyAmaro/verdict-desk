"""Debate touro/urso v2 com indicadores tecnicos avancados (RSI, MACD, Bollinger).

Mantem compatibilidade com v1 (mesmo juiz, mesma hash chain).
Adiciona argumentos baseados em indicadores que geram edge mais alto.
"""

from typing import NamedTuple

RULES_VERSION = "v2"
ENTRY_THRESHOLD = 1.5  # Reduced from 2.0 to allow more decisions while still requiring real signal
MAX_RISK_PCT = 1.0
STOP_ATR = 1.5
TAKE_ATR = 3.0


class Rules(NamedTuple):
    version: str = RULES_VERSION
    entry_threshold: float = ENTRY_THRESHOLD
    stop_atr: float = STOP_ATR
    take_atr: float = TAKE_ATR
    max_risk_pct: float = MAX_RISK_PCT


V2 = Rules()


def _arg(claim: str, ref: str, value, weight: float) -> dict:
    return {"claim": claim, "evidence_ref": ref, "value": value, "weight": weight}


def bull(f: dict) -> list[dict]:
    args = []
    # === Indicadores v1 (mantidos) ===
    if f["ema_fast"] > f["ema_slow"]:
        args.append(_arg("Short-term trend above long-term trend", "features.ema_fast>ema_slow", [f["ema_fast"], f["ema_slow"]], 1.5))
    if f["last_close"] > f["range_high_24"]:
        args.append(_arg("Close broke above the 24-candle range high", "features.range_high_24", f["range_high_24"], 2.0))
    if f["return_24"] > 2:
        args.append(_arg("Strong momentum over the last 24 candles", "features.return_24", f["return_24"], 0.75))
    if f["volume_ratio"] > 1.5 and f["return_24"] > 0:
        args.append(_arg("Rising price on above-average volume", "features.volume_ratio", f["volume_ratio"], 0.75))
    if f["funding_rate"] is not None and f["funding_rate"] < 0:
        args.append(_arg("Negative funding: shorts are paying, crowded short side", "features.funding_rate", f["funding_rate"], 0.5))
    if f["news"]["bullish"] > f["news"]["bearish"]:
        args.append(_arg("News flow leans positive", "features.news.bullish_titles", f["news"]["bullish_titles"], 0.5))

    # === Novos indicadores v2 ===
    # RSI oversold = bounce coming
    if f.get("rsi_14") is not None and f["rsi_14"] < 35:
        args.append(_arg("RSI oversold (<35): bounce likely", "features.rsi_14", f["rsi_14"], 1.25))
    # MACD bullish crossover
    if f.get("macd_histogram") is not None and f["macd_histogram"] > 0:
        args.append(_arg("MACD histogram positive: bullish momentum", "features.macd_histogram", f["macd_histogram"], 1.0))
    # Bollinger: price at lower band = oversold
    if f.get("bb_pct_b") is not None and f["bb_pct_b"] < 0.1:
        args.append(_arg("Price near Bollinger lower band (%B<0.1): oversold", "features.bb_pct_b", f["bb_pct_b"], 1.0))
    # Volume surge confirmation
    if f["volume_ratio"] > 2.0:
        args.append(_arg("Volume surge (>2x average): strong conviction", "features.volume_ratio", f["volume_ratio"], 1.0))
    # Mean reversion from Bollinger lower
    if f.get("bb_lower") is not None and f["last_close"] < f["bb_lower"]:
        args.append(_arg("Price below Bollinger lower band: mean reversion likely", "features.bb_lower", f["bb_lower"], 1.25))
    return args


def bear(f: dict) -> list[dict]:
    args = []
    # === Indicadores v1 (mantidos) ===
    if f["ema_fast"] < f["ema_slow"]:
        args.append(_arg("Short-term trend below long-term trend", "features.ema_fast<ema_slow", [f["ema_fast"], f["ema_slow"]], 1.5))
    if f["last_close"] < f["range_low_24"]:
        args.append(_arg("Close broke below the 24-candle range low", "features.range_low_24", f["range_low_24"], 2.0))
    if f["return_24"] < -2:
        args.append(_arg("Strong downside momentum over the last 24 candles", "features.return_24", f["return_24"], 1.0))
    if f["return_24"] < -4:
        args.append(_arg("Severe drop over 24 candles: selloff intensifying", "features.return_24", f["return_24"], 1.5))
    if f["volume_ratio"] > 1.5 and f["return_24"] < 0:
        args.append(_arg("Falling price on above-average volume", "features.volume_ratio", f["volume_ratio"], 0.75))
    if f["funding_rate"] is not None and f["funding_rate"] > 0.0005:
        args.append(_arg("High positive funding: longs are crowded", "features.funding_rate", f["funding_rate"], 0.5))
    if f["news"]["bearish"] > f["news"]["bullish"]:
        args.append(_arg("News flow leans negative", "features.news.bearish_titles", f["news"]["bearish_titles"], 0.5))

    # === Novos indicadores v2 ===
    # RSI overbought = pullback coming
    if f.get("rsi_14") is not None and f["rsi_14"] > 65:
        args.append(_arg("RSI elevated (>65): overbought, pullback risk", "features.rsi_14", f["rsi_14"], 1.0))
    if f.get("rsi_14") is not None and f["rsi_14"] > 75:
        args.append(_arg("RSI very high (>75): extreme overbought", "features.rsi_14", f["rsi_14"], 1.25))
    # MACD bearish crossover
    if f.get("macd_histogram") is not None and f["macd_histogram"] < 0:
        args.append(_arg("MACD histogram negative: bearish momentum", "features.macd_histogram", f["macd_histogram"], 1.0))
    # Bollinger: price at upper band = overbought
    if f.get("bb_pct_b") is not None and f["bb_pct_b"] > 0.85:
        args.append(_arg("Price near Bollinger upper band (%B>0.85): stretched", "features.bb_pct_b", f["bb_pct_b"], 1.0))
    if f.get("bb_pct_b") is not None and f["bb_pct_b"] > 0.95:
        args.append(_arg("Price above Bollinger upper band (%B>0.95): extreme", "features.bb_pct_b", f["bb_pct_b"], 1.25))
    # Mean reversion from Bollinger upper
    if f.get("bb_upper") is not None and f["last_close"] > f["bb_upper"]:
        args.append(_arg("Price above Bollinger upper: mean reversion due", "features.bb_upper", f["bb_upper"], 1.25))
    # Divergence: price up but momentum weakening
    if f.get("macd_histogram") is not None and f["return_24"] > 0 and f["macd_histogram"] < 0:
        args.append(_arg("Price up but MACD negative: bearish divergence", "features.macd_histogram", f["macd_histogram"], 1.5))
    # Price below both EMAs = strong downtrend
    if f["last_close"] < f["ema_fast"] < f["ema_slow"]:
        args.append(_arg("Price below both EMAs: confirmed downtrend", "features.ema_fast<ema_slow", [f["ema_fast"], f["ema_slow"]], 1.0))
    # Close at/near 24-candle low = distribution
    if f["last_close"] <= f["range_low_24"] * 1.002:
        args.append(_arg("Close at 24-candle low: distribution pattern", "features.range_low_24", f["range_low_24"], 0.75))
    return args


def _action(edge: float, rules: Rules) -> str:
    if edge >= rules.entry_threshold:
        return "LONG"
    if edge <= -rules.entry_threshold:
        return "SHORT"
    return "FLAT"


def sensitivity(bull_args: list[dict], bear_args: list[dict], rules: Rules = V2) -> dict:
    edge = round(sum(a["weight"] for a in bull_args) - sum(a["weight"] for a in bear_args), 4)
    base = _action(edge, rules)
    drops = []
    for side, args in (("bull", bull_args), ("bear", bear_args)):
        for a in args:
            without = round(edge - a["weight"] if side == "bull" else edge + a["weight"], 4)
            action = _action(without, rules)
            drops.append({"side": side, "claim": a["claim"], "weight": a["weight"], "edge_without": without, "action_without": action, "flips": action != base})
    return {
        "edge": edge,
        "needs_for_long": max(0.0, round(rules.entry_threshold - edge, 4)),
        "needs_for_short": max(0.0, round(rules.entry_threshold + edge, 4)),
        "drop_one": drops,
    }


def judge(f: dict, bull_args: list[dict], bear_args: list[dict], capital: float = 10_000.0, rules: Rules = V2) -> dict:
    bull_score = sum(a["weight"] for a in bull_args)
    bear_score = sum(a["weight"] for a in bear_args)
    edge = round(bull_score - bear_score, 4)

    # Fail-closed: evidencia de mercado vencida bloqueia a decisao em vez de
    # decidir com preco velho. O frescor vem congelado nas features, entao o
    # replay reproduz o mesmo bloqueio. Dossies antigos nao tem a chave e
    # seguem decidindo como sempre decidiram.
    fresh = f.get("freshness")
    if fresh is not None and not fresh.get("ok", True):
        return {
            "rules_version": rules.version,
            "bull_score": bull_score,
            "bear_score": bear_score,
            "edge": edge,
            "threshold": rules.entry_threshold,
            "action": "BLOCKED_STALE",
            "rationale": (
                f"Refused to decide: {fresh.get('reason') or 'evidence is stale'}. "
                "The evidence is still frozen in this dossier so the refusal itself is auditable, "
                "but no simulated position is opened on stale prices."
            ),
            "freshness": fresh,
        }

    action = _action(edge, rules)
    verdict = {
        "rules_version": rules.version,
        "bull_score": bull_score,
        "bear_score": bear_score,
        "edge": edge,
        "threshold": rules.entry_threshold,
        "action": action,
        "rationale": (
            f"Bull {bull_score} vs bear {bear_score}: edge {edge} "
            + ("reaches" if action != "FLAT" else "does not reach")
            + f" the entry threshold of {rules.entry_threshold}."
        ),
    }
    if action == "FLAT":
        return verdict
    entry = f["last_close"]
    stop_distance = f["atr_14"] * rules.stop_atr
    direction = 1 if action == "LONG" else -1
    risk_cash = capital * rules.max_risk_pct / 100
    verdict.update(
        {
            "entry": entry,
            "stop": round(entry - direction * stop_distance, 6),
            "take_profit": round(entry + direction * f["atr_14"] * rules.take_atr, 6),
            "size": round(risk_cash / stop_distance, 8),
            "risk_pct": rules.max_risk_pct,
            "simulated": True,
        }
    )
    return verdict


def decide(f: dict, rules: Rules = V2) -> dict:
    bull_args = bull(f)
    bear_args = bear(f)
    return {
        "bull": bull_args,
        "bear": bear_args,
        "verdict": judge(f, bull_args, bear_args, rules=rules),
        "sensitivity": sensitivity(bull_args, bear_args, rules),
    }
