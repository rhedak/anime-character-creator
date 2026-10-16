// The non-drawing parts of `character.py` that the foundation modules (`presets`, `supporting`, `urlstate`,
// `attribution`) import: the adult floor, the finishes and their validation, `aged_face`, `Expression`'s two
// methods, and what a Python dataclass gives for free that a TS interface does not: the constructor that fills the
// defaults, `dataclasses.replace`, and the refusal of a field that does not exist.
//
// The four dataclasses are interfaces in `params.ts`, with their field registry (`CHARACTERPARAMS_FIELDS` and
// the rest). Nothing here checks a value's type, because Python's dataclasses do not: a link can put a string in
// `hair_length` and the model keeps it (`pyvalue.ts` says how such values are spelt).

import { FINISHES } from "./character.ts";
import {
  CHARACTERPARAMS_FIELDS,
  DEFAULT_CHARACTERPARAMS,
  DEFAULT_EXPRESSION,
  DEFAULT_FACESTYLE,
  DEFAULT_OUTFIT,
  EXPRESSION_FIELDS,
  FACESTYLE_FIELDS,
  OUTFIT_FIELDS,
} from "./params.ts";
import type { CharacterParams, Expression, FaceStyle, FieldSpec, Outfit } from "./params.ts";
import { PyInt } from "./pyjson.ts";
import { PyError } from "./pynum.ts";
import { PyFloat, numberOf, plainNumber, pyValueRepr } from "./pyvalue.ts";

export { FINISHES };

// The youngest face a shipped preset or the GUI offers: twenty-one. The age of
// majority differs by country and twenty-one is the highest of the common ones.
// `face_age` is a drawing setting, not a number of years; this is the value the
// project reads as twenty-one (`docs/detail-plan.md`, D3).
export const ADULT_FACE_AGE = 0.9;

// ---------------------------------------------------------------------------------------------------------
// The dataclass machinery

export type ClassName = "CharacterParams" | "Outfit" | "FaceStyle" | "Expression";

/** The registry of each dataclass, by name. */
export const FIELDS: Readonly<Record<ClassName, readonly FieldSpec[]>> = {
  CharacterParams: CHARACTERPARAMS_FIELDS,
  Outfit: OUTFIT_FIELDS,
  FaceStyle: FACESTYLE_FIELDS,
  Expression: EXPRESSION_FIELDS,
};

const NAMES: Readonly<Record<ClassName, ReadonlySet<string>>> = {
  CharacterParams: new Set(CHARACTERPARAMS_FIELDS.map((f) => f.name)),
  Outfit: new Set(OUTFIT_FIELDS.map((f) => f.name)),
  FaceStyle: new Set(FACESTYLE_FIELDS.map((f) => f.name)),
  Expression: new Set(EXPRESSION_FIELDS.map((f) => f.name)),
};

/** The dataclass an object is an instance of, told by its keys (a plain object has no class), or `undefined`. */
export function classOf(obj: object): ClassName | undefined {
  const keys = Object.keys(obj);
  for (const cls of Object.keys(NAMES) as ClassName[]) {
    const names = NAMES[cls];
    if (keys.length === names.size && keys.every((k) => names.has(k))) return cls;
  }
  return undefined;
}

/**
 * What `Cls(**kwargs)` says about the first keyword that is not a field: Python's own text, since it reaches a
 * user inside `params_from_dict`'s `not a valid character: ...`.
 */
export function checkKeywords(cls: ClassName, keys: Iterable<string>): void {
  for (const k of keys) {
    if (k === "self") throw new PyError("TypeError", `${cls}.__init__() got multiple values for argument 'self'`);
    if (!NAMES[cls].has(k)) throw new PyError("TypeError", `${cls}.__init__() got an unexpected keyword argument '${k}'`);
  }
}

function construct<T extends object>(cls: ClassName, defaults: T, overrides: object): T {
  const given = Object.entries(overrides).filter(([, v]) => v !== undefined);
  checkKeywords(
    cls,
    given.map(([k]) => k),
  );
  return Object.freeze({ ...defaults, ...Object.fromEntries(given) }) as T;
}

/** `CharacterParams(**overrides)`: the defaults of the registry, with the named fields set. Frozen, like the dataclass. */
export const characterParams = (overrides: Partial<CharacterParams> = {}): CharacterParams =>
  construct("CharacterParams", DEFAULT_CHARACTERPARAMS, overrides);

/** `Outfit(**overrides)`. */
export const outfit = (overrides: Partial<Outfit> = {}): Outfit => construct("Outfit", DEFAULT_OUTFIT, overrides);

/** `FaceStyle(**overrides)`. */
export const faceStyle = (overrides: Partial<FaceStyle> = {}): FaceStyle => construct("FaceStyle", DEFAULT_FACESTYLE, overrides);

/** `Expression(**overrides)`: every field `null` (leave that one alone) unless named. */
export const expression = (overrides: Partial<Expression> = {}): Expression =>
  construct("Expression", DEFAULT_EXPRESSION, overrides);

/**
 * `dataclasses.replace(obj, **changes)`: a copy with the named fields changed, and a `TypeError` for a name that is
 * not a field. (A `changes` value of `undefined` is "not given", not a field set to nothing: `null` is Python's `None`.)
 */
export function replace<T extends object>(obj: T, changes: Partial<T>): T {
  const given = Object.entries(changes).filter(([, v]) => v !== undefined);
  const cls = classOf(obj);
  if (cls !== undefined) {
    checkKeywords(
      cls,
      given.map(([k]) => k),
    );
  }
  return Object.freeze({ ...obj, ...Object.fromEntries(given) });
}

// ---------------------------------------------------------------------------------------------------------
// validate_finish

/**
 * Raise `ValueError` if `p.finish` is not a finish, or if the soft finish's
 * `highlight_strength` is not a number from 0 to 2. The flat finish ignores the strength, so
 * it is only checked for the soft one.
 *
 * What the checks can see in TS: a plain number is a float, a `PyInt` an int (so `3` and `3.0` read differently
 * in the message, as in Python), and a boolean is a boolean (`true` is refused although `true == 1` in Python's
 * arithmetic). A value a caller types as `number` and means as the int `3` arrives as a float and reads `3.0`
 * in the message, which is the one place the text could differ from Python's for the same intent.
 */
export function validateFinish(p: CharacterParams): void {
  const finish: unknown = p.finish;
  if (!FINISHES.some((f) => f === finish)) {
    throw new PyError("ValueError", `finish must be one of ${FINISHES.join(", ")}, not ${pyValueRepr(finish)}`);
  }
  if (finish === "soft") {
    const strength: unknown = p.highlight_strength;
    const ok = typeof strength === "number" || strength instanceof PyInt || strength instanceof PyFloat;
    // `0.0 <= strength <= 2.0` is one chained comparison in Python; both halves are spelt out here, and a nan fails them.
    const n = numberOf(strength) as number;
    if (!ok || !(0.0 <= n && n <= 2.0)) {
      throw new PyError("ValueError", `highlight_strength must be between 0 and 2, not ${pyValueRepr(strength)}`);
    }
  }
}

// ---------------------------------------------------------------------------------------------------------
// aged_face

/**
 * A face read older, as a scaling of the fields that already exist:
 * `years` 0 leaves it alone, 1 is the cast's oldest. `presets.aged` says why
 * the eye carries almost all of it; `CharacterParams.face_age` applies it at
 * render time above 1.
 */
export function agedFace(face: FaceStyle, years = 1.0): FaceStyle {
  // The eye's terms at a third of what `aged()` first took (the eye shrank by
  // 14% and closed by 16% at the cast's oldest), for the same reason as
  // `_MATURE_EYE_SHARE`: within one story the eyes should not differ this
  // much; the grown face's jaw and nose now carry most of the age.
  return replace(face, {
    eye_size: plainNumber(face.eye_size) * (1 - (0.14 / 3) * years),
    eye_openness: plainNumber(face.eye_openness) * (1 - (0.16 / 3) * years),
    eye_lower_lid: plainNumber(face.eye_lower_lid) * (1 - (0.07 / 3) * years),
    iris_size: plainNumber(face.iris_size) * (1 - (0.09 / 3) * years),
    brow_weight: plainNumber(face.brow_weight) * (1 + 0.18 * years),
  });
}

// ---------------------------------------------------------------------------------------------------------
// Expression

/** This mood, over one face, leaving everything unnamed as it was (`Expression.on`). */
export function expressionOn(e: Expression, face: FaceStyle): FaceStyle {
  const stated = Object.fromEntries(Object.entries(e).filter(([, v]) => v !== null));
  return replace(face, stated as Partial<FaceStyle>);
}

/** The same, on a whole character (`Expression.applied_to`). */
export function expressionAppliedTo(e: Expression, p: CharacterParams): CharacterParams {
  return replace(p, { face: expressionOn(e, p.face) });
}
