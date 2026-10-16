// Decoding the recorded calls (`harness/ts_port/calls.py`) and comparing a TypeScript result with what Python returned.
//
// Encoding: "f:" + 16 hex digits of the double, "i:" integer, "b:1"/"b:0", "s:" text, null, {t: [...]} tuple, {l: [...]} list,
// {d: [[k, v], ...]} dict, {set: [...]}, {dc: "Class", f: {...}} dataclass, {ref: "NAME.key"} a registry object, {exc, msg} an
// exception. JavaScript has one number type and one array type, so int against float and tuple against list are not told
// apart: a float is compared by bits (within a few ulp where the maths library is involved), an int by value.

import { PyInt } from "../src/pyjson.ts";
import { BadValue } from "../src/pynum.ts";
import { FIELDS, classOf, type ClassName } from "../src/model.ts";
import { plainParams } from "../src/plain.ts";
import { PyFloat } from "../src/pyvalue.ts";
import { decodeFloat, encodeFloat } from "./fixtures.ts";

export type Enc = null | string | { [k: string]: any };
export type Refs = (name: string) => unknown;

export function decode(v: Enc, refs: Refs): unknown {
  if (v === null) return null;
  if (typeof v === "string") {
    const tag = v.slice(0, 2);
    const body = v.slice(2);
    if (tag === "f:") return decodeFloat(v);
    if (tag === "i:") return Number(body);
    if (tag === "b:") return body === "1";
    if (tag === "s:") return body;
    throw new Error(`unknown scalar encoding ${v.slice(0, 20)}`);
  }
  if ("t" in v) return (v.t as Enc[]).map((x) => decode(x, refs));
  if ("l" in v) return (v.l as Enc[]).map((x) => decode(x, refs));
  if ("set" in v) return new Set((v.set as Enc[]).map((x) => decode(x, refs)));
  if ("d" in v) {
    const pairs = (v.d as [Enc, Enc][]).map(([k, x]) => [decode(k, refs), decode(x, refs)] as const);
    return pairs.every(([k]) => typeof k === "string") ? Object.fromEntries(pairs) : new Map(pairs);
  }
  if ("dc" in v) {
    const specs = new Map((FIELDS[v.dc as ClassName] ?? []).map((f) => [f.name, f.type]));
    return Object.fromEntries(
      Object.entries(v.f as Record<string, Enc>).map(([k, x]) => {
        const val = decode(x, refs);
        // A link keeps Python's int in a float field and float in an int field: markers say so where the registry would not.
        const tag = specs.get(k);
        if (typeof x === "string" && x.startsWith("i:") && tag !== "int" && typeof val === "number") return [k, new PyInt(val)];
        if (typeof x === "string" && x.startsWith("f:") && tag === "int" && typeof val === "number") return [k, new PyFloat(val)];
        return [k, val];
      }),
    );
  }
  if ("ref" in v) return refs(v.ref as string);
  throw new Error(`unknown encoding ${JSON.stringify(v).slice(0, 80)}`);
}

const ulps = (a: number, b: number): number => {
  if (a === b) return 0;
  if (!Number.isFinite(a) || !Number.isFinite(b)) return Infinity;
  return Math.abs(a - b) / Math.max(Number.MIN_VALUE, Math.abs(a) * 2 ** -52);
};

export interface Tally {
  exact: number;
  withinUlps: number;
}

/** Whether `got` is what Python returned (`py`). `tol` is the largest difference in ulps accepted for a float; `tally` counts them. */
export function same(py: Enc, got: unknown, refs: Refs, tol: number, tally: Tally): boolean {
  // A link keeps Python's int and float apart with markers; the comparison is of the numbers.
  if (got instanceof BadValue) got = got.original;
  if (got instanceof PyInt) got = Number(got.value);
  else if (got instanceof PyFloat) got = got.value;
  if (py === null) return got === null || got === undefined;
  if (typeof py === "string") {
    const tag = py.slice(0, 2);
    if (tag === "f:") {
      if (typeof got !== "number") return false;
      const want = decodeFloat(py);
      if (encodeFloat(want) === encodeFloat(got) || (want !== want && got !== got)) {
        tally.exact++;
        return true;
      }
      const u = ulps(want, got);
      if (u <= tol) {
        tally.withinUlps++;
        return true;
      }
      return false;
    }
    if (tag === "i:") return typeof got === "number" && got === Number(py.slice(2));
    if (tag === "b:") return got === (py.slice(2) === "1");
    return got === py.slice(2);
  }
  if ("t" in py || "l" in py) {
    const items = (py.t ?? py.l) as Enc[];
    return Array.isArray(got) && got.length === items.length && items.every((x, i) => same(x, got[i], refs, tol, tally));
  }
  if ("set" in py) {
    const items = py.set as Enc[];
    return got instanceof Set && got.size === items.length && items.every((x) => [...got].some((g) => same(x, g, refs, tol, tally)));
  }
  if ("d" in py) {
    const pairs = py.d as [Enc, Enc][];
    if (got instanceof Map) return got.size === pairs.length && pairs.every(([k, x]) => [...got].some(([gk, gv]) => same(k, gk, refs, tol, tally) && same(x, gv, refs, tol, tally)));
    if (typeof got === "object" && got !== null) {
      const o = got as Record<string, unknown>;
      return Object.keys(o).length === pairs.length && pairs.every(([k, x]) => typeof k === "string" && same(x, o[k.slice(2)], refs, tol, tally));
    }
    return false;
  }
  if ("dc" in py) {
    if (typeof got !== "object" || got === null) return false;
    const o = got as Record<string, unknown>;
    return Object.entries(py.f as Record<string, Enc>).every(([k, x]) => same(x, o[k], refs, tol, tally));
  }
  if ("ref" in py) return got === refs(py.ref as string) || JSON.stringify(got) === JSON.stringify(refs(py.ref as string));
  return false;
}

/**
 * A recorded argument as the real flow hands it to a function. The codec decodes a dataclass as its raw fields, with the int
 * markers a link needs; the drawing is handed `plainParams(p)` and a skeleton as `buildSkeleton` stores one: a number field
 * holding a string or a list is a `BadValue`, an int is a plain number. `urlstate` functions take the raw, typed form.
 */
export function normalizeForFlow(v: unknown): unknown {
  if (Array.isArray(v)) return v.map(normalizeForFlow);
  if (v === null || typeof v !== "object" || v instanceof Set || v instanceof Map) return v;
  const o = v as Record<string, unknown>;
  if (classOf(o) === "CharacterParams") return plainParams(o as never);
  if ("canvas_w" in o && "waist_half_w" in o && "head_cx" in o) {
    return Object.fromEntries(
      Object.entries(o).map(([k, x]) => {
        if (x instanceof PyInt) return [k, Number(x.value)];
        if (x instanceof PyFloat) return [k, x.value];
        // `wrist_x` and `wrist_y` are the two fields that may be None.
        if ((x === null && (k === "wrist_x" || k === "wrist_y")) || typeof x === "number" || typeof x === "boolean" || x instanceof BadValue) return [k, x];
        return [k, new BadValue(x)];
      }),
    );
  }
  return v;
}

/** An argument for a parameter annotated `float` or `int`: a string, list or None there is what `plainParams` would make a `BadValue`. */
export function asAnnotatedParam(annotation: string | undefined, v: unknown): unknown {
  const nullable = annotation?.includes("None") ?? false;
  const base = annotation?.replace(/\s*\|\s*None/, "");
  if ((base === "float" || base === "int") && (typeof v === "string" || Array.isArray(v) || (v === null && !nullable))) return new BadValue(v);
  return v;
}
