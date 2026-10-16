// Correctly rounded `x ** y`, `sin` and `cos` for the one place core-limbs cannot live with the engine's: the fist's rounded
// boxes (`_rounded_box`), whose points are `centre + half * copysign(|cos t| ** (2 / e), cos t)` and sit next to a cancellation
// (`-0.3 + 0.4 * 0.75`), which turns a last-bit difference of the power or of the cosine into a difference of tens of ulps in
// the point. CPython hands `**`, `sin` and `cos` to the C library, which on the platform the recordings come from rounds them
// correctly for these inputs; V8's `Math.pow`, `Math.sin` and `Math.cos` are within an ulp or two. These compute the value in
// 192-bit fixed point (BigInt) and round it to nearest even, so they agree with a correctly rounding C library everywhere and
// differ from V8's where that one is off by a bit.
//
// Only the inputs the fist uses are handled (for the power a positive finite base, a positive finite exponent, a normal result;
// for sin and cos a finite argument below 100 in size); anything else goes to the kernel.

import { pyCos, pyPow, pySin } from "./pynum.ts";

const P = 192n;
const ONE = 1n << P;

const view = new DataView(new ArrayBuffer(8));

/** A finite double a > 0 as m * 2**e with m an integer below 2**53. */
function decompose(a: number): [bigint, number] {
  view.setFloat64(0, a);
  const hi = view.getUint32(0);
  const lo = view.getUint32(4);
  const biased = (hi >>> 20) & 0x7ff;
  const frac = (BigInt(hi & 0xfffff) << 32n) | BigInt(lo);
  return biased === 0 ? [frac, -1074] : [frac | (1n << 52n), biased - 1075];
}

const bitLength = (n: bigint): number => n.toString(2).length;

/** `2 * atanh(z)` for a fixed-point `z` with |z| below 1/3 (the series, 70 terms: far below the last of 192 bits). */
function twiceAtanh(z: bigint): bigint {
  const z2 = (z * z) >> P;
  let term = z;
  let sum = 0n;
  for (let n = 1n; n < 140n; n += 2n) {
    sum += term / n;
    term = (term * z2) >> P;
  }
  return 2n * sum;
}

const LN2 = twiceAtanh(ONE / 3n);

/** `ln(x)` in fixed point for a double x > 0. */
function lnFixed(x: number): bigint {
  const [m, e] = decompose(x);
  const len = bitLength(m);
  // x = 2**k * f with f in [0.75, 1.5): the series converges fast there. First k = len + e puts f in [0.5, 1).
  let k = len + e;
  let f = m << (P - BigInt(len));
  if (f * 4n < 3n * ONE) {
    k -= 1;
    f <<= 1n;
  }
  const z = ((f - ONE) << P) / (f + ONE);
  return twiceAtanh(z) + BigInt(k) * LN2;
}

/** `exp(t)` for a fixed-point `t`, as the double nearest to it. */
function expRound(t: bigint): number {
  // t = k * ln2 + r with |r| <= ln2 / 2.
  const half = LN2 / 2n;
  let k = t / LN2;
  let r = t - k * LN2;
  if (r > half) {
    k += 1n;
    r -= LN2;
  } else if (r < -half) {
    k -= 1n;
    r += LN2;
  }
  let term = ONE;
  let sum = ONE;
  for (let n = 1n; n < 70n; n++) {
    term = ((term * r) >> P) / n;
    sum += term;
  }
  // sum is exp(r) in [0.7, 1.42] times 2**P, and the result is that times 2**k.
  return toDouble(sum, Number(k) - Number(P));
}

/** The double nearest `v * 2**exp2` (half to even); `v` any sign. */
function toDouble(v: bigint, exp2: number): number {
  if (v === 0n) return 0;
  const neg = v < 0n;
  const a = neg ? -v : v;
  const s = bitLength(a) - 53;
  let mant = a;
  let shift = exp2;
  if (s > 0) {
    mant = a >> BigInt(s);
    const rem = a - (mant << BigInt(s));
    const halfRem = 1n << BigInt(s - 1);
    if (rem > halfRem || (rem === halfRem && (mant & 1n) === 1n)) mant += 1n;
    shift += s;
  }
  const out = ldexp(Number(mant), shift);
  return neg ? -out : out;
}

function ldexp(x: number, n: number): number {
  let out = x;
  let rest = n;
  while (rest > 1000) {
    out *= 2 ** 1000;
    rest -= 1000;
  }
  while (rest < -1000) {
    out *= 2 ** -1000;
    rest += 1000;
  }
  return out * 2 ** rest;
}

/** `x ** y` for a positive finite `x` and a positive finite `y`, correctly rounded; other inputs go to `pyPow`. */
export function powRounded(x: number, y: number): number {
  if (!(x > 0 && x < Infinity && y > 0 && y < Infinity) || x === 1) return pyPow(x, y);
  const [my, ey] = decompose(y);
  const lx = lnFixed(x);
  const prod = lx * my;
  const t = ey >= 0 ? prod << BigInt(ey) : prod >> BigInt(-ey);
  const result = expRound(t);
  // Only normal results are computed here; a subnormal or overflowing one is the kernel's.
  if (!(result >= 2.2250738585072014e-308 && result < Infinity)) return pyPow(x, y);
  return result;
}

/** The argument as fixed point: `t` is exact in a double, so this is exact for any `|t|` the shift leaves room for. */
function fixedOf(t: number): bigint {
  const neg = t < 0;
  const [m, e] = decompose(neg ? -t : t);
  const f = e + Number(P) >= 0 ? m << BigInt(e + Number(P)) : m >> BigInt(-(e + Number(P)));
  return neg ? -f : f;
}

/** `sin(t)` and `cos(t)` by their Taylor series on `|t|`, in fixed point. */
function sinCosFixed(t: number): [bigint, bigint] {
  const x = fixedOf(Math.abs(t));
  const x2 = (x * x) >> P;
  // sin: x - x^3/3! + ...; cos: 1 - x^2/2! + ...
  let term = x;
  let sin = 0n;
  for (let n = 1n; term !== 0n; n += 2n) {
    sin += ((n - 1n) / 2n) % 2n === 0n ? term : -term;
    term = (((term * x2) >> P) / (n + 1n)) / (n + 2n);
  }
  term = ONE;
  let cos = 0n;
  for (let n = 0n; term !== 0n; n += 2n) {
    cos += (n / 2n) % 2n === 0n ? term : -term;
    term = (((term * x2) >> P) / (n + 1n)) / (n + 2n);
  }
  return [t < 0 ? -sin : sin, cos];
}

/** `math.sin(t)`, correctly rounded for a finite `t` of size below 100; anything else is the kernel's. */
export function sinRounded(t: number): number {
  if (!(Math.abs(t) < 100)) return pySin(t);
  if (t === 0) return t;
  return toDouble(sinCosFixed(t)[0], -Number(P));
}

/** `math.cos(t)`, correctly rounded for a finite `t` of size below 100; anything else is the kernel's. */
export function cosRounded(t: number): number {
  if (!(Math.abs(t) < 100)) return pyCos(t);
  return toDouble(sinCosFixed(t)[1], -Number(P));
}
