"""CLI: python -m verdict_desk decide|replay|verify."""

import argparse
import json
import sys
from pathlib import Path

from . import backtest, dossier, evidence, journal, llm, narrative, portfolio, research

DEFAULT_LEDGER = Path("ledger/ledger.jsonl")


def cmd_decide(opts) -> int:
    feeds = dict(narrative.DEFAULT_FEEDS) if opts.default_feeds else {}
    for spec in opts.feed or []:
        name, _, url = spec.partition("=")
        feeds[name] = url
    block = None
    if feeds:
        # As vozes valem para todos os simbolos: busca e extracao rodam uma vez por execucao.
        voices = narrative.collect(feeds, log=lambda m: print(m, file=sys.stderr))
        ask = (lambda system, user: llm.chat(system, user, timeout=narrative.LLM_TIMEOUT, max_tokens=narrative.LLM_MAX_TOKENS)) if llm.available() else None
        block = narrative.build(voices, ask, llm.MODEL if ask else "")
        print(f"narrative ({block['method']}): {len(voices)} headlines from {len({v['name'] for v in voices})} voices, {len(block['convergence'])} convergences")
    recorded = 0
    for symbol in opts.symbols:
        try:
            packet = evidence.collect(symbol, opts.interval, with_news=not opts.no_news)
        except (OSError, ValueError, KeyError) as err:
            # Lacuna real: nada e gravado e o erro aparece, o historico nao finge uma decisao.
            print(f"{symbol}: no evidence collected, nothing recorded ({err})", file=sys.stderr)
            continue
        if block is not None:
            packet["narrative"] = block
        recorded += 1
        print_record(dossier.append(packet, opts.ledger))
    return 0 if recorded else 1


def cmd_decide_v2(opts) -> int:
    """Run the same decide flow but with agents_v2 + features_v2 (RSI, MACD, Bollinger)."""
    feeds = dict(narrative.DEFAULT_FEEDS) if opts.default_feeds else {}
    for spec in opts.feed or []:
        name, _, url = spec.partition("=")
        feeds[name] = url
    block = None
    if feeds:
        voices = narrative.collect(feeds, log=lambda m: print(m, file=sys.stderr))
        ask = (lambda system, user: llm.chat(system, user, timeout=narrative.LLM_TIMEOUT, max_tokens=narrative.LLM_MAX_TOKENS)) if llm.available() else None
        block = narrative.build(voices, ask, llm.MODEL if ask else "")
        print(f"narrative ({block['method']}): {len(voices)} headlines from {len({v['name'] for v in voices})} voices, {len(block['convergence'])} convergences")
    recorded = 0
    for symbol in opts.symbols:
        try:
            packet = evidence.collect(symbol, opts.interval, with_news=not opts.no_news)
        except (OSError, ValueError, KeyError) as err:
            print(f"{symbol}: no evidence collected, nothing recorded ({err})", file=sys.stderr)
            continue
        if block is not None:
            packet["narrative"] = block
        recorded += 1
        print_record(dossier.append(packet, opts.ledger, rules_version="v2"))
    return 0 if recorded else 1


def print_record(record: dict) -> None:
    v = record["verdict"]
    print(f"#{record['seq']} {record['evidence']['symbol']} {v['action']} edge={v['edge']} hash={record['hash'][:16]}")
    print(f"  {v['rationale']}")
    for side in ("bull", "bear"):
        for arg in record[side]:
            print(f"  [{side}] {arg['claim']} ({arg['evidence_ref']} = {arg['value']})")
    sens = record.get("sensitivity")
    if sens:
        flips = [d for d in sens["drop_one"] if d["flips"]]
        print(f"  to flip: +{sens['needs_for_long']} net edge for LONG, +{sens['needs_for_short']} for SHORT; "
              + (f"arguments that alone decide it: {len(flips)}" if flips else "no single argument decides it"))
    layer = record.get("llm")
    if layer:
        for side in ("bull", "bear"):
            for c in layer[side]["accepted"]:
                print(f"  [llm {side}] {c['claim']} cites {c['cites']}")
            print(f"  [llm {side}] {len(layer[side]['rejected'])} claims rejected by the citation validator")
    else:
        print("  LLM analysts off (no MISTRAL_API_KEY): deterministic core only")


def cmd_replay(opts) -> int:
    ledger = dossier.read_ledger(opts.ledger)
    targets = [d for d in ledger if opts.seq is None or d["seq"] == opts.seq]
    if not targets:
        print("No dossier found.", file=sys.stderr)
        return 1
    mismatches = 0
    for d in targets:
        rv = d.get("verdict", {}).get("rules_version", "v1")
        result = dossier.replay(d, rules_version=rv)
        mismatches += not result["matches"]
        print(f"#{result['seq']} replay {'MATCHES' if result['matches'] else 'DIFFERS'}: {result['replayed']['action']}")
    return 1 if mismatches else 0


def cmd_verify(opts) -> int:
    ledger = dossier.read_ledger(opts.ledger)
    problems = dossier.verify(ledger)
    if problems:
        print("\n".join(problems))
        return 1
    print(f"Chain intact: {len(ledger)} dossiers, head {ledger[-1]['hash'][:16] if ledger else '(empty)'}")
    return 0


def cmd_head(opts) -> int:
    try:
        head = dossier.head(dossier.read_ledger(opts.ledger))
    except ValueError as err:
        print(err, file=sys.stderr)
        return 1
    text = json.dumps(head, separators=(",", ":"))
    if opts.out:
        opts.out.parent.mkdir(parents=True, exist_ok=True)
        opts.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


def cmd_portfolio(opts) -> int:
    s = portfolio.summarize(dossier.read_ledger(opts.ledger))
    print(f"Decisions {s['decisions']} (flat {s['flat']}), positions {len(s['positions'])}: closed {s['closed']}, open {s['open']}")
    for p in s["positions"]:
        print(f"  #{p['seq']} {p['symbol']} {p['action']} entry {p['entry']} -> {p['status']} exit {p['exit']} pnl {p['pnl']}")
    print(f"Win rate {s['win_rate_pct']}%  realized {s['realized_pnl']}  unrealized {s['unrealized_pnl']}  max drawdown {s['max_drawdown_pct']}%  (simulated, start {s['start_capital']})")
    return 0


def cmd_backtest(opts) -> int:
    candles = backtest.fetch_history(opts.symbol, opts.interval, opts.candles)
    if len(candles) < backtest.WINDOW + opts.max_hold:
        print("Not enough history.", file=sys.stderr)
        return 1
    rep = backtest.report(opts.symbol, opts.interval, candles, max_hold=opts.max_hold, fee_pct=opts.fee_pct)
    s = rep["summary"]
    print(f"{rep['label']}: {rep['symbol']} {rep['interval']}, {rep['data']['candles']} candles, data sha256 {rep['data']['sha256'][:16]}")
    print(f"Trades {s['trades']} (long {s['longs']}, short {s['shorts']}), exits {s['by_exit']}, win rate {s['win_rate_pct']}%, profit factor {s['profit_factor']}")
    print(f"Net {s['net_pnl']} ({s['return_pct']}% of {s['start_capital']}), fees {s['fees_paid']}, max drawdown {s['max_drawdown_pct']}%, buy and hold {s['buy_and_hold_pct']}%")
    for seg in rep["segments"]:
        print(f"  part {seg['part']}: {seg['trades']} trades, net {seg['net_pnl']}")
    if opts.out:
        opts.out.parent.mkdir(parents=True, exist_ok=True)
        opts.out.write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8")
        print(f"Saved {opts.out}")
    return 0


def cmd_research(opts) -> int:
    studies = []
    for symbol in opts.symbols:
        candles = backtest.fetch_history(symbol, opts.interval, opts.candles)
        if len(candles) < backtest.WINDOW + backtest.MAX_HOLD * 4:
            print(f"{symbol}: not enough history.", file=sys.stderr)
            continue
        studies.append(research.study(symbol, candles, fee_pct=opts.fee_pct))
    if not studies:
        return 1
    print(research.LABEL)
    for s in studies:
        v1, v2 = s["v1_test"], s["v2"]
        print(f"{s['symbol']}: data sha256 {s['data']['sha256'][:16]}, train {s['data']['train_candles']} candles, test {s['data']['test_candles']} candles")
        print(f"  v1 on test : {v1['trades']} trades, net {v1['net_pnl']} ({v1['return_pct']}%), profit factor {v1['profit_factor']}, buy and hold {v1['buy_and_hold_pct']}%")
        if v2:
            print(f"  v2 chosen on train {v2['chosen']} (train net {v2['train']['net_pnl']}, {v2['train_configs_with_positive_net']} of {v2['configs_scored']} configs positive on train)")
            print(f"  v2 on test : {v2['test']['trades']} trades, net {v2['test']['net_pnl']} ({v2['test']['return_pct']}%), profit factor {v2['test']['profit_factor']}; beats v1: {v2['test_beats_v1']}")
    summary = research.verdict(studies)
    print(f"Verdict: v2 beats v1 out of sample on {summary['v2_beats_v1_out_of_sample']}, net positive on {summary['v2_net_positive_out_of_sample']}. {summary['reading']}")
    if opts.out:
        opts.out.parent.mkdir(parents=True, exist_ok=True)
        opts.out.write_text(json.dumps({"label": research.LABEL, "verdict": summary, "studies": studies}, indent=1) + "\n", encoding="utf-8")
        print(f"Saved {opts.out}")
    return 0


def cmd_audit_journal(opts) -> int:
    rows = journal.read_journal(opts.journal)
    print(f"{journal.LABEL}\nJournal: {len(rows)} turns, sha256 of the file lines kept per turn")
    result = journal.audit(rows, pause=0.2)
    outcomes = journal.mark_outcomes(result)
    summary = journal.summarize(result, outcomes)
    c = summary["journal_check"]
    print(f"Check against public Binance spot data (the journal reads futures, so volume is not compared): {c['closed_within_basis']} of {c['candles_closed']} closed candles agree within 0.3% ({c['closed_within_basis_pct']}%), "
          f"{c['candles_recorded'] - c['candles_closed']} candles were still forming and are not counted; "
          f"price inside the candle range on {c['prices_plausible']} of {c['prices_checked']} turns")
    print(f"Shadow decisions: {summary['shadow_decisions']} (one per symbol, hour and decision type), desk actions {summary['desk_actions']}")
    print(f"Automaton / desk: {summary['automaton_vs_desk']}")
    print(f"Hypothetical positions closed: {summary['hypothetical_closed']}, net {summary['hypothetical_net']} (past data, not a trade result); skipped turns {summary['skipped']}")
    if opts.out:
        opts.out.parent.mkdir(parents=True, exist_ok=True)
        opts.out.write_text(json.dumps({"summary": summary, "outcomes": outcomes, "skipped": result["skipped"]}, indent=1) + "\n", encoding="utf-8")
        print(f"Saved {opts.out}")
    if opts.shadow_ledger:
        opts.shadow_ledger.parent.mkdir(parents=True, exist_ok=True)
        opts.shadow_ledger.write_text("".join(json.dumps(d, ensure_ascii=False) + "\n" for d in result["ledger"]), encoding="utf-8")
        print(f"Saved shadow ledger {opts.shadow_ledger} (chain intact: {not dossier.verify(result['ledger'])})")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="verdict_desk")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("decide", help="collect evidence, debate, record a simulated decision")
    p.add_argument("symbols", nargs="+", metavar="SYMBOL")
    p.add_argument("--interval", default="1h")
    p.add_argument("--no-news", action="store_true")
    p.add_argument("--feed", action="append", metavar="NAME=URL", help="public RSS or Atom voice for the narrative agent (repeatable, up to 20)")
    p.add_argument("--default-feeds", action="store_true", help="also read the built-in public crypto news voices")
    p.set_defaults(func=cmd_decide)
    p = sub.add_parser("decide-v2", help="decide with agents_v2 + features_v2 (RSI, MACD, Bollinger)")
    p.add_argument("symbols", nargs="+", metavar="SYMBOL")
    p.add_argument("--interval", default="1h")
    p.add_argument("--no-news", action="store_true")
    p.add_argument("--feed", action="append", metavar="NAME=URL", help="public RSS or Atom voice for the narrative agent (repeatable, up to 20)")
    p.add_argument("--default-feeds", action="store_true", help="also read the built-in public crypto news voices")
    p.set_defaults(func=cmd_decide_v2)
    p = sub.add_parser("replay", help="re-run decisions from the frozen evidence")
    p.add_argument("seq", nargs="?", type=int)
    p.set_defaults(func=cmd_replay)
    p = sub.add_parser("verify", help="check the hash chain")
    p.set_defaults(func=cmd_verify)
    p = sub.add_parser("head", help="print the verified head of the chain as JSON, for the CRE anchor workflow")
    p.add_argument("--out", type=Path, help="also write the JSON to this file (published next to the ledger)")
    p.set_defaults(func=cmd_head)
    p = sub.add_parser("portfolio", help="mark simulated positions against later candles")
    p.set_defaults(func=cmd_portfolio)
    p = sub.add_parser("backtest", help="walk-forward test on past candles (separate from the live ledger)")
    p.add_argument("symbol")
    p.add_argument("--interval", default="1h")
    p.add_argument("--candles", type=int, default=4000)
    p.add_argument("--max-hold", type=int, default=backtest.MAX_HOLD)
    p.add_argument("--fee-pct", type=float, default=backtest.FEE_PCT_PER_SIDE, help="taker fee per side, in percent")
    p.add_argument("--out", type=Path)
    p.set_defaults(func=cmd_backtest)
    p = sub.add_parser("research", help="v2 rule search with a time split: choose on train, judge on test (separate from the live ledger)")
    p.add_argument("symbols", nargs="+")
    p.add_argument("--interval", default="1h")
    p.add_argument("--candles", type=int, default=4000)
    p.add_argument("--fee-pct", type=float, default=backtest.FEE_PCT_PER_SIDE)
    p.add_argument("--out", type=Path)
    p.set_defaults(func=cmd_research)
    p = sub.add_parser("audit-journal", help="check a third-party agent journal against public data and replay it in shadow")
    p.add_argument("journal", type=Path)
    p.add_argument("--out", type=Path, help="summary and per-turn outcomes (no free-text reasoning)")
    p.add_argument("--shadow-ledger", type=Path, help="write the shadow dossiers as a separate hash chain")
    p.set_defaults(func=cmd_audit_journal)
    opts = parser.parse_args()
    return opts.func(opts)


if __name__ == "__main__":
    sys.exit(main())
