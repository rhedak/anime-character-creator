// `p` as the drawing reads it. A character from a link or a model's request can carry the int `1` in a float field, a
// string in a number field, or a number in a flag; Python keeps what it was given and fails (or not) where the value is
// used. The drawing works on plain numbers, so this converts a numeric field's markers to numbers, a flag's numbers to
// booleans, and a value that is not a number at all to a `BadValue`, which raises `TypeError` the moment it is used as one.

import { FIELDS, type ClassName } from "./model.ts";
import type { CharacterParams } from "./params.ts";
import { PyInt } from "./pyjson.ts";
import { BadValue, FloatValue } from "./pynum.ts";
import { PyFloat, numberOf } from "./pyvalue.ts";

/** One dataclass with its numeric fields as plain numbers (the markers that keep Python's int against float are for links). */
function plainClass<T extends object>(cls: ClassName, obj: T): T {
  const out = { ...obj } as Record<string, unknown>;
  for (const f of FIELDS[cls]) {
    const v = out[f.name];
    if (f.type === "float" || f.type === "int") {
      const n = numberOf(v);
      // A float held where the registry says int keeps being a float (it fails `range()`); a plain number there is an int.
      if (n !== undefined) out[f.name] = f.type === "int" && v instanceof PyFloat ? new FloatValue(n) : n;
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
