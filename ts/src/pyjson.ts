// `json.dumps` as Python writes it, for the places where bytes matter (the embedded share link, `catalogue.json`,
// the manifest hashes). JS cannot tell the int 1 from the float 1.0, so an int that must print as one is wrapped
// in `PyInt`; every other number is a float and prints with Python's float repr (`1.0`, `1e-05`).

import { PY_TRUTH, compareCodePoints, pyRepr } from "./pynum.ts";

/** An integer that `dumps` prints without a decimal point. */
export class PyInt {
  readonly value: number;
  constructor(value: number) {
    this.value = value;
  }
  [PY_TRUTH](): boolean {
    return (this.value as unknown as number | bigint) !== 0 && (this.value as unknown as number | bigint) !== 0n;
  }
}

export type Json = null | boolean | number | string | PyInt | readonly Json[] | ReadonlyMap<string, Json> | { readonly [key: string]: Json };

export interface DumpsOptions {
  /** `sort_keys`. Default false. */
  readonly sortKeys?: boolean;
  /** `separators`: `[",", ":"]` for the compact form, `[", ", ": "]` (the default) otherwise. */
  readonly compact?: boolean;
  /** `indent` (a number of spaces). */
  readonly indent?: number;
  /** `ensure_ascii`. Default true. */
  readonly ensureAscii?: boolean;
}

function quote(s: string, ensureAscii: boolean): string {
  let out = '"';
  for (const ch of s) {
    const c = ch.codePointAt(0) as number;
    if (ch === '"') out += '\\"';
    else if (ch === "\\") out += "\\\\";
    else if (ch === "\n") out += "\\n";
    else if (ch === "\r") out += "\\r";
    else if (ch === "\t") out += "\\t";
    else if (ch === "\b") out += "\\b";
    else if (ch === "\f") out += "\\f";
    else if (c < 0x20 || (ensureAscii && c > 0x7e)) {
      if (c > 0xffff) {
        const v = c - 0x10000;
        out += `\\u${(0xd800 + (v >> 10)).toString(16).padStart(4, "0")}\\u${(0xdc00 + (v & 0x3ff)).toString(16).padStart(4, "0")}`;
      } else {
        out += `\\u${c.toString(16).padStart(4, "0")}`;
      }
    } else out += ch;
  }
  return `${out}"`;
}

function num(x: number): string {
  if (x !== x) return "NaN";
  if (x === Infinity) return "Infinity";
  if (x === -Infinity) return "-Infinity";
  return pyRepr(x);
}

export function dumps(value: Json, options: DumpsOptions = {}): string {
  const sortKeys = options.sortKeys ?? false;
  const ensureAscii = options.ensureAscii ?? true;
  const indent = options.indent;
  const itemSep = options.compact ? "," : indent !== undefined ? "," : ", ";
  const keySep = options.compact ? ":" : ": ";

  const write = (v: Json, depth: number): string => {
    if (v === null) return "null";
    if (v === true) return "true";
    if (v === false) return "false";
    if (typeof v === "number") return num(v);
    if (typeof v === "string") return quote(v, ensureAscii);
    if (v instanceof PyInt) return String(v.value);
    const pad = (d: number): string => (indent === undefined ? "" : `\n${" ".repeat(indent * d)}`);
    if (Array.isArray(v)) {
      if (v.length === 0) return "[]";
      return `[${v.map((x) => `${pad(depth + 1)}${write(x, depth + 1)}`).join(itemSep)}${pad(depth)}]`;
    }
    let entries: [string, Json][];
    if (v instanceof Map) {
      entries = [...v.entries()];
    } else {
      entries = Object.entries(v as { [key: string]: Json });
      // A JS object lists integer-like keys first and in order, whatever the insertion order; Python keeps insertion order.
      if (!sortKeys && entries.some(([k]) => /^(0|[1-9]\d*)$/.test(k))) {
        throw new Error("dumps: an integer-like key would be reordered by a JS object; pass a Map to keep insertion order");
      }
    }
    if (entries.length === 0) return "{}";
    if (sortKeys) entries.sort(([a], [b]) => compareCodePoints(a, b));
    return `{${entries
      .map(([k, x]) => `${pad(depth + 1)}${quote(k, ensureAscii)}${keySep}${write(x, depth + 1)}`)
      .join(itemSep)}${pad(depth)}}`;
  };
  return write(value, 0);
}
