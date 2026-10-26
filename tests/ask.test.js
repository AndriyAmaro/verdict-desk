// web/ask.js: "Ask the record", a conversation with one recorded decision that cannot make things up.
// Run: node --test tests/ask.test.js   (tests/test_ask.py runs it in CI, plus a sweep over the whole ledger)
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const ask = require("../web/ask.js");

const LEDGER = fs.readFileSync(path.join(__dirname, "..", "ledger", "ledger.jsonl"), "utf8").split("\n").filter(Boolean).map((l) => JSON.parse(l));
const latest = (pred) => [...LEDGER].reverse().find(pred);
const POSITION = latest((d) => ["LONG", "SHORT"].includes(d.verdict.action) && d.llm && d.llm.judge && d.llm.judge.ruling);
const DECLINED = latest((d) => d.verdict.action === "WATCH_REVERSAL");
const JUDGED = latest((d) => d.llm && d.llm.judge && d.llm.judge.accepted && d.llm.judge.weight > 0);
const VOIDED = latest((d) => d.llm && d.llm.judge && d.llm.judge.ruling && !d.llm.judge.accepted);
const OLD = LEDGER.find((d) => !d.llm);
const NO_SENSITIVITY = { ...OLD, sensitivity: undefined };
const textOf = (a) => a.parts.map((p) => p.text).join(" ");

test("free questions are routed to the intent they ask about, in English or Portuguese", () => {
  const cases = {
    "Why did you go short?": "why", "por que vendeu?": "why",
    "What would change your mind?": "flip", "what if one argument was removed": "flip",
    "How much could it lose?": "risk", "where is the stop?": "risk", "qual o risco?": "risk",
    "What did the AI judge think?": "judge", "o que o juiz achou": "judge",
    "What did you refuse?": "refused", "which claims were rejected": "refused",
    "What did the analysts claim?": "analysts",
    "Can I trust this record?": "proof", "was it tampered with?": "proof",
    "What did you decide?": "decision",
    "help": "help",
  };
  for (const [q, intent] of Object.entries(cases)) assert.equal(ask.route(q), intent, q);
});

test("a question outside the repertoire is declined, never improvised", () => {
  assert.equal(ask.route("will bitcoin hit 200k tomorrow?"), null);
  const a = ask.answer(POSITION, null);
  assert.equal(a.intent, "unknown");
  assert.match(textOf(a), /only answer from this record/);
  assert.ok(a.suggestions.length >= 5);
});

test("the time is shown in plain words and still checks against the recorded one", () => {
  const a = ask.answer(POSITION, "decision");
  assert.match(textOf(a), / at \d{2}:\d{2} UTC/);
  assert.ok(ask.check(a).ok);
});

test("the decision answer states the action, the edge and the band, each number cited", () => {
  const a = ask.answer(POSITION, "decision");
  const v = POSITION.verdict;
  assert.match(textOf(a), new RegExp(v.action));
  assert.ok(textOf(a).includes(String(v.edge)));
  assert.ok(a.cites.some((c) => c.ref === "verdict.edge"));
  assert.ok(ask.check(a).ok);
});

test("why names the heaviest arguments with their weights and the one that decided it, if any", () => {
  const a = ask.answer(POSITION, "why");
  const heaviest = [...POSITION.bull, ...POSITION.bear].sort((x, y) => y.weight - x.weight)[0];
  assert.ok(textOf(a).includes(heaviest.claim));
  assert.ok(ask.check(a).ok);
  const flips = (POSITION.sensitivity.drop_one || []).filter((d) => d.flips);
  if (!flips.length) assert.match(textOf(a), /No single argument/);
});

test("flip says how far each side is from the band", () => {
  const a = ask.answer(DECLINED, "flip");
  assert.ok(textOf(a).includes(String(DECLINED.sensitivity.needs_for_long)) || textOf(a).includes(String(DECLINED.sensitivity.needs_for_short)));
  assert.ok(ask.check(a).ok);
});

test("risk gives entry, stop, target, size and the most the stop can lose; a declined entry says no position", () => {
  const a = ask.answer(POSITION, "risk");
  const v = POSITION.verdict;
  for (const n of [v.entry, v.stop, v.take_profit, v.size]) assert.ok(textOf(a).includes(String(n)), String(n));
  assert.ok(ask.check(a).ok);
  assert.match(textOf(ask.answer(DECLINED, "risk")), /no position/i);
});

test("a counted judge vote says its weight and that it can never open a position alone, quoting the model", () => {
  const a = ask.answer(JUDGED, "judge");
  const j = JUDGED.llm.judge;
  assert.ok(a.parts.some((p) => p.kind === "quote" && p.text.includes(j.ruling.reason.slice(0, 20))));
  assert.ok(textOf(a).includes(String(j.weight)));
  assert.match(textOf(a), /never open a position on its own/);
  assert.ok(ask.check(a).ok);
});

test("a voided judge ruling says why and that it added nothing", () => {
  const a = ask.answer(VOIDED, "judge");
  assert.match(textOf(a), /voided/);
  assert.match(textOf(a), /added nothing/);
  assert.ok(ask.check(a).ok);
});

test("analysts and refusals show the model's claims as quotes, with the evidence each one cites", () => {
  const a = ask.answer(POSITION, "analysts");
  assert.ok(a.parts.some((p) => p.kind === "quote"));
  assert.ok(a.cites.some((c) => /^E\d+$/.test(c.ref)));
  assert.ok(ask.check(a).ok);
  assert.ok(ask.check(ask.answer(POSITION, "refused")).ok);
});

test("proof uses the fingerprint the page recomputed and says plainly when it does not match", () => {
  const ok = ask.answer(POSITION, "proof", { recomputedHash: POSITION.hash });
  assert.match(textOf(ok), /matches/);
  assert.ok(ask.check(ok).ok);
  const bad = ask.answer(POSITION, "proof", { recomputedHash: "0".repeat(64) });
  assert.match(textOf(bad), /does NOT match/);
});

test("the self-check refuses a number that no cited source contains", () => {
  const a = ask.answer(POSITION, "decision");
  const forged = { ...a, parts: [...a.parts, { kind: "text", text: "It expected a 37.5 percent move." }] };
  const result = ask.check(forged);
  assert.equal(result.ok, false);
  assert.ok(result.stray.includes("37.5"));
});

test("quotes are excluded from the number check but cited references are not", () => {
  const a = { parts: [{ kind: "quote", text: "claims 999" }, { kind: "text", text: "weight 1.5" }], cites: [{ ref: "x", label: "x", source: "1.5" }] };
  assert.ok(ask.check(a).ok);
});

test("records without an LLM layer or a sensitivity table answer plainly instead of breaking", () => {
  assert.match(textOf(ask.answer(OLD, "judge")), /no AI judge/i);
  assert.match(textOf(ask.answer(OLD, "analysts")), /no AI analyst/i);
  assert.match(textOf(ask.answer(NO_SENSITIVITY, "flip")), /predates/i);
  assert.match(textOf(ask.answer(NO_SENSITIVITY, "why")), /predates/i);
  for (const intent of ask.INTENTS) assert.ok(ask.check(ask.answer(OLD, intent, { recomputedHash: OLD.hash })).ok, intent);
});
