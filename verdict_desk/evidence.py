"""Coleta de evidencia de mercado de fontes publicas, sem chave.

Uma coleta vira um pacote congelado: tudo que os agentes usam para decidir fica
dentro dele, com a fonte e o horario. O replay roda so em cima desse pacote.
"""

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BINANCE_KLINES = "https://data-api.binance.vision/api/v3/klines"
OKX_FUNDING = "https://www.okx.com/api/v5/public/funding-rate"
GDELT_DOC = "https://api.gdeltproject.org/api/v2/doc/doc"
USER_AGENT = "verdict-desk/0.1 (+https://github.com/AndriyAmaro)"

NEWS_TERMS = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "BNB": "binance coin"}


def _get_json(url: str, params: dict, timeout: int = 20):
    full = f"{url}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(full, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return full, json.loads(response.read().decode("utf-8"))


def base_asset(symbol: str) -> str:
    return symbol.upper().removesuffix("USDT")


def parse_klines(rows: list) -> list[dict]:
    return [
        {"t": int(r[0]), "o": float(r[1]), "h": float(r[2]), "l": float(r[3]), "c": float(r[4]), "v": float(r[5])}
        for r in rows
    ]


def fetch_candles(symbol: str, interval: str, limit: int) -> dict:
    url, rows = _get_json(BINANCE_KLINES, {"symbol": symbol.upper(), "interval": interval, "limit": limit})
    return {"source": url, "interval": interval, "candles": parse_klines(rows)}


def fetch_funding(symbol: str) -> dict:
    inst = f"{base_asset(symbol)}-USDT-SWAP"
    url, body = _get_json(OKX_FUNDING, {"instId": inst})
    rate = float(body["data"][0]["fundingRate"]) if body.get("data") else None
    return {"source": url, "instrument": inst, "rate": rate}


def fetch_news(symbol: str, max_records: int = 8) -> dict:
    term = NEWS_TERMS.get(base_asset(symbol), base_asset(symbol).lower())
    params = {"query": term, "mode": "artlist", "maxrecords": max_records, "format": "json", "timespan": "1d", "sort": "datedesc"}
    try:
        url, body = _get_json(GDELT_DOC, params)
    except (ValueError, OSError) as err:
        return {"source": GDELT_DOC, "query": term, "articles": [], "error": str(err)}
    articles = [
        {"title": a.get("title", ""), "url": a.get("url", ""), "domain": a.get("domain", ""), "seen": a.get("seendate", "")}
        for a in body.get("articles", [])
    ]
    return {"source": url, "query": term, "articles": articles}


def collect(symbol: str, interval: str = "1h", limit: int = 72, with_news: bool = True) -> dict:
    """Coleta um pacote de evidencia congelado para um simbolo."""
    packet = {
        "symbol": symbol.upper(),
        "collected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "market": fetch_candles(symbol, interval, limit),
        "funding": fetch_funding(symbol),
    }
    if with_news:
        time.sleep(5)  # o GDELT aceita uma chamada a cada 5 segundos
        packet["news"] = fetch_news(symbol)
    return packet
