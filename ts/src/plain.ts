// `p` as the drawing reads it. A character from a link or a model's request can carry the int `1` in a float field, a
// string in a number field, or a number in a flag; Python keeps what it was given and fails (or not) where the value is
// used. The drawing works on plain numbers, so this converts a numeric field's markers to numbers, a flag's numbers to
// booleans, and a value that is not a number at all to a `BadValue`, which raises `TypeError` the moment it is used as one.

import { FIELDS, type ClassName } from "./model.ts";
import type { CharacterParams } from "./params.ts";
import { PyInt } from "./pyjson.ts";
import { BadValue, FloatValue } from "./pynum.ts";
import { PyFloat, numberOf } from "./pyvalue.ts";

/**
 * The int fields Python hands to `range()` (`character.py:_shoulder_bars`, line 10211): a float there, even a whole one, raises
 * `TypeError`. Everywhere else `1.0 == 1`, so a float in an int field is just the number (the corpus has `wristband_side: 1.0`,
 * which draws), and boxing it would break the `=== 1` comparisons the parts make. Add a field here only when Python's own code
 * would reject a float in it.
 */
const MUST_BE_INT: ReadonlySet<string> = new Set(["shoulder_bars"]);

/** One dataclass with its numeric fields as plain numbers (the markers that keep Python's int against float are for links). */
function plainClass<T extends object>(cls: ClassName, obj: T): T {
  const out = { ...obj } as Record<string, unknown>;
  for (const f of FIELDS[cls]) {
    const v = out[f.name];
    if (f.type === "float" || f.type === "int") {
      const n = numberOf(v);
      // A float held where the registry says int keeps being a float (it fails `range()`); a plain number there is an int.
      if (n !== undefined) out[f.name] = f.type === "int" && v instanceof PyFloat && MUST_BE_INT.has(f.name) ? new FloatValue(n) : n;
      else if (!(v === null && f.nullable) && !(v instanceof BadValue)) out[f.name] = new BadValue(v);
    } else if (f.type === "bool") {
      // A number in a bool field is only ever tested for truth.
      if (v instanceof PyInt || v instanceof PyFloat || typeof v === "number") out[f.name] = (numberOf(v) as number) !== 0;
    }
  }
  return Object.freeze(out) as T;
}

/** `p` with every numeric field a plain number (or a `BadValue`) and every flag a boolean. Idempotent. */
export function plainParams(p: CharacterParams): CharacterParams {
  const top = plainClass("CharacterParams", p);
  return Object.freeze({ ...top, outfit: plainClass("Outfit", p.outfit), face: plainClass("FaceStyle", p.face) });
}
