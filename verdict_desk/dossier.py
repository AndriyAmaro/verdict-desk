"""Dossie de decisao com hash encadeado, replay e verificacao independente.

O ledger e um JSONL: cada dossie guarda o hash do anterior, entao alterar
qualquer dossie antigo quebra a cadeia dali para frente.
"""

import hashlib
import json
from pathlib import Path

from . import agents, citations, features, llm
from .canonical import canonical

GENESIS = "0" * 64


def digest(body: dict) -> str:
    return hashlib.sha256(canonical(body)).hexdigest()


def read_ledger(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def analyst_layer(packet: dict, ask=None, feats: dict | None = None) -> dict | None:
    """Agentes LLM presos a evidencia. Sem chave (e sem `ask` injetado) devolve None.

    A saida validada fica congelada no dossie; o juiz segue deterministico.
    """
    if ask is None and not llm.available():
        return None
    items = citations.index(packet, feats if feats is not None else features.compute(packet))
    layer = {"model": llm.MODEL, "evidence_index": items}
    for side in ("bull", "bear"):
        try:
            claims = llm.argue(side, items, **({"ask": ask} if ask else {}))
        except (OSError, ValueError, KeyError) as err:
            layer[side] = {"accepted": [], "rejected": [], "error": str(err)}
            continue
        layer[side] = citations.validate(claims, items)
    return layer


def build(packet: dict, prev_hash: str, seq: int, ask=None, use_llm: bool = True) -> dict:
    feats = features.compute(packet)
    debate = agents.decide(feats)
    layer = analyst_layer(packet, ask, feats) if use_llm else None
    body = {
        "seq": seq,
        "prev_hash": prev_hash,
        "evidence": packet,
        "features": feats,
        "bull": debate["bull"],
        "bear": debate["bear"],
        "verdict": debate["verdict"],
        "sensitivity": debate["sensitivity"],
    }
    if layer is not None:
        body["llm"] = layer
    return {**body, "hash": digest(body)}


def append(packet: dict, path: Path, ask=None) -> dict:
    ledger = read_ledger(path)
    prev = ledger[-1]["hash"] if ledger else GENESIS
    dossier = build(packet, prev, len(ledger) + 1, ask)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(dossier, ensure_ascii=False) + "\n")
    return dossier


def replay(dossier: dict) -> dict:
    """Refaz a decisao so com a evidencia congelada e compara com o registrado."""
    feats = features.compute(dossier["evidence"])
    debate = agents.decide(feats)
    same = feats == dossier["features"] and debate["verdict"] == dossier["verdict"] and debate["sensitivity"] == dossier.get("sensitivity", debate["sensitivity"])
    result = {"seq": dossier["seq"], "matches": same, "recorded": dossier["verdict"], "replayed": debate["verdict"]}
    layer = dossier.get("llm")
    if layer:
        # A saida do LLM nao se refaz; o replay confere que as citacoes seguem validas na evidencia congelada.
        items = citations.index(dossier["evidence"], dossier["features"])
        recheck = all(
            citations.validate(layer[side]["accepted"], items)["rejected"] == [] for side in ("bull", "bear") if side in layer
        )
        result["llm_citations_valid"] = recheck and items == layer["evidence_index"]
        result["matches"] = same and result["llm_citations_valid"]
    return result


def verify(ledger: list[dict]) -> list[str]:
    """Lista os problemas da cadeia; lista vazia significa cadeia integra."""
    problems = []
    prev = GENESIS
    for dossier in ledger:
        body = {k: v for k, v in dossier.items() if k != "hash"}
        if dossier["prev_hash"] != prev:
            problems.append(f"seq {dossier['seq']}: prev_hash does not match the previous dossier")
        if digest(body) != dossier["hash"]:
            problems.append(f"seq {dossier['seq']}: content was altered after it was recorded")
        prev = dossier["hash"]
    return problems


def head(ledger: list[dict]) -> dict:
    """Ponta da cadeia para publicar e ancorar (fluxo CRE). Recusa cadeia quebrada ou vazia."""
    if not ledger:
        raise ValueError("the ledger is empty; nothing to anchor")
    problems = verify(ledger)
    if problems:
        raise ValueError("refusing to publish the head of a broken chain: " + "; ".join(problems))
    last = ledger[-1]
    return {"seq": last["seq"], "hash": last["hash"], "symbol": last["evidence"]["symbol"]}
