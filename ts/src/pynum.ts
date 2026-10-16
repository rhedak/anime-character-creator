// The kernel: every Python behaviour the drawing code relies on that JavaScript does not give for free.
//
// Nothing else in the port may call `toFixed`, `Math.round`, `Math.hypot`, `Array.prototype.sort` without a
// comparator, `%` on a possibly negative operand, `x[-1]`, `===` on arrays, or test a container for
// truthiness. `docs/ts-port-plan.md`, sections 5.2 and 6, say why; each function below names the Python
// behaviour it reproduces.

/** A Python exception: its class name and its message, so the port can raise what Python raises. */
export class PyError extends Error {
  readonly pyType: string;
  constructor(pyType: string, message: string) {
    super(`${pyType}: ${message}`);
    this.name = pyType;
    this.pyType = pyType;
  }
}

// ---------------------------------------------------------------------------------------------------------
// Float to text

const POW10 = [1, 10, 100, 1e3, 1e4, 1e5, 1e6];
const view = new DataView(new ArrayBuffer(8));

/** A finite double a >= 0 as m * 2**e with m an integer below 2**53. */
function decompose(a: number): [bigint, number] {
  view.setFloat64(0, a);
  const hi = view.getUint32(0);
  const lo = view.getUint32(4);
  const biased = (hi >>> 20) & 0x7ff;
  const frac = (BigInt(hi & 0xfffff) << 32n) | BigInt(lo);
  return biased === 0 ? [frac, -1074] : [frac | (1n << 52n), biased - 1075];
}

/** `a` (finite, >= 0) rounded half to even on its exact value to `d` decimals, as `f"{a:.{d}f}"` prints it. */
function exactFixed(a: number, d: number): string {
  const [m, e] = decompose(a);
  const scale = 10n ** BigInt(d);
  let n: bigint;
  if (e >= 0) {
    n = (m << BigInt(e)) * scale;
  } else {
    const num = m * scale;
    const sh = BigInt(-e);
    const q = num >> sh;
    const r = num - (q << sh);
    const half = 1n << (sh - 1n);
    n = r > half ? q + 1n : r < half ? q : q & 1n ? q + 1n : q;
  }
  let s = n.toString();
  if (d > 0) {
    s = s.padStart(d + 1, "0");
    s = `${s.slice(0, -d)}.${s.slice(-d)}`;
  }
  return s;
}

/**
 * `f"{x:.{d}f}"`. Python rounds half to even on the exact binary value (`0.25` prints `0.2`), prints the sign of
 * a negative zero and of a negative that rounds to zero (`-0.0`), spells nan and inf in lower case, and never
 * switches to exponent form. `toFixed` rounds ties up, drops the sign of `-0`, and switches to exponents from
 * 1e21. The fast path uses `toFixed` and drops to exact integer arithmetic whenever the value could be a tie.
 */
export function fmtFixed(x: number, d: number): string {
  if (x !== x) return "nan";
  if (x === Infinity) return "inf";
  if (x === -Infinity) return "-inf";
  const neg = x < 0 || Object.is(x, -0);
  const a = neg ? -x : x;
  let s: string;
  const scale = POW10[d];
  if (scale !== undefined && a * scale < 1e15) {
    const y = a * scale;
    const f = y - Math.floor(y);
    s = Math.abs(f - 0.5) > 1e-6 ? a.toFixed(d) : exactFixed(a, d);
  } else {
    s = exactFixed(a, d);
  }
  return neg ? `-${s}` : s;
}

export const fmt0 = (x: number): string => fmtFixed(x, 0);
export const fmt1 = (x: number): string => fmtFixed(x, 1);
export const fmt2 = (x: number): string => fmtFixed(x, 2);
export const fmt3 = (x: number): string => fmtFixed(x, 3);

/** `f"{n:02x}"` for an int. */
export function fmtHex2(n: number): string {
  // The width of 2 counts the sign: `format(-1, "02x")` is "-1".
  if (n < 0) return `-${Math.abs(n).toString(16)}`;
  return n.toString(16).padStart(2, "0");
}

/**
 * `repr(x)` of a float: the shortest digits that round-trip (JS and Python agree on the digits), but fixed notation
 * only for 1e-4 <= |x| < 1e16 and `1e-05` / `1e+16` style exponents otherwise, and `1.0` where JS prints `1`.
 */
export function pyRepr(x: number): string {
  if (x !== x) return "nan";
  if (x === Infinity) return "inf";
  if (x === -Infinity) return "-inf";
  if (x === 0) return Object.is(x, -0) ? "-0.0" : "0.0";
  const sign = x < 0 ? "-" : "";
  const [mant = "", expStr = "0"] = Math.abs(x).toExponential().split("e");
  const digits = mant.replace(".", "");
  const e = Number(expStr);
  if (e >= -4 && e < 16) {
    if (e >= 0) {
      const intLen = e + 1;
      if (digits.length <= intLen) return `${sign}${digits.padEnd(intLen, "0")}.0`;
      return `${sign}${digits.slice(0, intLen)}.${digits.slice(intLen)}`;
    }
    return `${sign}0.${"0".repeat(-e - 1)}${digits}`;
  }
  const m = digits.length > 1 ? `${digits[0]}.${digits.slice(1)}` : digits;
  return `${sign}${m}e${e < 0 ? "-" : "+"}${String(Math.abs(e)).padStart(2, "0")}`;
}

// ---------------------------------------------------------------------------------------------------------
// Rounding, integers, modulo

/** `round(x)` for a float: an int, ties to even (`round(2.5)` is 2, `Math.round` says 3). */
export function pyRound(x: number): number {
  if (x !== x) throw new PyError("ValueError", "cannot convert float NaN to integer");
  if (!Number.isFinite(x)) throw new PyError("OverflowError", "cannot convert float infinity to integer");
  if (Math.abs(x) >= 4503599627370496) return x;
  const f = Math.floor(x);
  const d = x - f;
  const r = d < 0.5 ? f : d > 0.5 ? f + 1 : f % 2 === 0 ? f : f + 1;
  return r === 0 ? 0 : r;
}

/** `round(x, n)` for a float: the exact value rounded half to even to `n` decimals, then the nearest double. */
export function roundTo(x: number, n: number): number {
  if (n < 0) throw new PyError("NotImplementedError", "round() to a negative number of digits is not ported");
  if (!Number.isFinite(x)) return x;
  return Number(fmtFixed(x, n));
}

/** `int(x)` for a float: truncation toward zero. */
export function pyInt(x: number): number {
  if (x !== x) throw new PyError("ValueError", "cannot convert float NaN to integer");
  if (!Number.isFinite(x)) throw new PyError("OverflowError", "cannot convert float infinity to integer");
  const t = Math.trunc(x);
  return t === 0 ? 0 : t;
}

/** `a % b` for floats: the result takes the sign of `b` (`-1 % 4` is 3, JS says -1). */
export function pyMod(a: number, b: number): number {
  if (b === 0) throw new PyError("ZeroDivisionError", "float modulo by zero");
  let m = a % b;
  if (m !== 0) {
    if (b < 0 !== m < 0) m += b;
  } else {
    m = copysign(0, b);
  }
  return m;
}

/** `a % b` for ints: as `pyMod` but never a negative zero. */
export function pyModInt(a: number, b: number): number {
  if (b === 0) throw new PyError("ZeroDivisionError", "integer modulo by zero");
  const m = pyMod(a, b);
  return m === 0 ? 0 : m;
}

export function copysign(a: number, b: number): number {
  const neg = b < 0 || Object.is(b, -0);
  return neg ? -Math.abs(a) : Math.abs(a);
}

// ---------------------------------------------------------------------------------------------------------
// Sums and extremes

/**
 * `sum(items)` as CPython 3.12 and later computes it: once a float is reached, Neumaier compensated summation.
 * `leadingInts` says how many of the first items are Python ints (they add exactly; the first float after them
 * is added plainly, with no compensation for that one step, as CPython does). Pass 0 when every item is a float.
 */
export function pySum(items: Iterable<number>, leadingInts = 0): number {
  const a = Array.isArray(items) ? (items as number[]) : [...items];
  let i = 0;
  let acc = 0;
  for (; i < leadingInts && i < a.length; i++) acc += a[i] as number;
  if (i >= a.length) return acc;
  acc += a[i] as number;
  i++;
  let c = 0;
  for (; i < a.length; i++) {
    const x = a[i] as number;
    const t = acc + x;
    if (Math.abs(acc) >= Math.abs(x)) c += acc - t + x;
    else c += x - t + acc;
    acc = t;
  }
  if (c !== 0 && Number.isFinite(c)) acc += c;
  return acc;
}

/** `max(a, b, ...)`: the first of equal maxima wins; a nan loses to what it is compared with (as in Python). */
export function pyMax(first: number, ...rest: number[]): number {
  let m = first;
  for (const x of rest) if (x > m) m = x;
  return m;
}

/** `min(a, b, ...)`: the first of equal minima wins. */
export function pyMin(first: number, ...rest: number[]): number {
  let m = first;
  for (const x of rest) if (x < m) m = x;
  return m;
}

/** The index `max(range(len(items)), key=...)` gives: the first index of the greatest key. */
export function argMax(keys: readonly number[]): number {
  if (keys.length === 0) throw new PyError("ValueError", "max() iterable argument is empty");
  let best = 0;
  for (let i = 1; i < keys.length; i++) if ((keys[i] as number) > (keys[best] as number)) best = i;
  return best;
}

// ---------------------------------------------------------------------------------------------------------
// Maths

const DEG_TO_RAD = Math.PI / 180;
const RAD_TO_DEG = 180 / Math.PI;

/** `math.radians(x)`: `x * (pi / 180)`. (`x * Math.PI / 180` rounds differently.) */
export const radians = (x: number): number => x * DEG_TO_RAD;
export const degrees = (x: number): number => x * RAD_TO_DEG;

const domainError = (): PyError => new PyError("ValueError", "math domain error");

export function pySqrt(x: number): number {
  if (x < 0) throw domainError();
  return Math.sqrt(x);
}

export function pyAcos(x: number): number {
  if (x > 1 || x < -1) throw domainError();
  return Math.acos(x);
}

export function pySin(x: number): number {
  if (x === Infinity || x === -Infinity) throw domainError();
  return Math.sin(x);
}

export function pyCos(x: number): number {
  if (x === Infinity || x === -Infinity) throw domainError();
  return Math.cos(x);
}

const isOddInteger = (y: number): boolean => Number.isInteger(y) && Math.abs(y) < 9007199254740992 && Math.abs(y % 2) === 1;

/**
 * `x ** y` for floats, following CPython's `float_pow`: its special cases (`1.0 ** nan` is 1, `(-1.0) ** inf` is 1, which
 * `Math.pow` gets differently), `ZeroDivisionError` for zero to a negative power, `OverflowError` where C's `pow` overflows,
 * and for a negative base with a fractional exponent, which is a complex number in Python, a `ValueError` here (loud on purpose).
 * Normal results come from the engine's `Math.pow` and can differ from the C library in the last bit.
 */
export function pyPow(x: number, y: number): number {
  if (y === 0) return 1;
  if (x !== x) return x;
  if (y !== y) return x === 1 ? 1 : y;
  if (y === Infinity || y === -Infinity) {
    const ax = Math.abs(x);
    if (ax === 1) return 1;
    return y > 0 === ax > 1 ? Infinity : 0;
  }
  if (x === Infinity || x === -Infinity) {
    const odd = isOddInteger(y);
    if (y > 0) return odd ? x : Math.abs(x);
    return odd ? copysign(0, x) : 0;
  }
  if (x === 0 && y < 0) throw new PyError("ZeroDivisionError", "0.0 cannot be raised to a negative power");
  let negate = false;
  let a = x;
  if (a < 0) {
    if (!Number.isInteger(y)) throw new PyError("ValueError", "complex result");
    negate = isOddInteger(y);
    a = -a;
  }
  if (a === 1) return negate ? -1 : 1;
  const r = Math.pow(a, y);
  if (r === Infinity) throw new PyError("OverflowError", "(34, 'Numerical result out of range')");
  return negate ? -r : r;
}

/** `a / b` for floats: Python raises `ZeroDivisionError` where JavaScript gives `Infinity` or `NaN`. */
export function pyDiv(a: number, b: number): number {
  if (b === 0) throw new PyError("ZeroDivisionError", "float division by zero");
  return a / b;
}

// CPython 3.12+ `math.hypot`: scaled, with the squares and their sum carried as exact double-doubles, and a final
// correction step. It is its own algorithm and not the C library's, so it can be reproduced exactly.

const SPLIT = 134217729; // 2**27 + 1

function dlMul(x: number, y: number): [number, number] {
  // Veltkamp-Dekker splitting; the same exact product and error that an fma gives.
  let t = x * SPLIT;
  const xh = t - (t - x);
  const xl = x - xh;
  t = y * SPLIT;
  const yh = t - (t - y);
  const yl = y - yh;
  const p = xh * yh;
  const q = xh * yl + xl * yh;
  const z = p + q;
  const zz = p - z + q + xl * yl;
  return [z, zz];
}

function dlFastSum(a: number, b: number): [number, number] {
  const x = a + b;
  return [x, a - x + b];
}

function frexpExp(a: number): number {
  // The e of a = m * 2**e with 0.5 <= m < 1, a finite and > 0.
  if (a < 2.2250738585072014e-308) return frexpExp(a * 2 ** 54) - 54;
  view.setFloat64(0, a);
  return ((view.getUint32(0) >>> 20) & 0x7ff) - 1022;
}

function vectorNorm(vec: number[], max: number): number {
  const n = vec.length;
  if (max === Infinity) return max;
  if (max === 0 || n <= 1) return max;
  const maxE = frexpExp(max);
  if (maxE < -1023) {
    const DBL_MIN = 2.2250738585072014e-308;
    return DBL_MIN * vectorNorm(vec.map((v) => v / DBL_MIN), max / DBL_MIN);
  }
  const scale = 2 ** -maxE;
  let csum = 1;
  let frac1 = 0;
  let frac2 = 0;
  for (const v of vec) {
    const x = v * scale;
    const [phi, plo] = dlMul(x, x);
    const [shi, slo] = dlFastSum(csum, phi);
    csum = shi;
    frac1 += plo;
    frac2 += slo;
  }
  let h = Math.sqrt(csum - 1 + (frac1 + frac2));
  const [phi, plo] = dlMul(-h, h);
  const [shi, slo] = dlFastSum(csum, phi);
  csum = shi;
  frac1 += plo;
  frac2 += slo;
  const x = csum - 1 + (frac1 + frac2);
  h += x / (2 * h);
  return h / scale;
}

/** `math.hypot(...values)`. */
export function pyHypot(...values: number[]): number {
  let max = 0;
  let foundNan = false;
  const vec = values.map((v) => {
    const a = Math.abs(v);
    if (a !== a) foundNan = true;
    if (a > max) max = a;
    return a;
  });
  if (max === Infinity) return max;
  if (foundNan) return NaN;
  return vectorNorm(vec, max);
}

// ---------------------------------------------------------------------------------------------------------
// Sequences

/** `items[i]` with Python indexing: negative counts from the end, out of range raises. */
export function at<T>(items: readonly T[], i: number): T {
  if (!Number.isInteger(i)) throw new PyError("TypeError", "list indices must be integers or slices, not float");
  const j = i < 0 ? i + items.length : i;
  if (j < 0 || j >= items.length) throw new PyError("IndexError", "list index out of range");
  return items[j] as T;
}

/** `items[start:stop:step]` with Python slice semantics (`None` is `undefined` or `null`). */
export function pySlice<T>(
  items: readonly T[],
  start?: number | null,
  stop?: number | null,
  step: number = 1,
): T[] {
  for (const v of [start, stop, step]) {
    if (v != null && !Number.isInteger(v) && Math.abs(v) !== Infinity) {
      throw new PyError("TypeError", "slice indices must be integers or None or have an __index__ method");
    }
  }
  if (step === 0) throw new PyError("ValueError", "slice step cannot be zero");
  const n = items.length;
  const adjust = (i: number, low: number, high: number): number => {
    if (i < 0) {
      const j = i + n;
      return j < low ? low : j;
    }
    return i > high ? high : i;
  };
  const out: T[] = [];
  if (step > 0) {
    const lo = start == null ? 0 : adjust(start, 0, n);
    const hi = stop == null ? n : adjust(stop, 0, n);
    for (let i = lo; i < hi; i += step) out.push(items[i] as T);
  } else {
    const lo = start == null ? n - 1 : adjust(start, -1, n - 1);
    const hi = stop == null ? -1 : adjust(stop, -1, n - 1);
    for (let i = lo; i > hi; i += step) out.push(items[i] as T);
  }
  return out;
}

/**
 * A value that is not a number sitting where the drawing does arithmetic on one (a string or a list in a `float` field of a
 * link or a model's request, or `None` where a number is required). Python keeps it and raises `TypeError` at the first
 * arithmetic or comparison, and not before: a field that is never used never complains. This reproduces that: it is stored
 * and passed around freely, and any use as a number raises. It keeps the truth value of what it replaced.
 */
export class BadValue {
  readonly original: unknown;
  constructor(original: unknown) {
    this.original = original;
  }
  private fail(): never {
    const t = this.original === null || this.original === undefined ? "NoneType" : Array.isArray(this.original) ? "list" : typeof this.original === "string" ? "str" : typeof this.original;
    throw new PyError("TypeError", `unsupported operand type(s): '${t}' is not a number`);
  }
  valueOf(): number {
    return this.fail();
  }
  [Symbol.toPrimitive](): never {
    return this.fail();
  }
}

/** Python's truth test: empty containers and strings are false, nan and every other number but zero are true. */
export function truthy(v: unknown): boolean {
  if (v instanceof BadValue) return truthy(v.original);
  if (v == null) return false;
  if (typeof v === "number") return v !== 0;
  if (typeof v === "string") return v.length > 0;
  if (typeof v === "boolean") return v;
  if (Array.isArray(v)) return v.length > 0;
  if (v instanceof Set || v instanceof Map) return v.size > 0;
  return true;
}

/** Python's ordering of numbers, strings and (lexicographically) tuples, for `sorted`. */
export function pyCompare(a: unknown, b: unknown): number {
  if (Array.isArray(a) && Array.isArray(b)) {
    const n = Math.min(a.length, b.length);
    for (let i = 0; i < n; i++) {
      const c = pyCompare(a[i], b[i]);
      if (c !== 0) return c;
    }
    return a.length - b.length;
  }
  if (typeof a === "string" && typeof b === "string") return compareCodePoints(a, b);
  return (a as number) < (b as number) ? -1 : (a as number) > (b as number) ? 1 : 0;
}

/** Python orders strings by code point; JS `<` orders by UTF-16 unit, which differs between astral characters and U+E000 to U+FFFF. */
export function compareCodePoints(a: string, b: string): number {
  const n = Math.min(a.length, b.length);
  for (let i = 0; i < n; i++) {
    let ca = a.charCodeAt(i);
    let cb = b.charCodeAt(i);
    if (ca === cb) continue;
    if (ca >= 0xd800 && cb >= 0xd800) {
      ca = ca >= 0xe000 ? ca - 0x800 : ca + 0x2000;
      cb = cb >= 0xe000 ? cb - 0x800 : cb + 0x2000;
    }
    return ca < cb ? -1 : 1;
  }
  return a.length < b.length ? -1 : a.length > b.length ? 1 : 0;
}

/** `sorted(items, key=key)`: stable, ascending, by Python's ordering (never JS's default string order). */
export function sorted<T>(items: Iterable<T>, key: (item: T) => unknown = (x) => x): T[] {
  return [...items]
    .map((item, i) => ({ item, k: key(item), i }))
    .sort((p, q) => pyCompare(p.k, q.k) || p.i - q.i)
    .map((p) => p.item);
}

/** `a == b` for nested arrays of numbers and strings (Python compares by value, JS by identity). */
export function deepEqual(a: unknown, b: unknown): boolean {
  if (Array.isArray(a) && Array.isArray(b)) {
    return a.length === b.length && a.every((x, i) => deepEqual(x, b[i]));
  }
  return a === b;
}

// ---------------------------------------------------------------------------------------------------------
// Strings

/** `s.replace(old, new)`: every occurrence, and `new` is literal text (JS gives `$&` and friends a meaning). */
export function pyReplace(s: string, old: string, replacement: string): string {
  // `"abc".replace("", "-")` is "-a-b-c-": the replacement goes between every code point and at both ends.
  if (old === "") return replacement + [...s].map((c) => c + replacement).join("");
  return s.split(old).join(replacement);
}

/** `float(s)` for the plain decimal forms the code feeds it. */
export function pyFloat(s: string): number {
  const t = s.trim();
  if (!/^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$/.test(t)) {
    throw new PyError("ValueError", `could not convert string to float: ${JSON.stringify(s).replace(/"/g, "'")}`);
  }
  return Number(t);
}

/** The value of a decimal digit in any script (Python's `int()` accepts them all): the offset within its run of ten. */
function decimalDigitValue(ch: string): number {
  const cp = ch.codePointAt(0) as number;
  if (cp < 128) return cp - 48;
  let start = cp;
  while (start > 0 && /^\p{Nd}$/u.test(String.fromCodePoint(start - 1)) && cp - start < 60) start--;
  return (cp - start) % 10;
}

const PY_SPACE = /^[\t\n\v\f\r\x1c-\x20\x85\xa0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+|[\t\n\v\f\r\x1c-\x20\x85\xa0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+$/g;

/**
 * `int(s, 16)`: surrounding whitespace, an optional sign, an optional `0x`, single underscores between digits, and decimal
 * digits of any script as well as `a` to `f`. Exact for up to 13 digits (the colour code reads two); more raise here.
 */
export function pyHex(s: string): number {
  const bad = (): PyError => new PyError("ValueError", `invalid literal for int() with base 16: ${pyStrRepr(s)}`);
  let t = s.replace(PY_SPACE, "");
  let sign = 1;
  if (t.startsWith("+") || t.startsWith("-")) {
    if (t[0] === "-") sign = -1;
    t = t.slice(1);
  }
  if (/^0[xX]/.test(t)) {
    t = t.slice(2);
    if (t.startsWith("_")) t = t.slice(1);
  }
  if (t === "" || t.startsWith("_") || t.endsWith("_") || t.includes("__")) throw bad();
  let value = 0;
  let digits = 0;
  for (const ch of t) {
    if (ch === "_") continue;
    let d: number;
    if (/^[0-9a-fA-F]$/.test(ch)) d = parseInt(ch, 16);
    else if (/^\p{Nd}$/u.test(ch)) d = decimalDigitValue(ch);
    else throw bad();
    value = value * 16 + d;
    if (value !== 0 && ++digits > 13) throw new PyError("OverflowError", "int() with more than 13 significant hex digits is not ported");
  }
  return sign * value === 0 ? 0 : sign * value;
}

/** `repr(s)` for a str: single quotes unless the text has a single and no double quote; backslash and control escapes. */
export function pyStrRepr(s: string): string {
  const quote = s.includes("'") && !s.includes('"') ? '"' : "'";
  let out = quote;
  for (const ch of s) {
    const c = ch.codePointAt(0) as number;
    if (ch === quote || ch === "\\") out += `\\${ch}`;
    else if (ch === "\n") out += "\\n";
    else if (ch === "\r") out += "\\r";
    else if (ch === "\t") out += "\\t";
    else if (c < 0x20 || c === 0x7f) out += `\\x${c.toString(16).padStart(2, "0")}`;
    else out += ch;
  }
  return out + quote;
}
