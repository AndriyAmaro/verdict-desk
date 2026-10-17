"""Carteira simulada: resolve cada posicao do ledger contra candles posteriores.

Nada e inventado: o resultado de uma posicao so usa candles que aparecem na
evidencia congelada de dossies registrados depois dela. Se stop e alvo caem no
mesmo candle, vale o stop (hipotese conservadora). Sem candle posterior, a
posicao fica OPEN e nao conta no resultado realizado.
"""

START_CAPITAL = 10_000.0


def _last_candle_time(dossier: dict) -> int:
    return dossier["evidence"]["market"]["candles"][-1]["t"]


def _later_candles(ledger: list[dict], index: int) -> list[dict]:
    """Candles de dossies posteriores do mesmo simbolo, sem repeticao, em ordem."""
    symbol = ledger[index]["evidence"]["symbol"]
    entry_t = _last_candle_time(ledger[index])
    seen, out = set(), []
    for later in ledger[index + 1 :]:
        if later["evidence"]["symbol"] != symbol:
            continue
        for c in later["evidence"]["market"]["candles"]:
            if c["t"] > entry_t and c["t"] not in seen:
                seen.add(c["t"])
                out.append(c)
    return sorted(out, key=lambda c: c["t"])


def resolve(dossier: dict, candles: list[dict]) -> dict:
    v = dossier["verdict"]
    direction = 1 if v["action"] == "LONG" else -1
    base = {"seq": dossier["seq"], "symbol": dossier["evidence"]["symbol"], "action": v["action"], "entry": v["entry"]}
    for bars, c in enumerate(candles, 1):
        hit_stop = c["l"] <= v["stop"] if direction == 1 else c["h"] >= v["stop"]
        hit_take = c["h"] >= v["take_profit"] if direction == 1 else c["l"] <= v["take_profit"]
        if hit_stop or hit_take:
            exit_price = v["stop"] if hit_stop else v["take_profit"]
            pnl = (exit_price - v["entry"]) * direction * v["size"]
            return {**base, "status": "STOP" if hit_stop else "TAKE", "exit": exit_price, "pnl": round(pnl, 4), "bars": bars}
    if candles:
        mark = candles[-1]["c"]
        return {**base, "status": "OPEN", "exit": mark, "pnl": round((mark - v["entry"]) * direction * v["size"], 4), "bars": len(candles)}
    return {**base, "status": "OPEN", "exit": v["entry"], "pnl": 0.0, "bars": 0}


def summarize(ledger: list[dict]) -> dict:
    positions = [
        resolve(d, _later_candles(ledger, i)) for i, d in enumerate(ledger) if d["verdict"]["action"] != "FLAT"
    ]
    closed = [p for p in positions if p["status"] != "OPEN"]
    wins = [p for p in closed if p["pnl"] > 0]
    realized = round(sum(p["pnl"] for p in closed), 4)
    unrealized = round(sum(p["pnl"] for p in positions if p["status"] == "OPEN"), 4)
    equity, peak, max_dd = START_CAPITAL, START_CAPITAL, 0.0
    for p in closed:
        equity += p["pnl"]
        peak = max(peak, equity)
        max_dd = max(max_dd, (peak - equity) / peak * 100)
    return {
        "decisions": len(ledger),
        "flat": sum(1 for d in ledger if d["verdict"]["action"] == "FLAT"),
        "positions": positions,
        "closed": len(closed),
        "open": len(positions) - len(closed),
        "win_rate_pct": round(len(wins) / len(closed) * 100, 1) if closed else None,
        "realized_pnl": realized,
        "unrealized_pnl": unrealized,
        "max_drawdown_pct": round(max_dd, 2),
        "start_capital": START_CAPITAL,
    }
