// The codecs a character link goes through, as CPython 3.13 does them: `str.encode("ascii")`, the lenient
// `base64.urlsafe_b64decode`, and `json.loads(bytes)` (`json.detect_encoding`, then a `surrogatepass` decode).
// The point is the same as `pyjsonload.ts`: a link is user input, and what Python accepts, refuses and says
// about it is part of the contract.

import type { Json } from "./pyjson.ts";
import { loadsCodePoints } from "./pyjsonload.ts";
import { PyError } from "./pynum.ts";

// ---------------------------------------------------------------------------------------------------------
// str.encode("ascii")

/** The `\xNN`, `\uNNNN` or `\UNNNNNNNN` spelling `UnicodeEncodeError` uses for a character. */
function escapeChar(c: number): string {
  if (c < 0x100) return `\\x${c.toString(16).padStart(2, "0")}`;
  if (c < 0x10000) return `\\u${c.toString(16).padStart(4, "0")}`;
  return `\\U${c.toString(16).padStart(8, "0")}`;
}

/** `s.encode("ascii")`: the bytes, or `UnicodeEncodeError` naming the first run of characters above 127. */
export function asciiEncode(s: string): Uint8Array {
  const cps = Array.from(s, (ch) => ch.codePointAt(0) as number);
  const out = new Uint8Array(cps.length);
  for (let i = 0; i < cps.length; i++) {
    const c = cps[i] as number;
    if (c < 128) {
      out[i] = c;
      continue;
    }
    let j = i;
    while (j < cps.length && (cps[j] as number) >= 128) j++;
    const where = j - i === 1 ? `character '${escapeChar(c)}' in position ${i}` : `characters in position ${i}-${j - 1}`;
    throw new PyError("UnicodeEncodeError", `'ascii' codec can't encode ${where}: ordinal not in range(128)`);
  }
  return out;
}

// ---------------------------------------------------------------------------------------------------------
// base64

const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";

/** `base64.urlsafe_b64encode(data)`, padding included. */
export function urlsafeB64encode(data: Uint8Array): string {
  let out = "";
  for (let i = 0; i < data.length; i += 3) {
    const a = data[i] as number;
    const b = i + 1 < data.length ? (data[i + 1] as number) : 0;
    const c = i + 2 < data.length ? (data[i + 2] as number) : 0;
    out += ALPHABET[a >> 2];
    out += ALPHABET[((a & 3) << 4) | (b >> 4)];
    out += i + 1 < data.length ? ALPHABET[((b & 15) << 2) | (c >> 6)] : "=";
    out += i + 2 < data.length ? ALPHABET[c & 63] : "=";
  }
  return out;
}

function sextet(ch: number): number {
  if (ch >= 0x41 && ch <= 0x5a) return ch - 0x41;
  if (ch >= 0x61 && ch <= 0x7a) return ch - 0x61 + 26;
  if (ch >= 0x30 && ch <= 0x39) return ch - 0x30 + 52;
  if (ch === 0x2b || ch === 0x2d) return 62; // `+`, and `-` after `urlsafe_b64decode`'s translation
  if (ch === 0x2f || ch === 0x5f) return 63; // `/`, and `_`
  return -1;
}

/**
 * `base64.urlsafe_b64decode(data)`: `-` and `_` become `+` and `/`, then `binascii.a2b_base64` in its lenient
 * mode. A character outside the alphabet is skipped without a word; `=` counts only after at least two data
 * characters and ends the input once the quad is full; a short quad is `Incorrect padding`, and exactly one
 * stray data character is its own error. `data` is ASCII (the caller has already encoded it).
 */
export function urlsafeB64decode(data: Uint8Array): Uint8Array {
  const out: number[] = [];
  let quad = 0;
  let left = 0;
  let pads = 0;
  for (let i = 0; i < data.length; i++) {
    const ch = data[i] as number;
    if (ch === 0x3d) {
      if (quad >= 2 && quad + ++pads >= 4) {
        quad = 0;
        left = 0;
        break;
      }
      continue;
    }
    const v = sextet(ch);
    if (v < 0) continue;
    pads = 0;
    switch (quad) {
      case 0: quad = 1; left = v; break;
      case 1: quad = 2; out.push((left << 2) | (v >> 4)); left = v & 0x0f; break;
      case 2: quad = 3; out.push((left << 4) | (v >> 2)); left = v & 0x03; break;
      default: quad = 0; out.push((left << 6) | v); left = 0; break;
    }
  }
  if (quad !== 0) {
    if (quad === 1) {
      throw new PyError(
        "Error",
        `Invalid base64-encoded string: number of data characters (${Math.floor(out.length / 3) * 4 + 1}) cannot be 1 more than a multiple of 4`,
      );
    }
    throw new PyError("Error", "Incorrect padding");
  }
  return Uint8Array.from(out);
}

// ---------------------------------------------------------------------------------------------------------
// bytes to text, for json.loads

function hex2(b: number): string {
  return b.toString(16).padStart(2, "0");
}

function decodeFailure(codec: string, bytes: Uint8Array, start: number, end: number, reason: string, base = 0): PyError {
  const where =
    end === start + 1
      ? `byte 0x${hex2(bytes[start] as number)} in position ${start + base}`
      : `bytes in position ${start + base}-${end - 1 + base}`;
  return new PyError("UnicodeDecodeError", `'${codec}' codec can't decode ${where}: ${reason}`);
}

const isCont = (b: number | undefined): boolean => b !== undefined && (b & 0xc0) === 0x80;

/** `bytes.decode("utf-8", "surrogatepass")` to code points, with CPython's errors and positions. */
export function utf8DecodeSurrogatePass(bytes: Uint8Array, codec = "utf-8"): number[] {
  const out: number[] = [];
  const n = bytes.length;
  let i = 0;
  while (i < n) {
    const b0 = bytes[i] as number;
    if (b0 < 0x80) {
      out.push(b0);
      i++;
      continue;
    }
    if (b0 < 0xc2 || b0 > 0xf4) throw decodeFailure(codec, bytes, i, i + 1, "invalid start byte");
    const avail = n - i;
    if (b0 < 0xe0) {
      if (avail < 2) throw decodeFailure(codec, bytes, i, n, "unexpected end of data");
      if (!isCont(bytes[i + 1])) throw decodeFailure(codec, bytes, i, i + 1, "invalid continuation byte");
      out.push(((b0 & 0x1f) << 6) | ((bytes[i + 1] as number) & 0x3f));
      i += 2;
      continue;
    }
    if (b0 < 0xf0) {
      const b1 = bytes[i + 1];
      // The second byte is out of range for the strict decoder after E0 below A0 and after ED at A0 or above
      // (a surrogate); `surrogatepass` then takes a whole surrogate if its third byte is there.
      const badSecond = !isCont(b1) || (b0 === 0xe0 && (b1 as number) < 0xa0) || (b0 === 0xed && (b1 as number) >= 0xa0);
      if (avail < 3) {
        if (avail < 2) throw decodeFailure(codec, bytes, i, n, "unexpected end of data");
        if (badSecond) throw decodeFailure(codec, bytes, i, i + 1, "invalid continuation byte");
        throw decodeFailure(codec, bytes, i, n, "unexpected end of data");
      }
      const b2 = bytes[i + 2];
      if (badSecond) {
        if (!(b0 === 0xed && isCont(b1) && (b1 as number) >= 0xa0 && isCont(b2))) {
          throw decodeFailure(codec, bytes, i, i + 1, "invalid continuation byte");
        }
      } else if (!isCont(b2)) {
        throw decodeFailure(codec, bytes, i, i + 2, "invalid continuation byte");
      }
      out.push(((b0 & 0x0f) << 12) | (((b1 as number) & 0x3f) << 6) | ((b2 as number) & 0x3f));
      i += 3;
      continue;
    }
    const b1 = bytes[i + 1];
    const badSecond = !isCont(b1) || (b0 === 0xf0 && (b1 as number) < 0x90) || (b0 === 0xf4 && (b1 as number) >= 0x90);
    if (avail < 4) {
      if (avail < 2) throw decodeFailure(codec, bytes, i, n, "unexpected end of data");
      if (badSecond) throw decodeFailure(codec, bytes, i, i + 1, "invalid continuation byte");
      if (avail < 3) throw decodeFailure(codec, bytes, i, n, "unexpected end of data");
      if (!isCont(bytes[i + 2])) throw decodeFailure(codec, bytes, i, i + 2, "invalid continuation byte");
      throw decodeFailure(codec, bytes, i, n, "unexpected end of data");
    }
    if (badSecond) throw decodeFailure(codec, bytes, i, i + 1, "invalid continuation byte");
    if (!isCont(bytes[i + 2])) throw decodeFailure(codec, bytes, i, i + 2, "invalid continuation byte");
    if (!isCont(bytes[i + 3])) throw decodeFailure(codec, bytes, i, i + 3, "invalid continuation byte");
    out.push(
      ((b0 & 0x07) << 18) | (((b1 as number) & 0x3f) << 12) | (((bytes[i + 2] as number) & 0x3f) << 6) | ((bytes[i + 3] as number) & 0x3f),
    );
    i += 4;
  }
  return out;
}

/** UTF-16 to code points (`surrogatepass`: a lone surrogate is kept). Errors are Python's class, with its common wording. */
function utf16Decode(bytes: Uint8Array, codec: string, littleEndian: boolean, base = 0): number[] {
  const out: number[] = [];
  const n = bytes.length;
  let i = 0;
  const unit = (at: number): number => (littleEndian ? (bytes[at] as number) | ((bytes[at + 1] as number) << 8) : ((bytes[at] as number) << 8) | (bytes[at + 1] as number));
  while (i < n) {
    if (n - i < 2) throw decodeFailure(codec, bytes, i, n, "truncated data", base);
    const u = unit(i);
    if (u >= 0xd800 && u <= 0xdbff) {
      if (n - i < 4) throw decodeFailure(codec, bytes, i, n, "unexpected end of data", base);
      const u2 = unit(i + 2);
      if (u2 >= 0xdc00 && u2 <= 0xdfff) {
        out.push(0x10000 + ((u - 0xd800) << 10) + (u2 - 0xdc00));
        i += 4;
        continue;
      }
      throw decodeFailure(codec, bytes, i, i + 2, "illegal UTF-16 surrogate", base);
    }
    out.push(u);
    i += 2;
  }
  return out;
}

/** UTF-32 to code points. */
function utf32Decode(bytes: Uint8Array, codec: string, littleEndian: boolean, base = 0): number[] {
  const out: number[] = [];
  const n = bytes.length;
  for (let i = 0; i < n; i += 4) {
    if (n - i < 4) throw decodeFailure(codec, bytes, i, n, "truncated data", base);
    const b = [bytes[i] as number, bytes[i + 1] as number, bytes[i + 2] as number, bytes[i + 3] as number];
    const u = (littleEndian ? (b[3] as number) * 0x1000000 + ((b[2] as number) << 16) + ((b[1] as number) << 8) + (b[0] as number) : (b[0] as number) * 0x1000000 + ((b[1] as number) << 16) + ((b[2] as number) << 8) + (b[3] as number));
    if (u > 0x10ffff) throw decodeFailure(codec, bytes, i, i + 4, "code point not in range(0x110000)", base);
    out.push(u);
  }
  return out;
}

/** `json.detect_encoding(b)`. */
export function detectEncoding(b: Uint8Array): string {
  const starts = (...prefix: number[]): boolean => prefix.every((x, i) => b[i] === x);
  if (starts(0x00, 0x00, 0xfe, 0xff) || starts(0xff, 0xfe, 0x00, 0x00)) return "utf-32";
  if (starts(0xfe, 0xff) || starts(0xff, 0xfe)) return "utf-16";
  if (starts(0xef, 0xbb, 0xbf)) return "utf-8-sig";
  if (b.length >= 4) {
    if (!b[0]) return b[1] ? "utf-16-be" : "utf-32-be";
    if (!b[1]) return b[2] || b[3] ? "utf-16-le" : "utf-32-le";
  } else if (b.length === 2) {
    if (!b[0]) return "utf-16-be";
    if (!b[1]) return "utf-16-le";
  }
  return "utf-8";
}

/** `bytes.decode(detect_encoding(bytes), "surrogatepass")`, to code points. */
export function jsonDecodeBytes(bytes: Uint8Array): number[] {
  const enc = detectEncoding(bytes);
  switch (enc) {
    case "utf-8":
      return utf8DecodeSurrogatePass(bytes);
    case "utf-8-sig":
      return utf8DecodeSurrogatePass(bytes.subarray(3), "utf-8");
    case "utf-16-be":
      return utf16Decode(bytes, enc, false);
    case "utf-16-le":
      return utf16Decode(bytes, enc, true);
    case "utf-16": {
      // The BOM picks the byte order and is dropped.
      const le = bytes[0] === 0xff;
      return utf16Decode(bytes.subarray(2), le ? "utf-16-le" : "utf-16-be", le, 2);
    }
    case "utf-32-be":
      return utf32Decode(bytes, enc, false);
    case "utf-32-le":
      return utf32Decode(bytes, enc, true);
    default: {
      const le = bytes[0] === 0xff;
      return utf32Decode(bytes.subarray(4), le ? "utf-32-le" : "utf-32-be", le, 4);
    }
  }
}

/** `json.loads(data)` for `bytes`. */
export function loadsBytes(data: Uint8Array): Json {
  return loadsCodePoints(jsonDecodeBytes(data));
}
