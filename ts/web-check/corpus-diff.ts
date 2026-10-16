// The full corpus's diff form turned into characters. Browser-safe (no Node imports): the tests (`test/corpus.ts`) and the
// cross-engine page (`web-check/check.ts`) both use it.

import { FIELDS, characterParams, faceStyle, outfit, type ClassName } from "../src/model.ts";
import type { CharacterParams } from "../src/params.ts";
import type { Json } from "../src/pyjson.ts";
import { loadsText } from "../src/pyjsonload.ts";
import { PyFloat } from "../src/pyvalue.ts";

export interface RenderKw {
  id_prefix?: string;
  background?: string | null;
  metadata?: unknown;
}
export interface FullCase {
  id: string;
  params: CharacterParams;
  kw: RenderKw;
}

/** A decoded JSON value with objects turned into plain objects; ints stay `PyInt` and floats stay numbers. */
export function plainObjects(v: Json | unknown): unknown {
  // JSON has no spelling for nan and inf; the corpus writes `{"$float": "nan" | "inf" | "-inf"}`.
  if (v instanceof Map && v.size === 1 && v.has("$float")) {
    const kind = v.get("$float");
    if (kind === "nan") return NaN;
    if (kind === "inf") return Infinity;
    if (kind === "-inf") return -Infinity;
    throw new Error(`unknown $float marker ${String(kind)}`);
  }
  if (v instanceof Map) return Object.fromEntries([...v].map(([k, x]) => [k, plainObjects(x)]));
  if (Array.isArray(v)) return v.map(plainObjects);
  return v;
}

/**
 * JSON gives an int as `PyInt` and a float as a plain number; the registry reads a plain number in an `int` field as an int. So a
 * float written there (`"shoulder_bars": 1.0`) has to be marked, as `urlstate` does for a link.
 */
function typedFloats(cls: ClassName, fields: Record<string, unknown>): Record<string, unknown> {
  const out = { ...fields };
  for (const f of FIELDS[cls]) {
    const v = out[f.name];
    if (f.type === "int" && typeof v === "number") out[f.name] = new PyFloat(v);
  }
  return out;
}

/** A character from the corpus's diff form: the fields that differ from the defaults, with nested `outfit` and `face` dicts. */
export function paramsFromDiff(p: Record<string, unknown>): CharacterParams {
  const { outfit: o, face: f, ...top } = p;
  return characterParams({
    ...(top as Partial<CharacterParams>),
    ...(top && Object.keys(top).length ? typedFloats("CharacterParams", top) : {}),
    outfit: outfit(typedFloats("Outfit", (o ?? {}) as Record<string, unknown>) as object),
    face: faceStyle(typedFloats("FaceStyle", (f ?? {}) as Record<string, unknown>) as object),
  });
}

/** `corpus/full.json`'s text as cases. Python's `json.loads` keeps `1` and `1.0` apart, which `JSON.parse` cannot. */
export function parseFullCorpus(text: string): FullCase[] {
  return (loadsText(text) as Json[]).map((e) => {
    const m = plainObjects(e) as { id: string; kw: RenderKw; p: Record<string, unknown> };
    return { id: m.id, params: paramsFromDiff(m.p), kw: m.kw };
  });
}

/** UTF-8 with `surrogatepass`, as the Python side hashes a document that holds a lone surrogate. */
export function utf8SurrogatePass(s: string): Uint8Array {
  const bytes: number[] = [];
  for (let i = 0; i < s.length; i++) {
    let c = s.charCodeAt(i);
    if (c >= 0xd800 && c <= 0xdbff && i + 1 < s.length) {
      const d = s.charCodeAt(i + 1);
      if (d >= 0xdc00 && d <= 0xdfff) {
        c = 0x10000 + ((c - 0xd800) << 10) + (d - 0xdc00);
        i++;
      }
    }
    if (c < 0x80) bytes.push(c);
    else if (c < 0x800) bytes.push(0xc0 | (c >> 6), 0x80 | (c & 63));
    else if (c < 0x10000) bytes.push(0xe0 | (c >> 12), 0x80 | ((c >> 6) & 63), 0x80 | (c & 63));
    else bytes.push(0xf0 | (c >> 18), 0x80 | ((c >> 12) & 63), 0x80 | ((c >> 6) & 63), 0x80 | (c & 63));
  }
  return Uint8Array.from(bytes);
}
