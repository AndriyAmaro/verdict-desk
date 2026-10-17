/* Estatisticas do ledger calculadas no navegador (global VerdictStats) e no Node (module.exports).
 * portfolio() e a mesma regra de verdict_desk/portfolio.py: cada posicao so usa candles de dossies
 * registrados depois dela; se stop e alvo caem no mesmo candle, vale o stop; sem candle posterior, OPEN.
 * cadence() mostra os buracos reais do historico horario em vez de escondê-los. */
(function (root) {
  "use strict";
  var START_CAPITAL = 10000;
  var GAP_LIMIT_MS = 90 * 60 * 1000;

  function round(x, places) {
    var f = Math.pow(10, places);
    return Math.round((x + Number.EPSILON) * f) / f;
  }

  function lastCandleTime(d) {
    var c = d.evidence.market.candles;
    return c[c.length - 1].t;
  }

  function laterCandles(ledger, index) {
    var symbol = ledger[index].evidence.symbol, entry = lastCandleTime(ledger[index]), seen = {}, out = [];
    for (var i = index + 1; i < ledger.length; i++) {
      if (ledger[i].evidence.symbol !== symbol) continue;
      ledger[i].evidence.market.candles.forEach(function (c) {
        if (c.t > entry && !seen[c.t]) { seen[c.t] = true; out.push(c); }
      });
    }
    return out.sort(function (a, b) { return a.t - b.t; });
  }

  function resolve(d, candles) {
    var v = d.verdict, dir = v.action === "LONG" ? 1 : -1;
    var base = { seq: d.seq, symbol: d.evidence.symbol, action: v.action, entry: v.entry };
    for (var i = 0; i < candles.length; i++) {
      var c = candles[i];
      var hitStop = dir === 1 ? c.l <= v.stop : c.h >= v.stop;
      var hitTake = dir === 1 ? c.h >= v.take_profit : c.l <= v.take_profit;
      if (hitStop || hitTake) {
        var exit = hitStop ? v.stop : v.take_profit;
        return Object.assign(base, { status: hitStop ? "STOP" : "TAKE", exit: exit, pnl: round((exit - v.entry) * dir * v.size, 4), bars: i + 1 });
      }
    }
    if (candles.length) {
      var mark = candles[candles.length - 1].c;
      return Object.assign(base, { status: "OPEN", exit: mark, pnl: round((mark - v.entry) * dir * v.size, 4), bars: candles.length });
    }
    return Object.assign(base, { status: "OPEN", exit: v.entry, pnl: 0, bars: 0 });
  }

  function portfolio(ledger) {
    var positions = [];
    ledger.forEach(function (d, i) { if (d.verdict.action !== "FLAT") positions.push(resolve(d, laterCandles(ledger, i))); });
    var closed = positions.filter(function (p) { return p.status !== "OPEN"; });
    var wins = closed.filter(function (p) { return p.pnl > 0; });
    var equity = START_CAPITAL, peak = START_CAPITAL, maxDd = 0;
    closed.forEach(function (p) {
      equity += p.pnl;
      peak = Math.max(peak, equity);
      maxDd = Math.max(maxDd, (peak - equity) / peak * 100);
    });
    var sum = function (list) { return list.reduce(function (a, p) { return a + p.pnl; }, 0); };
    return {
      decisions: ledger.length,
      flat: ledger.filter(function (d) { return d.verdict.action === "FLAT"; }).length,
      positions: positions,
      closed: closed.length,
      open: positions.length - closed.length,
      win_rate_pct: closed.length ? round(wins.length / closed.length * 100, 1) : null,
      realized_pnl: round(sum(closed), 4),
      unrealized_pnl: round(sum(positions.filter(function (p) { return p.status === "OPEN"; })), 4),
      max_drawdown_pct: round(maxDd, 2),
      start_capital: START_CAPITAL
    };
  }

  function cadence(ledger) {
    var bySymbol = {}, all = [];
    ledger.forEach(function (d) {
      var t = Date.parse(d.evidence.collected_at);
      if (isNaN(t)) return;
      (bySymbol[d.evidence.symbol] = bySymbol[d.evidence.symbol] || []).push(t);
      all.push(t);
    });
    var longest = 0, longestSymbol = null, gapsOver = 0, counts = {};
    Object.keys(bySymbol).forEach(function (sym) {
      var times = bySymbol[sym].sort(function (a, b) { return a - b; });
      counts[sym] = times.length;
      for (var i = 1; i < times.length; i++) {
        var gap = times[i] - times[i - 1];
        if (gap > GAP_LIMIT_MS) gapsOver++;
        if (gap > longest) { longest = gap; longestSymbol = sym; }
      }
    });
    all.sort(function (a, b) { return a - b; });
    return {
      total: ledger.length,
      per_symbol: counts,
      first: all.length ? new Date(all[0]).toISOString() : null,
      last: all.length ? new Date(all[all.length - 1]).toISOString() : null,
      longest_gap_minutes: Math.round(longest / 60000),
      longest_gap_symbol: longestSymbol,
      gaps_over_90_minutes: gapsOver
    };
  }

  var api = { START_CAPITAL: START_CAPITAL, portfolio: portfolio, cadence: cadence, resolve: resolve };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.VerdictStats = api;
})(typeof self !== "undefined" ? self : this);
