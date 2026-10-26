/* Ask the record: a conversation with one recorded decision that cannot make things up.
 *
 * No model runs here. Every answer is built from the frozen dossier: each sentence is a template filled with
 * its fields, and each field used is cited with the exact text it came from. Words a model wrote when the
 * decision was recorded (analyst claims, the judge's reason) are shown as quotes, labelled, never rewritten.
 * `check` then applies the citation validator's rule to the answer itself: every number in the answer's own
 * text must appear in one of its cited sources, or the answer is refused. tests/test_ask.py runs that check on
 * every question for every dossier of the published ledger.
 *
 * Pure data in, pure data out. No DOM, no network.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.VerdictAsk = api;
})(typeof self !== "undefined" ? self : this, function () {
  const NUMBER = /-?\d+(?:\.\d+)?/g;

  const SUGGESTIONS = [
    { intent: "decision", label: "What did you decide?" },
    { intent: "why", label: "Why?" },
    { intent: "flip", label: "What would change your mind?" },
    { intent: "risk", label: "How much could it lose?" },
    { intent: "analysts", label: "What did the AI analysts claim?" },
    { intent: "refused", label: "What did you refuse?" },
    { intent: "judge", label: "What did the AI judge think?" },
    { intent: "proof", label: "Can I trust this record?" },
    { intent: "help", label: "What can I ask?" },
  ];
  const INTENTS = SUGGESTIONS.map((s) => s.intent);
  const TITLE = Object.fromEntries(SUGGESTIONS.map((s) => [s.intent, s.label]));

  // Most specific first: "why did the judge lean bear" is about the judge, not a generic why.
  const ROUTES = [
    ["refused", /\b(refus|reject|discard|threw|thrown|invalid|recus|rejeit|descart)/i],
    ["judge", /\b(judge|ruling|lean|conviction|juiz|veredito do juiz)/i],
    ["analysts", /\b(analyst|claim|bull case|bear case|llm|ai said|analista|afirma)/i],
    ["flip", /\b(flip|change (your|its) mind|would change|what if|without|sensitiv|removed|mudaria|mudar de ideia|virar)/i],
    ["risk", /\b(risk|stop|target|take profit|size|lose|loss|position|entry|risco|perd|alvo|tamanho|posi[cç])/i],
    ["proof", /\b(trust|proof|prove|verify|hash|fingerprint|tamper|changed|edited|real\b|genuine|confi|prova|verific|adulter)/i],
    ["why", /\b(why|reason|because|argument|por ?qu[eê]|motivo|raz[aã]o)/i],
    ["decision", /\b(decide|decision|verdict|action|what did (you|it) do|long or short|decid|decis[aã]o|a[cç][aã]o)/i],
    ["help", /\b(help|what can (i|you)|options|ajuda|o que posso)/i],
  ];

  function route(question) {
    const q = String(question || "");
    for (const [intent, pattern] of ROUTES) if (pattern.test(q)) return intent;
    return null;
  }

  // ---------------------------------------------------------------- the self-check
  function key(n) {
    const x = Number.parseFloat(n);
    if (!Number.isFinite(x)) return n;
    return Object.is(x, -0) ? "-0" : String(Math.round(x * 1e6) / 1e6);
  }

  /** The citation validator's rule, applied to the answer: every number in its own text must be in a cited source. */
  function check(answer) {
    const allowed = new Set();
    for (const c of answer.cites || []) for (const n of String(c.source).match(NUMBER) || []) allowed.add(key(n));
    const stray = [];
    for (const p of answer.parts || []) {
      if (p.kind === "quote") continue; // a model's own words, recorded and validated when the decision was made
      for (const n of String(p.text).match(NUMBER) || []) if (!allowed.has(key(n))) stray.push(n);
    }
    return { ok: stray.length === 0, stray };
  }

  // ---------------------------------------------------------------- building an answer
  function builder(d, intent) {
    const parts = [];
    const cites = [];
    const cite = (ref, label, value) => {
      const source = typeof value === "string" ? value : JSON.stringify(value);
      if (!cites.some((c) => c.ref === ref)) cites.push({ ref, label, source });
      return ref;
    };
    return {
      cite,
      say(text, refs) { parts.push({ kind: "text", text, refs: refs || [] }); },
      quote(text, label, refs) { parts.push({ kind: "quote", text: String(text), label, refs: refs || [] }); },
      done() {
        return { intent, title: TITLE[intent] || "", seq: d.seq, parts, cites, suggestions: SUGGESTIONS.filter((s) => s.intent !== intent) };
      },
    };
  }

  const has = (x) => x !== undefined && x !== null;

  /** "2026-10-26 at 18:20 UTC" from the recorded ISO time; any other shape is shown as recorded. */
  function when(iso) {
    const m = /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})(?::\d{2}(?:\.\d+)?)?(?:Z|\+00:00)$/.exec(String(iso));
    return m ? `${m[1]} at ${m[2]} UTC` : String(iso);
  }
  const ACTION_WORDS = {
    LONG: "went LONG (a simulated buy)",
    SHORT: "went SHORT (a simulated sale, betting on a fall)",
    WATCH_REVERSAL: "did not open a position (WATCH_REVERSAL: the sides were close and one argument could flip it)",
    REDUCE_EXPOSURE: "did not open a position (REDUCE_EXPOSURE: both sides strong while volatility was high)",
    FLAT: "did not open a position (FLAT: neither side was strong enough)",
    BLOCKED_STALE: "refused to decide (BLOCKED_STALE: the newest price was too old to trust)",
  };

  function decision(d, b) {
    const v = d.verdict || {};
    const ev = d.evidence || {};
    b.say(`Record ${d.seq}: on ${when(ev.collected_at)} the desk looked at ${ev.symbol} and ${ACTION_WORDS[v.action] || `recorded ${v.action}`}.`,
      [b.cite("seq", "record number", String(d.seq)), b.cite("evidence.collected_at", "when it looked", String(ev.collected_at))]);
    if (has(v.bull_score) && has(v.bear_score) && has(v.edge)) {
      const refs = [b.cite("verdict.bull_score", "bull score", v.bull_score), b.cite("verdict.bear_score", "bear score", v.bear_score), b.cite("verdict.edge", "edge", v.edge)];
      let line = `The arguments for a rise weighed ${v.bull_score} and those for a fall ${v.bear_score}, an edge of ${v.edge}`;
      if (has(v.threshold)) {
        refs.push(b.cite("verdict.threshold", "entry band", v.threshold));
        line += `; a position needs at least ${v.threshold} either way`;
      }
      b.say(line + ".", refs);
    }
    if (has(v.rules_version)) b.say(`It decided under rules ${v.rules_version}, frozen inside the record.`, [b.cite("verdict.rules_version", "rules", String(v.rules_version))]);
    b.say("Simulated only: no real order was placed.");
  }

  function arguments_(d) {
    return [...(d.bull || []).map((a, i) => ({ ...a, side: "bull", i })), ...(d.bear || []).map((a, i) => ({ ...a, side: "bear", i }))];
  }

  function why(d, b) {
    const v = d.verdict || {};
    const args = arguments_(d).sort((x, y) => y.weight - x.weight);
    if (!args.length) {
      b.say("No argument fired on either side in this record.");
    } else {
      b.say(`It ${ACTION_WORDS[v.action] || `recorded ${v.action}`}. The heaviest arguments:`);
      for (const a of args.slice(0, 4)) {
        const ref = b.cite(`${a.side}[${a.i}]`, `${a.side} argument`, `${a.claim} ${a.weight}`);
        b.say(`${a.side}: "${a.claim}", weight ${a.weight}.`, [ref]);
      }
    }
    if (has(v.bull_score) && has(v.bear_score)) {
      b.say(`In total, bull ${v.bull_score} against bear ${v.bear_score}.`, [b.cite("verdict.bull_score", "bull score", v.bull_score), b.cite("verdict.bear_score", "bear score", v.bear_score)]);
    }
    const sens = d.sensitivity;
    if (!sens || !sens.drop_one) {
      b.say("This record predates the sensitivity table, so it does not say which single argument decided it.");
      return;
    }
    const flips = sens.drop_one.filter((x) => x.flips);
    if (!flips.length) {
      b.say(`No single argument decides it: removing any one of them still leaves ${v.action}.`);
    } else {
      const f = flips[0];
      b.say(`The one that decided it: "${f.claim}" (weight ${f.weight}). Without it the edge would be ${f.edge_without} and the verdict ${f.action_without}.`,
        [b.cite("sensitivity.flip", "deciding argument", `${f.claim} ${f.weight} ${f.edge_without} ${f.action_without}`)]);
    }
  }

  function flip(d, b) {
    const sens = d.sensitivity;
    const v = d.verdict || {};
    if (!sens || !has(sens.needs_for_long)) {
      b.say("This record predates the sensitivity table (no sensitivity data), so it cannot say what would have changed the verdict.");
      return;
    }
    const refs = [b.cite("sensitivity.needs_for_long", "needed for a LONG", sens.needs_for_long), b.cite("sensitivity.needs_for_short", "needed for a SHORT", sens.needs_for_short)];
    b.say(`To open a LONG the bull side would have needed ${sens.needs_for_long} more net weight; to open a SHORT the bear side ${sens.needs_for_short} more (zero means it was already there).`, refs);
    const flips = (sens.drop_one || []).filter((x) => x.flips);
    if (!flips.length) b.say(`No single argument, removed on its own, changes ${v.action}.`);
    for (const f of flips.slice(0, 4)) {
      b.say(`Remove "${f.claim}" (${f.side}, weight ${f.weight}) and the edge becomes ${f.edge_without}: ${f.action_without}.`,
        [b.cite(`drop_one:${f.side}:${f.claim}`, "argument removed", `${f.claim} ${f.weight} ${f.edge_without} ${f.action_without}`)]);
    }
  }

  function risk(d, b) {
    const v = d.verdict || {};
    const p = v.policy || {};
    if (!has(v.entry)) {
      const refs = [];
      let line = `No position was opened (${v.action}), so there is no entry, stop, target or size`;
      if (has(p.max_risk_pct)) {
        refs.push(b.cite("verdict.policy.max_risk_pct", "risk limit", p.max_risk_pct));
        line += `. The risk limit in force was ${p.max_risk_pct}% of the simulated capital per position`;
      }
      b.say(line + ".", refs);
      return;
    }
    b.say(`Entry ${v.entry}, stop ${v.stop}, target ${v.take_profit}, size ${v.size} ${d.evidence.symbol}.`,
      [b.cite("verdict.entry", "entry", v.entry), b.cite("verdict.stop", "stop", v.stop), b.cite("verdict.take_profit", "target", v.take_profit), b.cite("verdict.size", "size", v.size)]);
    if (has(v.risk_pct)) {
      const refs = [b.cite("verdict.risk_pct", "risk per position", v.risk_pct)];
      let line = `The size is set so that if the stop is hit the simulated loss is exactly ${v.risk_pct}% of the simulated capital`;
      if (has(v.system_max_risk_pct)) {
        refs.push(b.cite("verdict.system_max_risk_pct", "system cap", v.system_max_risk_pct));
        line += `; a user may lower that limit, never raise it above ${v.system_max_risk_pct}%`;
      }
      b.say(line + ".", refs);
    }
    if (has(p.stop_atr) && has(p.take_atr)) {
      b.say(`The stop sits ${p.stop_atr} ATR from the entry and the target ${p.take_atr} ATR away, by the rules frozen in the record.`,
        [b.cite("verdict.policy.stop_atr", "stop rule", p.stop_atr), b.cite("verdict.policy.take_atr", "target rule", p.take_atr)]);
    }
    b.say("Simulated only: no real order was placed.");
  }

  function analysts(d, b) {
    const llm = d.llm;
    if (!llm) {
      b.say("This record has no AI analyst layer: the decision rests on the fixed rules alone.");
      return;
    }
    const items = llm.evidence_index || {};
    for (const side of ["bull", "bear"]) {
      const block = llm[side] || {};
      if (block.error) {
        b.say(`The ${side} analyst failed for this record, so it made no claim. The provider's error is recorded:`);
        b.quote(block.error, "provider error, recorded");
        continue;
      }
      const kept = block.accepted || [];
      const refused = block.rejected || [];
      const who = block.served_by ? [b.cite(`llm.${side}.served_by`, "model that answered", block.served_by)] : [];
      b.say(`The ${side} analyst made ${kept.length + refused.length} claims: ${kept.length} passed the citation check and ${refused.length} were refused${block.served_by ? ` (answered by ${block.served_by})` : ""}.`,
        [b.cite(`llm.${side}.counts`, `${side} claims kept and refused`, `${kept.length + refused.length} ${kept.length} ${refused.length}`), ...who]);
      for (const c of kept.slice(0, 4)) {
        const refs = (c.cites || []).filter((e) => typeof e === "string" && items[e]).map((e) => b.cite(e, `evidence ${e}`, items[e]));
        b.quote(c.claim, `${side} analyst (LLM), passed the check`, refs);
      }
    }
  }

  function refused(d, b) {
    const llm = d.llm;
    if (!llm) {
      b.say("This record has no AI analyst layer, so nothing could be refused.");
      return;
    }
    let any = false;
    for (const side of ["bull", "bear"]) {
      for (const r of ((llm[side] || {}).rejected || []).slice(0, 6)) {
        any = true;
        const reason = r.rejected_because || r.reason || "no valid citation";
        b.quote(r.claim, `${side} analyst (LLM), refused`);
        b.say(`Refused because: ${reason}.`, [b.cite(`refused:${side}:${r.claim}`, "refusal reason", reason)]);
      }
    }
    const j = llm.judge;
    if (j && j.ruling && !j.accepted && j.rejected_because) {
      any = true;
      b.say(`The AI judge's ruling was voided too: ${j.rejected_because}.`, [b.cite("llm.judge.rejected_because", "why the ruling was voided", j.rejected_because)]);
    }
    if (!any) b.say("Nothing was refused in this record: every claim the analysts made passed the citation check.");
  }

  function judge(d, b) {
    const v = d.verdict || {};
    const j = d.llm && d.llm.judge;
    if (!j) {
      b.say(`This record has no AI judge: it was decided under rules ${v.rules_version}, before the judge existed (rules v6), so the fixed rules decided alone.`,
        [b.cite("verdict.rules_version", "rules", `${v.rules_version} v6`)]);
      return;
    }
    const weights = (v.policy || {}).llm_judge_weights;
    const cap = weights ? Math.max(...Object.values(weights)) : null;
    const who = j.served_by ? [b.cite("llm.judge.served_by", "model that answered", j.served_by)] : [];
    const r = j.ruling;
    if (!r) {
      const why = j.rejected_because || j.error || "no ruling";
      b.say(`The AI judge did not rule on this record (${why}), so it added nothing.`, [b.cite("llm.judge.why", "why there is no ruling", why)]);
      return;
    }
    const relied = r.relied_on || [];
    const base = [b.cite("llm.judge.ruling.relied_on", "claims it relied on", relied), ...who];
    if (j.accepted && j.weight > 0) {
      const refs = [...base, b.cite("llm.judge.weight", "weight of the vote", j.weight)];
      let line = `The AI judge read only the claims that passed and leaned ${r.lean} with ${r.conviction} conviction, relying on ${relied.join(", ")}. Under rules v6 that adds ${j.weight} to the ${r.lean} side`;
      if (cap !== null && has(v.threshold)) {
        refs.push(b.cite("verdict.policy.llm_judge_weights", "judge weight table", weights), b.cite("verdict.threshold", "entry band", v.threshold), b.cite("verdict.rules_version", "rules", String(v.rules_version)));
        line += `; its vote is capped at ${cap}, below the entry band of ${v.threshold}, so it can never open a position on its own`;
      }
      b.say(line + (j.served_by ? ` (answered by ${j.served_by}).` : "."), refs);
    } else if (j.accepted) {
      b.say(`The AI judge read the claims that passed, found the two cases balanced (${r.lean}), and added nothing.`, base);
    } else {
      const why = j.rejected_because || "it did not hold";
      b.say(`The AI judge leaned ${r.lean}, but its ruling was voided (${why}), so it added nothing.`, [...base, b.cite("llm.judge.rejected_because", "why the ruling was voided", why)]);
    }
    if (r.reason) b.quote(r.reason, `the judge's own words (LLM)${j.accepted ? ", checked when recorded" : ", voided"}`);
  }

  function proof(d, b, ctx) {
    const recomputed = ctx && ctx.recomputedHash;
    const refs = [b.cite("hash", "recorded fingerprint", d.hash)];
    if (!recomputed) {
      b.say(`The recorded fingerprint is ${d.hash}. The page has not recomputed it yet.`, refs);
    } else if (recomputed === d.hash) {
      b.say(`The fingerprint recomputed in your browser from this record's contents just now matches the recorded one: ${d.hash}. Nobody has changed this record since it was written.`, refs);
    } else {
      refs.push(b.cite("recomputed", "recomputed fingerprint", recomputed));
      b.say(`The fingerprint recomputed in your browser, ${recomputed}, does NOT match the recorded one, ${d.hash}: this copy was changed after it was written. Do not rely on it.`, refs);
    }
    if (d.prev_hash) b.say(`It is chained to the record before it, whose fingerprint is ${d.prev_hash}; changing any earlier record breaks that link.`, [b.cite("prev_hash", "previous fingerprint", d.prev_hash)]);
    b.say("To check that this is the record we published, and when: the Witnesses page compares the chain's head with Bitcoin, the Sigstore log and the Sepolia anchor, none of which we control.");
  }

  function help(d, b) {
    b.say("I answer only from this record: what it decided, why, what would have changed it, the risk it took, what the AI analysts claimed, what was refused, what the AI judge thought, and whether you can trust the record. Every number I give points to the field it came from, and this page checks it before showing it.");
  }

  const ANSWERS = { decision, why, flip, risk, analysts, refused, judge, proof, help };

  function answer(dossier, intent, ctx) {
    if (!intent || !ANSWERS[intent]) {
      const b = builder(dossier, "unknown");
      b.say("I can only answer from this record, and that question is outside it. Try one of these:");
      const out = b.done();
      out.suggestions = SUGGESTIONS;
      return out;
    }
    const b = builder(dossier, intent);
    ANSWERS[intent](dossier, b, ctx || {});
    return b.done();
  }

  return { route, answer, check, INTENTS, SUGGESTIONS };
});
