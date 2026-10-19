// Shared by the Phase 3 tests (model, presets, supporting, urlstate, attribution, codecs): fixture loading, the
// outcome shape the Python side records, and the rebuilding of Python values from their tagged form.

import { createHash } from "node:crypto";
import { join } from "node:path";
import { PyInt } from "../src/pyjson.ts";
import { loadsText } from "../src/pyjsonload.ts";
import { PyError } from "../src/pynum.ts";
import { bigPyInt } from "../src/pyvalue.ts";
import { paramsFromDict, paramsJsonText } from "../src/urlstate.ts";
import type { CharacterParams } from "../src/params.ts";
import { TS_ROOT, loadJson } from "./fixtures.ts";

export const fixture = <T = any>(name: string): T => loadJson<T>(join(TS_ROOT, "fixtures", name));

export const sha256 = (text: string): string => createHash("sha256").update(text, "utf8").digest("hex");

export type Outcome = { ok?: unknown; ok_sha256?: string; err?: string; msg?: string };

/** What a call did, in the shape the Python side records: a result, or the exception class and message. */
export function outcomeOf(fn: () => unknown): Outcome {
  try {
    const r = fn();
    if (r !== null && typeof r === "object" && "face" in r && "outfit" in r) {
      return { ok_sha256: sha256(paramsJsonText(r as CharacterParams)) };
    }
    return { ok: r };
  } catch (e) {
    if (e instanceof PyError) return { err: e.pyType, msg: e.message.slice(e.pyType.length + 2) };
    return { err: (e as Error).name, msg: String((e as Error).message) };
  }
}

/** Python's expected outcome, trimmed to what `outcomeOf` can produce (the diff is for the failure message only). */
export function wanted(want: Outcome & { ok_diff?: string }): Outcome {
  if (want.ok_sha256 !== undefined) return { ok_sha256: want.ok_sha256 };
  return want.err !== undefined ? { err: want.err, msg: want.msg } : { ok: want.ok };
}

/** A character from the compact JSON of what differs from the defaults, read as a link would be. */
export const paramsFromDiff = (text: string): CharacterParams => paramsFromDict(loadsText(text) as Map<string, unknown>);

export type Tagged = { t: string; v?: unknown };

/** A Python value from the fixture's tagged spelling: `{t: "int", v: "3"}` is the int 3, `{t: "float", v: "3.0"}` a float. */
export function fromTagged(x: Tagged): unknown {
  switch (x.t) {
    case "none": return null;
    case "bool": return x.v;
    case "str": return x.v;
    case "int": {
      const big = BigInt(x.v as string);
      return Number.isSafeInteger(Number(big)) && big <= 9007199254740991n && big >= -9007199254740991n ? new PyInt(Number(big)) : bigPyInt(big);
    }
    case "float": {
      const t = x.v as string;
      return t === "nan" ? NaN : t === "inf" ? Infinity : t === "-inf" ? -Infinity : Number(t);
    }
    case "list": return (x.v as Tagged[]).map(fromTagged);
    case "dict": return new Map(Object.entries(x.v as Record<string, Tagged>).map(([k, v]) => [k, fromTagged(v)] as const));
    default: throw new Error(`unknown tag ${x.t}`);
  }
}
