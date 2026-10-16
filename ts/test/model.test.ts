// `model.ts` against Python: the defaults, `aged_face`, `Expression`, the dataclass errors and `validate_finish`.

import assert from "node:assert/strict";
import { test } from "node:test";
import { ADULT_FACE_AGE, FINISHES, agedFace, characterParams, expression, expressionAppliedTo, expressionOn, faceStyle, outfit, replace, validateFinish } from "../src/model.ts";
import type { CharacterParams, FaceStyle } from "../src/params.ts";
import { dumps } from "../src/pyjson.ts";
import { loadsText } from "../src/pyjsonload.ts";
import { PyError } from "../src/pynum.ts";
import { PRESETS, EXPRESSIONS, aged } from "../src/presets.ts";
import { dataclassJson, paramsJsonText } from "../src/urlstate.ts";
import { fixture, fromTagged, outcomeOf, sha256, wanted } from "./phase3.ts";
import type { Tagged } from "./phase3.ts";

const model = fixture("model.json");
const presetsFx = fixture("presets.json");

const text = (cls: "CharacterParams" | "Outfit" | "FaceStyle" | "Expression", obj: object): string =>
  dumps(dataclassJson(cls, obj), { sortKeys: true, compact: true });
const faceFrom = (t: string): FaceStyle => faceStyle(Object.fromEntries(loadsText(t) as Map<string, never>) as Partial<FaceStyle>);

test("the adult floor and the finishes are Python's", () => {
  assert.equal(ADULT_FACE_AGE, model.adult_face_age);
  assert.deepEqual([...FINISHES], presetsFx.constants.FINISHES);
});

test("the constructors fill the registry's defaults: the JSON of each default equals Python's", () => {
  assert.equal(paramsJsonText(characterParams()), presetsFx.defaults.CharacterParams);
  assert.equal(text("Outfit", outfit()), presetsFx.defaults.Outfit);
  assert.equal(text("FaceStyle", faceStyle()), presetsFx.defaults.FaceStyle);
  assert.equal(text("Expression", expression()), presetsFx.defaults.Expression);
});

test("a dataclass is frozen, and a constructor does not alias the defaults", () => {
  const p = characterParams({ height: 1.2 });
  assert.throws(() => {
    (p as { height: number }).height = 2;
  }, TypeError);
  assert.equal(characterParams().height, 1);
  assert.notEqual(characterParams().outfit, characterParams().outfit === undefined ? null : undefined);
});

test("aged_face reproduces Python on faces from the presets and random ones, at nine ages each", () => {
  assert.ok(model.aged_face.length >= 300);
  const bad: string[] = [];
  for (const c of model.aged_face) {
    const got = text("FaceStyle", agedFace(faceFrom(c.face), Number(c.years)));
    if (got !== c.want) bad.push(`${c.years}: ${c.face.slice(0, 60)}`);
  }
  assert.deepEqual(bad, []);
});

test("presets.aged is aged_face, with years defaulting to 1", () => {
  for (const c of model.presets_aged) assert.equal(text("FaceStyle", aged(faceFrom(c.face), Number(c.years))), c.want);
  assert.equal(text("FaceStyle", aged(faceFrom(model.presets_aged_default.face))), model.presets_aged_default.want);
});

test("Expression.on and applied_to reproduce Python for every mood on six presets", () => {
  assert.equal(model.expressions.length, 13 * 6);
  for (const c of model.expressions) {
    const e = EXPRESSIONS[c.expression]!;
    const p = PRESETS[c.preset]!;
    assert.equal(text("FaceStyle", expressionOn(e, p.face)), c.face);
    assert.equal(sha256(paramsJsonText(expressionAppliedTo(e, p))), c.params_sha256);
  }
});

test("an expression leaves what it does not name alone, and its own fields may be set to zero", () => {
  const face = faceStyle({ eye_size: 0.7, brow_tilt: 0.4 });
  const flat = expression({ brow_tilt: 0 });
  assert.equal(expressionOn(flat, face).brow_tilt, 0);
  assert.equal(expressionOn(flat, face).eye_size, 0.7);
  assert.equal(expressionOn(expression(), face).brow_tilt, 0.4);
});

test("constructor and replace errors carry Python's class and text", () => {
  const p = characterParams();
  const calls: Record<string, () => unknown> = {
    "replace unknown on params": () => replace(p, { zzz: 1 } as never),
    "replace unknown on face": () => replace(p.face, { zzz: 1 } as never),
    "replace unknown on outfit": () => replace(p.outfit, { zzz: 1 } as never),
    "replace unknown on expression": () => replace(expression(), { zzz: 1 } as never),
    "replace two unknown": () => replace(p, { zzz: 1, yyy: 2 } as never),
    "replace self": () => replace(p, { self: 1 } as never),
    "construct unknown": () => characterParams({ zzz: 1 } as never),
    "construct outfit unknown": () => outfit({ zzz: 1 } as never),
    "construct face unknown": () => faceStyle({ zzz: 1 } as never),
    "construct expression unknown": () => expression({ zzz: 1 } as never),
    "construct self": () => characterParams({ self: 1 } as never),
  };
  assert.equal(model.errors.length, Object.keys(calls).length);
  for (const c of model.errors) assert.deepEqual(outcomeOf(calls[c.label]!), wanted(c.want), c.label);
});

test("replace keeps the fields it was not given, in order, and ignores undefined", () => {
  const p = characterParams({ height: 1.1 });
  const q = replace(p, { frame: 0.5, bust: undefined });
  assert.deepEqual(Object.keys(q), Object.keys(p));
  assert.equal(q.frame, 0.5);
  assert.equal(q.bust, p.bust);
  assert.equal(p.frame, 0);
});

test("validate_finish: the same outcome as Python on every finish and strength spelling", () => {
  assert.ok(model.validate_finish.length > 70);
  const bad: string[] = [];
  for (const c of model.validate_finish) {
    const p = characterParams({ finish: fromTagged(c.finish), highlight_strength: fromTagged(c.strength) } as unknown as Partial<CharacterParams>);
    const got = outcomeOf(() => {
      validateFinish(p);
      return "ok";
    });
    const want = wanted(c.want);
    if (JSON.stringify(got) !== JSON.stringify(want)) bad.push(`${JSON.stringify(c.finish)} ${JSON.stringify(c.strength)}: got ${JSON.stringify(got)} want ${JSON.stringify(want)}`);
  }
  assert.deepEqual(bad, []);
});

test("validate_finish text is the documented API text", () => {
  const f = (finish: unknown, strength = 1): unknown =>
    outcomeOf(() => validateFinish(characterParams({ finish, highlight_strength: strength } as unknown as Partial<CharacterParams>)));
  assert.deepEqual(f("x"), { err: "ValueError", msg: "finish must be one of flat, soft, not 'x'" });
  assert.deepEqual(f("soft", 2.5), { err: "ValueError", msg: "highlight_strength must be between 0 and 2, not 2.5" });
  assert.deepEqual(f("soft", Number.NaN), { err: "ValueError", msg: "highlight_strength must be between 0 and 2, not nan" });
  assert.deepEqual(f("flat", 99), { ok: undefined });
  assert.ok(new PyError("ValueError", "x") instanceof Error);
});
