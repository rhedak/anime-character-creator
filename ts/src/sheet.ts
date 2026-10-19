// The cast on one page: a labelled grid of characters. A transcription of `sheet.py` (the frozen Python), byte for byte the
// same SVG for the same parameters.
//
// A sheet is how a cast gets judged: whether twelve people look like they come from one world is a question about the set,
// and a tile about a sixth of the page wide is the size a character is actually looked at. Construction follows the cover:
// authored geometry, flat tones, no gradients, and the figures come through `renderCharacter` unchanged.
//
// Two checked-in sheets, one for each reference roster: `ROSTERS["cast"]` (all fourteen, `ref-out/sheet.svg`) and
// `ROSTERS["satoshi"]` (Satoshi's persona rather than Satoko's, `ref-out/sheet_satoshi.svg`).
//
// Port notes. `SheetParams` is a plain object with the dataclass's field names and defaults, built by `sheetParams`.
// `sheetMetadataBlock` (`attribution.sheet_metadata_block`) lives here, as `attribution.ts` says it should.

import { escape, metadataHeader, TOOL_URL } from "./attribution.ts";
import { skeletonFor } from "./body.ts";
import { OUTLINE } from "./character.ts";
import { replace } from "./model.ts";
import { DISPLAY_NAMES, PRESETS, ROSTERS } from "./presets.ts";
import { PyError, fmt0, fmt1, fmtFixed, pyModInt, pyStrRepr } from "./pynum.ts";
import { renderCharacter } from "./render.ts";
import { characterUrl } from "./urlstate.ts";

export const CHARACTER_DESCRIPTIONS: Readonly<Record<string, string>> = {
  satoko: "Innkeeper's girl, local expedition guide",
  satoshi: "Innkeeper's boy, local expedition guide",
  kyoko: "Former assistant researcher to Natsume",
  tomohiro: "Former assistant researcher to Natsume",
  chiyo: "Innkeeper of Kiriguchi",
  daizen: "Merchant of the Kurogane house",
  elara: "Woden Soldier, Captain of the Expedition's soldiers",
  haruto: "Okiri Lord who got to keep his title after the Woden Annexation",
  keiko: "Former Okiri head researcher, now Woden assistant researcher",
  krista: "Woden Crystal specialist and Woden head researcher, rank Magus-Sergeant",
  reika: "High Priestess and first Kiri-no-Miko",
  reinhard: "Woden Oberst-Researcher, Leader of the Expedition and Investigator",
  tenno: "Former King of Okiri, now a porter to the Woden",
  viktor: "Lieutenant of the Woden's Ravens, Reinhard's second in command",
};

/**
 * Dark ground, light cards, white labels. Taken from the reference sheets: the figures carry a `#0d0d0d` outline, so they
 * need a light card under them to hold their silhouette, and a dark surround stops twelve light cards merging.
 */
export interface SheetPalette {
  readonly ground: string;
  readonly card: string;
  readonly label: string;
  readonly ink: string;
}

export const sheetPalette = (overrides: Partial<SheetPalette> = {}): SheetPalette =>
  Object.freeze({ ground: "#161619", card: "#f2f2f0", label: "#ffffff", ink: OUTLINE, ...overrides });

/** One sheet. A roster, a grid, and how big a figure sits in its tile. */
export interface SheetParams {
  readonly roster: string;
  /** An explicit list of preset names, overriding `roster`. */
  readonly members: readonly string[] | null;
  /** Four across, which is what both reference sheets use. The number of rows follows from the roster. */
  readonly columns: number;
  readonly tile_w: number;
  readonly tile_h: number;
  readonly gap: number;
  readonly margin: number;
  /** Room above each card for its name. */
  readonly label_h: number;
  readonly label_size: number;
  readonly description_size: number;
  readonly label_font: string;
  /** How much of a tile's height the figure fills, and where its soles land, as fractions of the tile. */
  readonly figure_height: number;
  readonly figure_feet_y: number;
  readonly palette: SheetPalette;
}

export const sheetParams = (overrides: Partial<SheetParams> = {}): SheetParams =>
  Object.freeze({
    roster: "cast",
    members: null,
    columns: 4,
    tile_w: 300.0,
    tile_h: 400.0,
    gap: 16.0,
    margin: 20.0,
    label_h: 60.0,
    label_size: 21.0,
    description_size: 13.0,
    label_font: "Helvetica, Arial, sans-serif",
    figure_height: 0.86,
    figure_feet_y: 0.94,
    palette: sheetPalette(),
    ...overrides,
  });

/** Python's `[...]` repr of a list of strings, for the error text. */
const listRepr = (items: readonly string[]): string => `[${items.map(pyStrRepr).join(", ")}]`;

/**
 * Who is on this sheet, and a hard error if any of them is not a character. A roster naming a preset that does not exist
 * would otherwise just be one tile shorter, which looks like a layout choice rather than a missing character.
 */
export function membersOf(p: SheetParams): readonly string[] {
  let names: readonly string[];
  if (p.members !== null) names = p.members;
  else if (Object.hasOwn(ROSTERS, p.roster)) names = ROSTERS[p.roster]!;
  else throw new PyError("KeyError", pyStrRepr(p.roster));
  const missing = names.filter((n) => !Object.hasOwn(PRESETS, n));
  if (missing.length > 0) throw new PyError("KeyError", pyStrRepr(`roster names ${listRepr(missing)}, which are not in PRESETS`));
  return [...names];
}

/** `a // b` for ints. */
function floorDiv(a: number, b: number): number {
  if (b === 0) throw new PyError("ZeroDivisionError", "integer division or modulo by zero");
  return Math.floor(a / b);
}

/** Page size and row count for this many tiles. */
function grid(p: SheetParams, count: number): readonly [number, number, number] {
  const rows = Math.max(1, -floorDiv(-count, p.columns));
  const cellH = p.label_h + p.tile_h;
  const w = p.margin * 2 + p.columns * p.tile_w + (p.columns - 1) * p.gap;
  const h = p.margin * 2 + rows * cellH + (rows - 1) * p.gap;
  return [w, h, rows];
}

function tileOrigin(p: SheetParams, i: number): readonly [number, number] {
  const col = pyModInt(i, p.columns);
  const row = floorDiv(i, p.columns);
  const x = p.margin + col * (p.tile_w + p.gap);
  const y = p.margin + row * (p.label_h + p.tile_h + p.gap);
  return [x, y];
}

/** Break a description into lines, at word boundaries. */
function breakDescription(text: string, maxChars = 45): string[] {
  const words = text.split(/\s+/).filter((w) => w !== "");
  const lines: string[] = [];
  let current: string[] = [];
  let currentLength = 0;
  for (const word of words) {
    const wordLength = word.length + (current.length > 0 ? 1 : 0);
    if (currentLength + wordLength > maxChars && current.length > 0) {
      lines.push(current.join(" "));
      current = [word];
      currentLength = word.length;
    } else {
      current.push(word);
      currentLength += wordLength;
    }
  }
  if (current.length > 0) lines.push(current.join(" "));
  return lines;
}

/**
 * The character's name and role description, centred over its card. Plain fill, no outline: this sits on a flat dark
 * ground where a stroke would only thicken the letters.
 */
function label(p: SheetParams, preset: string, displayName: string, x: number, y: number): string {
  const description = Object.hasOwn(CHARACTER_DESCRIPTIONS, preset) ? CHARACTER_DESCRIPTIONS[preset]! : "";
  const nameY = y + 16.0;
  const descY = y + 32.0;
  const nameSvg =
    `<text x="${fmt1(x + p.tile_w / 2)}" y="${fmt1(nameY)}" text-anchor="middle" ` +
    `font-family="${p.label_font}" font-size="${fmt1(p.label_size)}" font-weight="bold" ` +
    `fill="${p.palette.label}">${displayName}</text>`;
  let descSvg = "";
  if (description) {
    const lines = breakDescription(description, 45);
    const lineHeight = p.description_size * 1.2;
    const startY = descY - ((lines.length - 1) * lineHeight) / 2;
    const tspans = lines.map((line) => `<tspan x="${fmt1(x + p.tile_w / 2)}" dy="${fmt1(lineHeight)}">${line}</tspan>`);
    descSvg =
      `\n    <text x="${fmt1(x + p.tile_w / 2)}" y="${fmt1(startY)}" text-anchor="middle" ` +
      `font-family="${p.label_font}" font-size="${fmt1(p.description_size)}" ` +
      `fill="${p.palette.label}" opacity="0.8" font-style="italic">${tspans.join("")}</text>`;
  }
  return nameSvg + descSvg;
}

/**
 * One card with one figure standing on it. The figure is scaled off its own skeleton rather than off the drawing's
 * bounding box, so every tile puts its character at the same body scale.
 */
function tile(p: SheetParams, preset: string, x: number, y: number): string {
  const top = y + p.label_h;
  const character = PRESETS[preset]!;
  // The hat is taken off for the skeleton alone, because its headroom shrinks the figure on the canvas and every tile has
  // to stand at the same body scale.
  const bare = replace(character, { outfit: replace(character.outfit, { hat_color: null }) });
  const sk = skeletonFor(bare);
  const k = (p.tile_h * p.figure_height) / sk.canvas_h;
  const fx = x + p.tile_w / 2 - (sk.canvas_w * k) / 2;
  const fy = top + p.tile_h * p.figure_feet_y - sk.foot_y * k;
  // Each tile its own id prefix: the eye's clip path is `eye-l` in every figure, and a viewer takes one definition for them
  // all, which clipped Risa's iris away when her eye was drawn through another figure's clip.
  const doc = renderCharacter(character, sk, null, false, preset);
  const body = doc.replace(/^<svg[^>]*>\s*/, "").replace(/<\/svg>\s*$/, "").trim();
  if (!Object.hasOwn(DISPLAY_NAMES, preset)) throw new PyError("KeyError", pyStrRepr(preset));
  return (
    `<rect x="${fmt1(x)}" y="${fmt1(top)}" width="${fmt1(p.tile_w)}" height="${fmt1(p.tile_h)}" ` +
    `fill="${p.palette.card}" />\n` +
    `  ${label(p, preset, DISPLAY_NAMES[preset]!, x, y)}\n` +
    `  <g transform="translate(${fmt1(fx)} ${fmt1(fy)}) scale(${fmtFixed(k, 4)})">\n  ${body}\n  </g>`
  );
}

/**
 * The sheet's own `<metadata>` element: like `metadataBlock`, except a sheet has no single character to reproduce, so this
 * carries one named `<character>` per member instead of one bare one.
 */
export function sheetMetadataBlock(members: readonly string[]): string {
  const entries = members
    .map((name) => `    <character name="${escape(name)}">${escape(characterUrl(PRESETS[name]!, TOOL_URL))}</character>\n`)
    .join("");
  return `<metadata>\n${metadataHeader()}${entries}  </metadata>`;
}

/**
 * Draw one sheet and return the whole SVG document as a string. Deterministic, like `renderCharacter` and `renderCover`.
 * `metadata` embeds an SVG `<metadata>` block naming every member and a link that reproduces each of them. Off by default so
 * the committed sheets in `ref-out/` do not churn.
 */
export function renderSheet(params?: SheetParams | null, metadata = false): string {
  const p = params ?? sheetParams();
  const names = membersOf(p);
  const [w, h] = grid(p, names.length);
  const tiles = names.map((preset, i) => {
    const [x, y] = tileOrigin(p, i);
    return tile(p, preset, x, y);
  });
  const body = tiles.join("\n  ");
  const md = metadata ? `  ${sheetMetadataBlock(names)}\n` : "";
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" width="${fmt0(w)}" height="${fmt0(h)}" ` +
    `viewBox="0 0 ${fmt0(w)} ${fmt0(h)}">\n` +
    `${md}` +
    `  <rect width="${fmt0(w)}" height="${fmt0(h)}" fill="${p.palette.ground}" />\n` +
    `  ${body}\n` +
    `</svg>\n`
  );
}
