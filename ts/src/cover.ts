// A book cover: flat backdrop, mist banks, one character, title. A transcription of `cover.py` (the frozen Python), byte for
// byte the same SVG for the same parameters.
//
// The character layers draw a figure on nothing. This draws the page around one: a dark backdrop, banks of mist as flat
// shapes, the figure, and the title over the top. Every shape is authored geometry, no gradients and no blur anywhere: a
// mist bank is a hard-edged silhouette in one flat tone, and depth comes from stacking several of them in a tone ladder.
//
// Simple is the design, not a stage on the way to something denser. A ridge and two clusters of ruined towers were built on
// top of this and then dropped, on the owner's call of 2026-08-08: do not try to beat the AI generated cover on its own
// ground. What is left is a large centred figure standing in mist under a stacked title, and nothing else on the page.
//
// Port notes. `CoverParams` is a plain object with the same field names and defaults as the dataclass, built by
// `coverParams` (the `CoverParams(...)` call) and changed with `replace` from `model.ts` (`dataclasses.replace`).
// `_jitter` goes through `pySin`, since `Math.sin` and `math.sin` may differ in the last bit and that bit reaches the
// mist's width. Every number reaches the text through `fmt0` to `fmt4`.

import { existsSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { metadataBlock } from "./attribution.ts";
import { skeletonFor } from "./body.ts";
import { OUTLINE } from "./character.ts";
import { expressionAppliedTo, replace } from "./model.ts";
import type { CharacterParams } from "./params.ts";
import { EXPRESSIONS, PRESETS } from "./presets.ts";
import { PyError, fmt0, fmt1, fmtFixed, pyFloat, pySin, pyStrRepr } from "./pynum.ts";
import { PyInt } from "./pyjson.ts";
import { loadsText } from "./pyjsonload.ts";
import { renderCharacter } from "./render.ts";
import type { Skeleton } from "./skeleton.ts";

/**
 * The flat tones the page is built from, back to front. A ladder rather than a pair, because that is what replaces the
 * gradient a painted cover would use: each mist bank sits one rung lighter than the one behind it.
 */
export interface CoverPalette {
  readonly sky: string;
  readonly sky_low: string;
  /** Dark to light, back to front. Five rungs, because the step between neighbours is what has to stay small. */
  readonly mist: readonly string[];
  readonly ink: string;
  readonly title: string;
}

export const coverPalette = (overrides: Partial<CoverPalette> = {}): CoverPalette =>
  Object.freeze({
    sky: "#141c21",
    sky_low: "#1e2b30",
    mist: ["#2b3d41", "#384b4d", "#47595a", "#586a69", "#6d7d7a"],
    ink: OUTLINE,
    title: "#ffffff",
    ...overrides,
  });

/**
 * One cover. Everything a book needs to differ on lives here. `title` is a list of lines rather than one string because
 * where a title breaks is a design decision about that specific title.
 */
export interface CoverParams {
  readonly title: readonly string[];
  /** Empty by default: a lone line under the figure reads as a byline, whoever it names. */
  readonly subtitle: string;
  /** The byline at the foot of the page. */
  readonly author: string;
  readonly preset: string;
  /** An explicit character, overriding `preset`. */
  readonly character: CharacterParams | null;
  /** A named mood from `EXPRESSIONS`, laid over whichever character the two fields above resolve to. */
  readonly expression: string | null;
  readonly width: number;
  readonly height: number;
  readonly palette: CoverPalette;
  /** Family stacks, not files: the renderer substitutes whatever the system has. */
  readonly title_font: string;
  readonly subtitle_font: string;
  /** How low each mist bump is against its width: the number that separates mist from foam. */
  readonly mist_flatness: number;
  /** Where the figure sits, as fractions of the page. */
  readonly figure_height: number;
  readonly figure_feet_y: number;
}

export const coverParams = (overrides: Partial<CoverParams> = {}): CoverParams =>
  Object.freeze({
    title: ["THE HERO", "OF THE MIST", "TRAGEDY"],
    subtitle: "",
    author: "rhedak",
    preset: "satoshi",
    character: null,
    expression: "hollow",
    width: 1000.0,
    height: 1500.0,
    palette: coverPalette(),
    title_font: "Georgia, 'Times New Roman', serif",
    subtitle_font: "Helvetica, Arial, sans-serif",
    mist_flatness: 0.3,
    figure_height: 0.6,
    figure_feet_y: 0.885,
    ...overrides,
  });

/** A repeatable 0 to 1 from an index. Not an RNG: every render here is byte-identical run to run. */
function jitter(i: number): number {
  const x = pySin(i * 12.9898) * 43758.5453;
  return x - Math.floor(x);
}

/**
 * One bank of mist: low wide bumps along the top, flat along the bottom. The bumps are elliptical and much wider than they
 * are tall (`flatness` is that ratio), and sit on one baseline. It runs off both edges of a `width`-wide page on purpose.
 * Public so a page other than the cover can stand a figure in the same mist.
 */
export function mistBand(width: number, y: number, depth: number, color: string, seed: number, scale: number, flatness = 0.3): string {
  const over = width * 0.1;
  let x = -over;
  const d = [`M ${fmt1(-over)} ${fmt1(y + depth)}`, `L ${fmt1(-over)} ${fmt1(y)}`];
  let i = seed;
  while (x < width + over) {
    const rx = width * scale * (0.5 + jitter(i) * 1.1);
    const ry = rx * flatness;
    const x2 = x + rx * 2;
    // Sweep 1 going right bulges the arc upward, which is the whole shape.
    d.push(`A ${fmt1(rx)} ${fmt1(ry)} 0 0 1 ${fmt1(x2)} ${fmt1(y)}`);
    x = x2;
    i += 1;
  }
  d.push(`L ${fmt1(x)} ${fmt1(y + depth)}`);
  d.push("Z");
  return `<path d="${d.join(" ")}" fill="${color}" />`;
}

/** `mistBand` at the cover's own width and flatness. */
const coverMist = (p: CoverParams, y: number, depth: number, color: string, seed: number, scale: number): string =>
  mistBand(p.width, y, depth, color, seed, scale, p.mist_flatness);

/** The sky, in two flat steps rather than a wash. */
function backdrop(p: CoverParams): string {
  const pal = p.palette;
  const horizon = p.height * 0.52;
  return (
    `<rect width="${fmt0(p.width)}" height="${fmt0(p.height)}" fill="${pal.sky}" />\n` +
    `  <rect y="${fmt1(horizon)}" width="${fmt0(p.width)}" ` +
    `height="${fmt1(p.height - horizon)}" fill="${pal.sky_low}" />`
  );
}

/** Python's `float(x)` on a value `json.loads` gave back. */
function floatOf(v: unknown): number {
  if (typeof v === "number") return v;
  if (v instanceof PyInt) return Number(v.value);
  if (typeof v === "boolean") return v ? 1 : 0;
  if (typeof v === "string") return pyFloat(v);
  throw new PyError("TypeError", `float() argument must be a string or a real number, not '${v === null ? "NoneType" : typeof v}'`);
}

/** The repository root, where `local/` lives when `ACC_LOCAL_DIR` does not move it. */
const REPO_ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");

/**
 * The preset, with a face age from an untracked local file when one names it. Every shipped preset is twenty-one or older.
 * A cover that was published with another face keeps it by listing `{"<preset>": <face_age>}` in `local/cover_faces.json`
 * (`ACC_LOCAL_DIR` moves the folder), which is not in the repository. Without the file a cover draws the preset as shipped.
 */
function presetForCover(name: string): CharacterParams {
  const character = Object.hasOwn(PRESETS, name) ? PRESETS[name]! : undefined;
  if (character === undefined) throw new PyError("KeyError", pyStrRepr(name));
  const path = join(process.env["ACC_LOCAL_DIR"] || join(REPO_ROOT, "local"), "cover_faces.json");
  if (existsSync(path) && statSync(path).isFile()) {
    const ages = loadsText(readFileSync(path, "utf8"));
    if (ages instanceof Map && ages.has(name)) return replace(character, { face_age: floatOf(ages.get(name)) });
  }
  return character;
}

export interface Placement {
  readonly sk: Skeleton;
  readonly character: CharacterParams;
  readonly k: number;
  readonly x: number;
  readonly y: number;
}

/**
 * Where the figure lands on the page: its skeleton, its scale, its offset. Split out from drawing it because the mist in
 * front has to be positioned off the body, not off the page: `figure_feet_y` is where the soles land, and `sk.foot_y` is
 * 485 on a 500-tall canvas.
 */
export function placement(p: CoverParams): Placement {
  let character = p.character !== null ? p.character : presetForCover(p.preset);
  if (p.expression) {
    const e = Object.hasOwn(EXPRESSIONS, p.expression) ? EXPRESSIONS[p.expression] : undefined;
    if (e === undefined) throw new PyError("KeyError", pyStrRepr(p.expression));
    character = expressionAppliedTo(e, character);
  }
  const sk = skeletonFor(character);
  const k = (p.height * p.figure_height) / sk.canvas_h;
  const x = p.width / 2 - (sk.canvas_w * k) / 2;
  const y = p.height * p.figure_feet_y - sk.foot_y * k;
  return { sk, character, k, x, y };
}

/**
 * The character, scaled and placed. Rendered through `renderCharacter` exactly as anywhere else, on transparency. The
 * document it returns is unwrapped and re-wrapped in a `<g>`: its own `<svg>` element carries a width, a height and a
 * viewBox that would otherwise fight the page's.
 */
export function figure(character: CharacterParams, sk: Skeleton, k: number, x: number, y: number): string {
  const doc = renderCharacter(character, sk);
  const body = doc.replace(/^<svg[^>]*>\s*/, "").replace(/<\/svg>\s*$/, "").trim();
  return `<g transform="translate(${fmt1(x)} ${fmt1(y)}) scale(${fmtFixed(k, 4)})">\n  ${body}\n  </g>`;
}

/**
 * One line, drawn twice: a heavy stroke underneath and the fill over it. `paint-order="stroke"` is not used because
 * cairosvg ignores it silently, so the stroke would land on top of the fill.
 */
function text(p: CoverParams, line: string, y: number, size: number, font: string, spacing: number): string {
  const common =
    `x="${fmt1(p.width / 2)}" y="${fmt1(y)}" text-anchor="middle" font-family="${font}" ` +
    `font-size="${fmt1(size)}" font-weight="bold" letter-spacing="${fmt1(spacing)}"`;
  return (
    `<text ${common} fill="none" stroke="${p.palette.ink}" ` +
    `stroke-width="${fmt1(size * 0.155)}" stroke-linejoin="round">${line}</text>\n` +
    `  <text ${common} fill="${p.palette.title}">${line}</text>`
  );
}

/**
 * Draw one cover and return the whole SVG document as a string. Deterministic, like `renderCharacter`: same params, same
 * bytes. `metadata` embeds an SVG `<metadata>` block with a link that reproduces the featured character (as `placement`
 * resolves it, expression and all). Off by default so the committed cover in `ref-out/` does not churn.
 */
export function renderCover(params?: CoverParams | null, metadata = false): string {
  const p = params ?? coverParams();
  const pal = p.palette;
  const H = p.height;

  // Back to front. Three banks behind the figure and two in front of his feet, which is what puts him in the mist rather
  // than on top of a picture of it. The two in front are placed off the figure rather than off the page.
  const { sk, character, k, x, y } = placement(p);
  const sole = y + sk.foot_y * k;
  const footH = (sk.foot_y - sk.ankle_y) * k;

  // Feet just covered, and no more (the owner's call): the front banks are sized from the boot rather than positioned by
  // eye, since a bank's waterline is not its baseline.
  const near = footH / (p.width * 1.6 * p.mist_flatness);

  const behind: readonly (readonly [number, number, number])[] = [
    [0.455, 0.055, 3],
    [0.56, 0.07, 17],
    [0.655, 0.085, 41],
  ];
  const layers: string[] = [backdrop(p)];
  behind.forEach(([top, scale, seed], i) => {
    layers.push(coverMist(p, H * top, H - H * top, pal.mist[i]!, seed, scale));
  });
  layers.push(figure(character, sk, k, x, y));
  // The seed is chosen so one bump does not sit across a boot, and has to be re-picked whenever `figure_height` or the body
  // moves the feet.
  layers.push(coverMist(p, sole, H - sole, pal.mist[3]!, 111, near));
  layers.push(coverMist(p, sole + footH * 0.7, H, pal.mist[4]!, 83, near * 1.25));

  const size = H * 0.072;
  const top = H * 0.115;
  p.title.forEach((line, i) => {
    layers.push(text(p, line, top + i * size * 1.16, size, p.title_font, size * 0.02));
  });
  // A subtitle belongs under the title, not at the foot of the page, where it would read as a byline.
  if (p.subtitle) {
    layers.push(text(p, p.subtitle, top + p.title.length * size * 1.16, H * 0.034, p.subtitle_font, H * 0.008));
  }
  if (p.author) {
    layers.push(text(p, p.author, H * 0.945, H * 0.028, p.subtitle_font, H * 0.006));
  }

  const body = layers.filter((layer) => layer).join("\n  ");
  const md = metadata ? `  ${metadataBlock(character)}\n` : "";
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" width="${fmt0(p.width)}" height="${fmt0(H)}" ` +
    `viewBox="0 0 ${fmt0(p.width)} ${fmt0(H)}">\n` +
    `${md}` +
    `  ${body}\n` +
    `</svg>\n`
  );
}
