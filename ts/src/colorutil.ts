// Color helpers for the flat cel-shading look: every shape gets a base color and a single darker "shadow" tone,
// derived rather than hand-picked, so palettes stay internally consistent across characters.
//
// Port of colorutil.py and of the two `colorsys` functions it uses (CPython 3.13, same in 3.12). The
// evaluation order of every expression is kept as it is in Python, since a different order rounds differently.

import { PyError, fmtHex2, pyHex, pyMax, pyMin, pyMod, pyRound, pyInt, pyModInt } from "./pynum.ts";

export type Rgb = readonly [number, number, number];
export type Hsv = readonly [number, number, number];

/** `colorsys.rgb_to_hsv`. */
export function rgbToHsv(r: number, g: number, b: number): Hsv {
  const maxc = pyMax(r, g, b);
  const minc = pyMin(r, g, b);
  const rangec = maxc - minc;
  const v = maxc;
  if (minc === maxc) return [0, 0, v];
  const s = rangec / maxc;
  const rc = (maxc - r) / rangec;
  const gc = (maxc - g) / rangec;
  const bc = (maxc - b) / rangec;
  let h: number;
  if (r === maxc) h = bc - gc;
  else if (g === maxc) h = 2 + rc - bc;
  else h = 4 + gc - rc;
  h = pyMod(h / 6, 1);
  return [h, s, v];
}

/** `colorsys.hsv_to_rgb`. */
export function hsvToRgb(h: number, s: number, v: number): Rgb {
  if (s === 0) return [v, v, v];
  let i = pyInt(h * 6);
  const f = h * 6 - i;
  const p = v * (1 - s);
  const q = v * (1 - s * f);
  const t = v * (1 - s * (1 - f));
  i = pyModInt(i, 6);
  switch (i) {
    case 0:
      return [v, t, p];
    case 1:
      return [q, v, p];
    case 2:
      return [p, v, t];
    case 3:
      return [p, q, v];
    case 4:
      return [t, p, v];
    default:
      return [v, p, q];
  }
}

/** `hex_color.lstrip("#")` and three two-digit slices; a short or malformed string raises as in Python. */
export function hexToRgb01(hexColor: string): Rgb {
  if (typeof hexColor !== "string") {
    throw new PyError("AttributeError", `'${hexColor === null || hexColor === undefined ? "NoneType" : Array.isArray(hexColor) ? "list" : typeof hexColor === "number" ? "float" : typeof hexColor}' object has no attribute 'lstrip'`);
  }
  const h = hexColor.replace(/^#+/, "");
  return [pyHex(h.slice(0, 2)) / 255, pyHex(h.slice(2, 4)) / 255, pyHex(h.slice(4, 6)) / 255];
}

export function rgb01ToHex(rgb: Rgb): string {
  const [r, g, b] = rgb.map((c) => pyMax(0, pyMin(255, pyRound(c * 255)))) as [number, number, number];
  return `#${fmtHex2(r)}${fmtHex2(g)}${fmtHex2(b)}`;
}

/** Darker, slightly more saturated variant for shadow shapes. */
export function shade(hexColor: string, valueFactor = 0.8, saturationBoost = 1.08): string {
  const [r, g, b] = hexToRgb01(hexColor);
  const hsv = rgbToHsv(r, g, b);
  const s = pyMin(1, hsv[1] * saturationBoost);
  const v = pyMax(0, hsv[2] * valueFactor);
  return rgb01ToHex(hsvToRgb(hsv[0], s, v));
}

/** Lighter variant, `amount` of the way to white. For the soft finish's highlights and glows. */
export function tint(hexColor: string, amount = 0.5): string {
  const [r, g, b] = hexToRgb01(hexColor);
  return rgb01ToHex([r + (1 - r) * amount, g + (1 - g) * amount, b + (1 - b) * amount]);
}

/**
 * Lighter by `rise` of value, keeping the saturation, hue nudged a little warm when the colour has one. Where
 * value would pass white the saturation gives way instead, by part of the overshoot.
 */
export function litTone(hexColor: string, rise: number): string {
  const [h0, s0, v] = rgbToHsv(...hexToRgb01(hexColor));
  let h = h0;
  let s = s0;
  let v2 = v + rise;
  if (v2 > 1.0) {
    s = pyMax(0, s - (v2 - 1.0) * 0.6);
    v2 = 1.0;
  }
  // A warm nudge means nothing on near-grey or near-black hair, and on yellow-green it is a nudge toward green.
  if (s >= 0.35 && !(55.0 / 360.0 <= h && h < 90.0 / 360.0)) {
    h = pyMod(h + 4.0 / 360.0, 1);
  }
  return rgb01ToHex(hsvToRgb(h, s, v2));
}

/** How far a strong highlight rises in value: more on dark colours, little on light ones. */
export function highlightRise(hexColor: string): number {
  const v = rgbToHsv(...hexToRgb01(hexColor))[2];
  return pyMin(0.28, pyMax(0.06, 0.3 * (1.0 - v) + 0.08));
}

/**
 * A step darker than the colour, gentler than `shade` so a shadow clump is a tone and not a stripe, quieter still
 * on pale or grey colours, and with yellow pulled a little toward orange so its shadow is warm and not olive.
 */
export function softShadowTone(hexColor: string, gain = 1.0): string {
  const [, s0, v0] = rgbToHsv(...hexToRgb01(hexColor));
  let factor = s0 < 0.35 ? 0.92 : 0.87 - 0.05 * v0;
  factor = pyMax(0.3, 1.0 - (1.0 - factor) * gain);
  const [h0, s, v] = rgbToHsv(...hexToRgb01(shade(hexColor, factor, 1.3)));
  let h = h0;
  if (30.0 / 360.0 < h && h < 70.0 / 360.0) {
    h -= 7.0 / 360.0;
  }
  return rgb01ToHex(hsvToRgb(h, s, v));
}
