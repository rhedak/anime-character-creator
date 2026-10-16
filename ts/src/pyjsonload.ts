// `json.loads` as CPython 3.13 does it, for the one place the answer is part of the contract: a character link
// (`urlstate.decode_params`). It differs from `JSON.parse` in ways a link can reach:
//
//  * an int is not a float: `1` and `1.0` are different values and print differently when written back, so ints
//    come back as `PyInt` and every other number as a plain float (`pyjson.ts` writes both as Python does);
//  * `NaN`, `Infinity` and `-Infinity` are accepted, and `1e999` is `inf`;
//  * an int may have any number of digits (kept exactly, up to the interpreter's 4300 digit limit, which raises);
//  * a `bytes` input is decoded with `json.detect_encoding` first, and UTF-8 errors are `UnicodeDecodeError`;
//  * every error is a `JSONDecodeError` with Python's text, `Expecting value: line 1 column 1 (char 0)`;
//  * an object keeps its first-seen key order and the last value for a repeated key (a `Map`).
//
// The scanner follows `Modules/_json.c` (the C scanner `json.loads` uses), working on code points as CPython does,
// so the positions in the messages are code point offsets.

import { PyInt } from "./pyjson.ts";
import type { Json } from "./pyjson.ts";
import { PyError } from "./pynum.ts";
import { bigPyInt } from "./pyvalue.ts";

const DIGIT_LIMIT = 4300;
/** The deepest nesting the scanner accepts before CPython raises `RecursionError` (measured on 3.13.11: nesting 9998 loads, 9999 raises). */
export const MAX_DEPTH = 9998;

const err = (msg: string): PyError => new PyError("JSONDecodeError", msg);

/** `JSONDecodeError`'s text: `msg: line L column C (char P)` with `P` in code points. */
function decodeError(msg: string, cps: readonly number[], pos: number): PyError {
  let lineno = 1;
  let lastNl = -1;
  for (let i = 0; i < pos && i < cps.length; i++) {
    if (cps[i] === 10) {
      lineno++;
      lastNl = i;
    }
  }
  const colno = lastNl >= 0 ? pos - lastNl : pos + 1;
  return err(`${msg}: line ${lineno} column ${colno} (char ${pos})`);
}

class Stop extends Error {
  readonly idx: number;
  constructor(idx: number) {
    super("stop");
    this.idx = idx;
  }
}

const isWs = (c: number): boolean => c === 0x20 || c === 0x09 || c === 0x0a || c === 0x0d;
const isDigit = (c: number | undefined): boolean => c !== undefined && c >= 0x30 && c <= 0x39;

function hexValue(c: number): number {
  if (c >= 0x30 && c <= 0x39) return c - 0x30;
  if (c >= 0x61 && c <= 0x66) return c - 0x61 + 10;
  if (c >= 0x41 && c <= 0x46) return c - 0x41 + 10;
  return -1;
}

const isHigh = (c: number): boolean => c >= 0xd800 && c <= 0xdbff;
const isLow = (c: number): boolean => c >= 0xdc00 && c <= 0xdfff;

const cpString = (cps: readonly number[], from: number, to: number): string => {
  let out = "";
  for (let i = from; i < to; i += 4096) out += String.fromCodePoint(...cps.slice(i, Math.min(to, i + 4096)));
  return out;
};

/** `json.loads(text)` on a string given as code points. */
export function loadsCodePoints(cps: readonly number[]): Json {
  const len = cps.length;
  const end = len - 1;

  function scanString(cpsStart: number): [string, number] {
    const begin = cpsStart - 1;
    let pos = cpsStart;
    let out = "";
    for (;;) {
      let next = pos;
      let c = 0;
      for (; next < len; next++) {
        c = cps[next] as number;
        if (c === 0x22 || c === 0x5c) break;
        if (c <= 0x1f) throw decodeError("Invalid control character at", cps, next);
      }
      if (next >= len) throw decodeError("Unterminated string starting at", cps, begin);
      out += cpString(cps, pos, next);
      next++;
      if (c === 0x22) return [out, next];
      if (next === len) throw decodeError("Unterminated string starting at", cps, begin);
      c = cps[next] as number;
      if (c !== 0x75) {
        pos = next + 1;
        switch (c) {
          case 0x22: out += '"'; break;
          case 0x5c: out += "\\"; break;
          case 0x2f: out += "/"; break;
          case 0x62: out += "\b"; break;
          case 0x66: out += "\f"; break;
          case 0x6e: out += "\n"; break;
          case 0x72: out += "\r"; break;
          case 0x74: out += "\t"; break;
          default: throw decodeError("Invalid \\escape", cps, pos - 2);
        }
      } else {
        next++;
        let e = next + 4;
        if (e >= len) throw decodeError("Invalid \\uXXXX escape", cps, next - 1);
        let u = 0;
        for (; next < e; next++) {
          const h = hexValue(cps[next] as number);
          if (h < 0) throw decodeError("Invalid \\uXXXX escape", cps, e - 5);
          u = (u << 4) | h;
        }
        if (isHigh(u) && e + 6 < len && cps[next++] === 0x5c && cps[next++] === 0x75) {
          let u2 = 0;
          e += 6;
          for (; next < e; next++) {
            const h = hexValue(cps[next] as number);
            if (h < 0) throw decodeError("Invalid \\uXXXX escape", cps, e - 5);
            u2 = (u2 << 4) | h;
          }
          if (isLow(u2)) u = 0x10000 + (((u - 0xd800) << 10) | (u2 - 0xdc00));
          else e -= 6;
        }
        pos = e;
        out += String.fromCodePoint(u);
      }
    }
  }

  function matchNumber(start: number): [Json, number] {
    let idx = start;
    if (idx > end) throw new Stop(start);
    if (cps[idx] === 0x2d) {
      idx++;
      if (idx > end) throw new Stop(start);
    }
    const first = cps[idx] as number;
    if (first >= 0x31 && first <= 0x39) {
      idx++;
      while (idx <= end && isDigit(cps[idx])) idx++;
    } else if (first === 0x30) {
      idx++;
    } else {
      throw new Stop(start);
    }
    let isFloat = false;
    if (idx < end && cps[idx] === 0x2e && isDigit(cps[idx + 1])) {
      isFloat = true;
      idx += 2;
      while (idx <= end && isDigit(cps[idx])) idx++;
    }
    if (idx < end && (cps[idx] === 0x65 || cps[idx] === 0x45)) {
      const eStart = idx;
      idx++;
      if (idx < end && (cps[idx] === 0x2d || cps[idx] === 0x2b)) idx++;
      while (idx <= end && isDigit(cps[idx])) idx++;
      if (isDigit(cps[idx - 1])) isFloat = true;
      else idx = eStart;
    }
    const text = cpString(cps, start, idx);
    if (isFloat) return [Number(text), idx];
    const digits = text.startsWith("-") ? text.length - 1 : text.length;
    if (digits > DIGIT_LIMIT) {
      throw new PyError(
        "ValueError",
        `Exceeds the limit (${DIGIT_LIMIT} digits) for integer string conversion: value has ${digits} digits; use sys.set_int_max_str_digits() to increase the limit`,
      );
    }
    if (digits <= 15) return [new PyInt(Number(text) + 0), idx];
    const big = BigInt(text);
    const abs = big < 0n ? -big : big;
    return [abs <= 9007199254740991n ? new PyInt(Number(big)) : bigPyInt(big), idx];
  }

  const matches = (at: number, word: string): boolean => {
    for (let i = 0; i < word.length; i++) if (cps[at + i] !== word.charCodeAt(i)) return false;
    return true;
  };

  function skipWs(idx: number): number {
    while (idx <= end && isWs(cps[idx] as number)) idx++;
    return idx;
  }

  /** One scalar (a string, a literal or a number) at `idx`, or `undefined` where a container opens. */
  function scanScalar(idx: number): [Json, number] | undefined {
    if (idx >= len) throw new Stop(idx);
    const c = cps[idx] as number;
    switch (c) {
      case 0x22: return scanString(idx + 1);
      case 0x7b:
      case 0x5b: return undefined;
      case 0x6e: if (matches(idx + 1, "ull")) return [null, idx + 4]; break;
      case 0x74: if (matches(idx + 1, "rue")) return [true, idx + 4]; break;
      case 0x66: if (matches(idx + 1, "alse")) return [false, idx + 5]; break;
      case 0x4e: if (matches(idx + 1, "aN")) return [NaN, idx + 3]; break;
      case 0x49: if (matches(idx + 1, "nfinity")) return [Infinity, idx + 8]; break;
      case 0x2d: if (matches(idx + 1, "Infinity")) return [-Infinity, idx + 9]; break;
      default: break;
    }
    return matchNumber(idx);
  }

  // The scanner of `_json.c` recurses once per container; this keeps its own stack instead, so that the
  // 9998 levels CPython allows do not overflow the JS stack, and counts levels the same way.
  type Frame = { readonly list: Json[] | null; readonly map: Map<string, Json> | null; key: string };

  function overflow(what: string): PyError {
    return new PyError("RecursionError", `maximum recursion depth exceeded while decoding a JSON ${what} from a unicode string`);
  }

  /** The key of an object's next pair and the index of its value: `"key" : ` with whitespace around the colon. */
  function readKey(idx: number): [string, number] {
    if (idx > end || cps[idx] !== 0x22) throw decodeError("Expecting property name enclosed in double quotes", cps, idx);
    const [key, afterKey] = scanString(idx + 1);
    const colon = skipWs(afterKey);
    if (colon > end || cps[colon] !== 0x3a) throw decodeError("Expecting ':' delimiter", cps, colon);
    return [key, skipWs(colon + 1)];
  }

  function scanValue(start: number): [Json, number] {
    const stack: Frame[] = [];
    let idx = start;
    for (;;) {
      // A value starts at `idx`: a scalar, an empty container, or the opening of a full one.
      let value: Json;
      const scalar = scanScalar(idx);
      if (scalar !== undefined) {
        [value, idx] = scalar;
      } else if (cps[idx] === 0x7b) {
        if (stack.length + 1 > MAX_DEPTH) throw overflow("object");
        idx = skipWs(idx + 1);
        if (idx > end || cps[idx] !== 0x7d) {
          const frame: Frame = { list: null, map: new Map<string, Json>(), key: "" };
          [frame.key, idx] = readKey(idx);
          stack.push(frame);
          continue;
        }
        value = new Map<string, Json>();
        idx += 1;
      } else {
        if (stack.length + 1 > MAX_DEPTH) throw overflow("array");
        idx = skipWs(idx + 1);
        if (idx > end || cps[idx] !== 0x5d) {
          stack.push({ list: [], map: null, key: "" });
          continue;
        }
        value = [];
        idx += 1;
      }
      // Hand the finished value to its parent, closing every container that it finishes.
      for (;;) {
        const frame = stack[stack.length - 1];
        if (frame === undefined) return [value, idx];
        const close = frame.list ? 0x5d : 0x7d;
        if (frame.list) frame.list.push(value);
        else (frame.map as Map<string, Json>).set(frame.key, value);
        idx = skipWs(idx);
        if (idx <= end && cps[idx] === close) {
          idx += 1;
          value = frame.list ?? (frame.map as Map<string, Json>);
          stack.pop();
          continue;
        }
        if (idx > end || cps[idx] !== 0x2c) throw decodeError("Expecting ',' delimiter", cps, idx);
        const comma = idx;
        idx = skipWs(idx + 1);
        if (idx <= end && cps[idx] === close) {
          throw decodeError(`Illegal trailing comma before end of ${frame.list ? "array" : "object"}`, cps, comma);
        }
        if (!frame.list) [frame.key, idx] = readKey(idx);
        break;
      }
    }
  }

  let value: Json;
  let after: number;
  try {
    [value, after] = scanValue(skipWs(0));
  } catch (e) {
    if (e instanceof Stop) throw decodeError("Expecting value", cps, e.idx);
    throw e;
  }
  const tail = skipWs(after);
  if (tail !== len) throw decodeError("Extra data", cps, tail);
  return value;
}

/** `json.loads(text)` on a JS string (its code points, so an astral character is one position). */
export function loadsText(text: string): Json {
  return loadsCodePoints(Array.from(text, (ch) => ch.codePointAt(0) as number));
}
