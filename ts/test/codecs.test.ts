// `pyjsonload.ts` and `pycodecs.ts` against CPython's `json.loads(bytes)` and `base64.urlsafe_b64decode`: seeded
// valid, mutated and random input, with the result or the exception class and message Python gave.

import assert from "node:assert/strict";
import { test } from "node:test";
import { asciiEncode, loadsBytes, urlsafeB64decode, urlsafeB64encode } from "../src/pycodecs.ts";
import { PyInt, dumps } from "../src/pyjson.ts";
import type { Json } from "../src/pyjson.ts";
import { loadsText } from "../src/pyjsonload.ts";
import { PyError } from "../src/pynum.ts";
import { fixture } from "./phase3.ts";

const fx = fixture("codecs.json");

type Mark = { close: string } | { raw: string };
const isMark = (v: unknown): v is Mark => v !== null && typeof v === "object" && !Array.isArray(v) && !(v instanceof Map) && !(v instanceof PyInt) && ("close" in v || "raw" in v);

/** `dumps(value, compact)` without recursion: the 9998 deep inputs would overflow the writer's own stack. */
function flat(value: Json): string {
  const out: string[] = [];
  const stack: (Json | { close: string } | { raw: string })[] = [value];
  while (stack.length > 0) {
    const v = stack.pop() as Json | { close: string } | { raw: string };
    if (isMark(v) && "close" in v) out.push(v.close);
    else if (isMark(v)) out.push((v as { raw: string }).raw);
    else if (Array.isArray(v)) {
      out.push("[");
      stack.push({ close: "]" });
      for (let i = v.length - 1; i >= 0; i--) {
        stack.push(v[i] as Json);
        if (i > 0) stack.push({ raw: "," });
      }
    } else if (v instanceof Map) {
      out.push("{");
      stack.push({ close: "}" });
      const entries = [...v.entries()];
      for (let i = entries.length - 1; i >= 0; i--) {
        const [k, x] = entries[i] as [string, Json];
        stack.push(x);
        stack.push({ raw: `${dumps(k)}:` });
        if (i > 0) stack.push({ raw: "," });
      }
    } else out.push(dumps(v as Json, { compact: true }));
  }
  return out.join("");
}

type Result = { ok: string } | { err: string; msg: string };

function run(fn: () => string): Result {
  try {
    return { ok: fn() };
  } catch (e) {
    if (e instanceof PyError) return { err: e.pyType, msg: e.message.slice(e.pyType.length + 2) };
    throw e;
  }
}

const same = (got: Result, c: { ok?: string; err?: string; msg?: string }): boolean =>
  JSON.stringify(got) === JSON.stringify(c.ok !== undefined ? { ok: c.ok } : { err: c.err, msg: c.msg });

test("json.loads(bytes): result and error text match CPython on thousands of inputs", () => {
  assert.ok(fx.json.length > 2500);
  const bad: string[] = [];
  const kinds = new Set<string>();
  for (const c of fx.json) {
    const got = run(() => dumps(loadsBytes(Uint8Array.from(Buffer.from(c.hex, "hex"))), { compact: true }));
    kinds.add("ok" in got ? "ok" : got.err);
    if (!same(got, c)) bad.push(`${c.hex.slice(0, 60)}: got ${JSON.stringify(got).slice(0, 160)} want ${JSON.stringify(c).slice(0, 160)}`);
  }
  assert.deepEqual(bad.slice(0, 10), []);
  assert.deepEqual([...kinds].sort(), ["JSONDecodeError", "UnicodeDecodeError", "ok"]);
});

test("json.loads on long inputs: nesting to 9998 loads and 9999 raises RecursionError, as CPython; 4300 digits load and 4301 raise", () => {
  for (const c of fx.json_long) {
    const text = (c.parts as [string, number][]).map(([unit, n]) => unit.repeat(n)).join("");
    const got = run(() => flat(loadsText(text)));
    assert.ok(same(got, c), `${text.slice(0, 20)}...: got ${JSON.stringify(got).slice(0, 200)}`);
  }
});

test("urlsafe_b64decode: the lenient decoder gives Python's bytes or Python's error", () => {
  assert.ok(fx.base64.length > 3000);
  const bad: string[] = [];
  for (const c of fx.base64 as { s: string; ok?: string; err?: string; msg?: string }[]) {
    const n = Array.from(c.s).length;
    const got = run(() => Buffer.from(urlsafeB64decode(asciiEncode(c.s + "=".repeat((4 - (n % 4)) % 4)))).toString("hex"));
    if (!same(got, c)) bad.push(`${JSON.stringify(c.s)}: got ${JSON.stringify(got)}`);
  }
  assert.deepEqual(bad.slice(0, 10), []);
});

test("urlsafe_b64encode round-trips and uses the url-safe alphabet", () => {
  const bytes = Uint8Array.from([0xfb, 0xff, 0xfe, 0x01]);
  assert.equal(urlsafeB64encode(bytes), "-__-AQ==");
  assert.deepEqual([...urlsafeB64decode(asciiEncode("-__-AQ=="))], [...bytes]);
  assert.deepEqual([...urlsafeB64decode(asciiEncode("+//+AQ=="))], [...bytes]);
});

test("json.loads keeps ints and floats apart, accepts NaN and Infinity, and keeps big ints whole", () => {
  assert.equal(dumps(loadsText('[1,1.0,1e0,-0,-0.0,NaN,Infinity,-Infinity,123456789012345678901234567890]'), { compact: true }), "[1,1.0,1.0,0,-0.0,NaN,Infinity,-Infinity,123456789012345678901234567890]");
  assert.equal(dumps(loadsText('{"a":1,"b":2,"a":3}'), { compact: true }), '{"a":3,"b":2}');
});
