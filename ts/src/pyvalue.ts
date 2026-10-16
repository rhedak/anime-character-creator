// Python values that arrive from outside (a link, the web tool, a companion app's model) and that the
// model keeps exactly as they came. `params_from_dict` checks the names of the fields and two of the values
// and nothing else, so a field typed `float` can hold the int `1`, a field typed `int` the float `1.0`, a
// string, a list. Python keeps them and writes them back as they were, so the port has to be able to say what
// a value was.
//
// How a value is spelt at run time, in a field the registry (`params.ts`) types:
//
//  * a plain JS `number` is what the registry says: a float in a `float` field (`1.0`), an int in an `int`
//    field when it is a whole number, and a float spelling when it is not;
//  * a `PyInt` (from `pyjson.ts`) is an int where the registry says float or says nothing (`"height": 1`);
//  * a `PyFloat` is a float where the registry says int and the value is whole (`"scar_side": 1.0`);
//  * everything else is itself: `null`, a boolean, a string, an array, a `Map` for a dict.
//
// The renderer works on plain numbers, so `plainNumber` strips the markers where a value is drawn.

import { PyInt } from "./pyjson.ts";
import { PY_TRUTH, pyRepr } from "./pynum.ts";

/** A float that must be spelt as one where the registry's tag would spell it as an int (`1.0` in an int field). */
export class PyFloat {
  readonly value: number;
  constructor(value: number) {
    this.value = value;
  }
  [PY_TRUTH](): boolean {
    return this.value !== 0;
  }
}

/**
 * An int too big for a double, kept exactly: a `PyInt` whose `value` is really a `bigint`. `dumps` prints
 * `String(value)`, which spells a `bigint` in full, which is all a big int ever needs here (it is kept and
 * written back, never computed with).
 */
export function bigPyInt(value: bigint): PyInt {
  return new PyInt(value as unknown as number);
}

/** The number a numeric value stands for (`int`, `float` and `bool` are numbers in Python), or `undefined`. */
export function numberOf(v: unknown): number | undefined {
  if (typeof v === "number") return v;
  if (typeof v === "boolean") return v ? 1 : 0;
  if (v instanceof PyInt) return Number(v.value);
  if (v instanceof PyFloat) return v.value;
  return undefined;
}

/** A value as a plain `number`, for drawing (`1` for the int `1`, `1` for `True`, as Python's arithmetic reads them). */
export function plainNumber(v: unknown): number {
  const n = numberOf(v);
  if (n === undefined) throw new TypeError(`not a number: ${String(v)}`);
  return n;
}

/** `type(v).__name__`. A plain number is a `float`: an int is a `PyInt` unless a field's tag says so. */
export function pyTypeName(v: unknown): string {
  if (v === null || v === undefined) return "NoneType";
  if (typeof v === "boolean") return "bool";
  if (typeof v === "number" || v instanceof PyFloat) return "float";
  if (v instanceof PyInt) return "int";
  if (typeof v === "string") return "str";
  if (Array.isArray(v)) return "list";
  return "dict";
}

const NOT_PRINTABLE = /^[\p{Cc}\p{Cf}\p{Cs}\p{Co}\p{Cn}\p{Zl}\p{Zp}\p{Zs}]$/u;

/**
 * `repr(s)` of a str, with CPython's rule for what is printable (`str.isprintable`: not a control, format,
 * surrogate, private-use, unassigned or separator character other than the space), which `pynum.pyStrRepr`
 * does not apply beyond the ASCII controls.
 */
export function pyStrReprFull(s: string): string {
  const quote = s.includes("'") && !s.includes('"') ? '"' : "'";
  let out = quote;
  for (const ch of s) {
    const c = ch.codePointAt(0) as number;
    if (ch === quote || ch === "\\") out += `\\${ch}`;
    else if (ch === "\n") out += "\\n";
    else if (ch === "\r") out += "\\r";
    else if (ch === "\t") out += "\\t";
    else if (c !== 0x20 && NOT_PRINTABLE.test(ch)) {
      if (c < 0x100) out += `\\x${c.toString(16).padStart(2, "0")}`;
      else if (c < 0x10000) out += `\\u${c.toString(16).padStart(4, "0")}`;
      else out += `\\U${c.toString(16).padStart(8, "0")}`;
    } else out += ch;
  }
  return out + quote;
}

/** `repr(v)` of a JSON-shaped value, as Python spells it (`None`, `True`, `1.0`, `'text'`, `[1, 2]`, `{'a': 1}`). */
export function pyValueRepr(v: unknown): string {
  if (v === null || v === undefined) return "None";
  if (v === true) return "True";
  if (v === false) return "False";
  if (typeof v === "number") return pyRepr(v);
  if (v instanceof PyFloat) return pyRepr(v.value);
  if (v instanceof PyInt) return String(v.value);
  if (typeof v === "string") return pyStrReprFull(v);
  if (Array.isArray(v)) return `[${v.map(pyValueRepr).join(", ")}]`;
  const entries = v instanceof Map ? [...v.entries()] : Object.entries(v as object);
  return `{${entries.map(([k, x]) => `${pyStrReprFull(k)}: ${pyValueRepr(x)}`).join(", ")}}`;
}

/** `str(v)`: a string as it is, anything else as its `repr` (`5`, `True`, `['#fff']`), which is what an f-string prints for a wrong-typed value. */
export const pyStr = (v: unknown): string => (typeof v === "string" ? v : pyValueRepr(v));
