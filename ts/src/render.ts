// `render_character`: the assembly. A transcription of character.py's `render_character` (lines 14028 to 14265 of the
// Python), slot for slot, so the stage names equal the oracle's (`chest[3]`, `under_arms[0]`, `layers[17]`, `body`, `body_soft`,
// `body_ns`, `doc`). Slots 11 and 14 of `layers` are the spread `*chest` and `*under_arms` and have no stage of their own.
//
// It runs with whatever is ported. A part that is not in the registry makes its own slot `null` and every stage that needs
// that slot `null` too; `renderCharacter` refuses to return a document while anything is missing and names what is.

import { metadataBlock } from "./attribution.ts";
import "./body-adult-hair.ts";
import { ADULT_BODY_TYPES } from "./body-adult.ts";
import { ADULT_GARMENT_PARTS } from "./body-adult-garments.ts";
import { ADULT_PARTS, withLoweredHead } from "./body-adult-parts.ts";
import { skeletonFor } from "./body.ts";
import { documentWrap, namespaceIds, soft, softStrokeWidths } from "./character.ts";
import { characterParams, validateFinish } from "./model.ts";
import type { CharacterParams } from "./params.ts";
import { PARTS as arms } from "./parts-arms.ts";
import { PARTS as body } from "./parts-body.ts";
import { PARTS as face } from "./parts-face.ts";
import { PARTS as garments } from "./parts-garments.ts";
import { PARTS as hair } from "./parts-hair.ts";
import { PARTS as props } from "./parts-props.ts";
import type { PartTable } from "./parts.ts";
import { plainParams } from "./plain.ts";
import { truthy } from "./pynum.ts";
import type { Skeleton } from "./skeleton.ts";

export const ALL_PARTS: PartTable = { ...hair, ...face, ...body, ...arms, ...garments, ...props };

export interface RenderOptions {
  readonly sk?: Skeleton;
  readonly background?: unknown;
  readonly metadata?: unknown;
  readonly id_prefix?: unknown;
}

/** The stages of one render by the oracle's names; `null` where a part the stage needs is not ported yet. */
export interface Stages {
  readonly stages: ReadonlyMap<string, string | null>;
  readonly missing: readonly string[];
}

export class NotPorted extends Error {
  readonly missing: readonly string[];
  constructor(missing: readonly string[]) {
    super(`not ported yet: ${missing.join(", ")}`);
    this.name = "NotPorted";
    this.missing = missing;
  }
}

export function renderStages(typed: CharacterParams, opts: RenderOptions = {}, shared: PartTable = ALL_PARTS): Stages {
  validateFinish(typed);
  const p = plainParams(typed);
  // An adult body draws its own torso, legs and underwear; the head, hair, face and garments are the shared parts.
  const parts: PartTable = shared === ALL_PARTS && Object.hasOwn(ADULT_BODY_TYPES, p.body) ? { ...shared, ...withLoweredHead(shared), ...ADULT_PARTS, ...ADULT_GARMENT_PARTS } : shared;
  const sk = opts.sk ?? skeletonFor(p);
  const missing = new Set<string>();
  const stages = new Map<string, string | null>();

  /** Call a part by Python name, or note that it is missing. */
  const call = <T>(name: string, ...args: unknown[]): T | null => {
    const fn = parts[name];
    if (fn === undefined) {
      missing.add(name);
      return null;
    }
    return fn(...args) as T;
  };
  const part = (name: string, ...extra: unknown[]): string | null => call<string>(name, sk, p, ...extra);
  const record = (stage: string, text: string | null): string | null => {
    stages.set(stage, text);
    return text;
  };
  const when = (cond: boolean, name: string, ...extra: unknown[]): string | null => (cond ? part(name, ...extra) : "");
  const join = (items: readonly (string | null)[], sep: string): string | null => (items.some((x) => x === null) ? null : (items as string[]).join(sep));

  // Everything worn on the torso up to the arms, built once: drawn in its place, and again over the arms masked to a bust.
  const coat = p.outfit.coat_color !== null;
  const chest = [
    part("_tunic"),
    part("_bust_lines"),
    part("_underwear_top"),
    part("_navel"),
    part("_chest_lines"),
    part("_robe_front"),
    part("_placket"),
    part("_chest_pockets"),
    part("_strap"),
    part("_apron"),
    when(coat, "_belt"),
    when(truthy(p.outfit.collar_mock), "_collar"),
    part("_coat"),
    when(!coat, "_belt"),
    part("_pouches"),
    part("_crystal_harness"),
  ].map((t, i) => record(`chest[${i}]`, t));
  const underArms = [part("_traced_coat_and_belt", false)].map((t, i) => record(`under_arms[${i}]`, t));

  const handsAfterCoat = call<boolean>("_hands_after_coat", sk, p);
  const wrap = (outer: string, inner: string | null): string | null => (inner === null ? null : call<string>(outer, inner, p));

  const slots: [number, string | null][] = [
    [0, part("_hair_defs")],
    [1, part("_hat_underside")],
    [2, part("_hair_tail")],
    [3, wrap("_hair_lines", part("_hair_mass"))],
    [4, wrap("_without_raised_sleeves", part("_torso"))],
    [5, part("_neck")],
    [6, part("_legs_and_boots")],
    [7, part("_underskirt")],
    [8, part("_skirt")],
    [9, part("_hakama")],
    [10, part("_hanging_sleeves")],
    // 11: *chest
    [12, part("_katana")],
    [13, part("_staff")],
    // 14: *under_arms
    [15, handsAfterCoat === null ? null : part("_arms", handsAfterCoat ? false : null)],
    [16, (() => { const j = join([...chest, ...underArms], ""); return j === null ? null : part("_bust_over_arms", j); })()],
    [17, part("_traced_coat_and_belt", true)],
    [18, handsAfterCoat === null ? null : handsAfterCoat ? part("_arms", true) : ""],
    [19, part("_shoulder_bars")],
    [20, when(!truthy(p.outfit.collar_mock), "_collar")],
    [21, part("_ribbon")],
    [22, part("_mask")],
    [23, part("_ears")],
    [24, part("_head")],
    [25, part("_beard")],
    [26, part("_face")],
    [27, part("_glasses")],
    [28, part("_goggles_strap")],
    [29, wrap("_hair_lines", part("_hair_front"))],
    [30, part("_brows_over_hair")],
    [31, part("_hair_knot")],
    [32, part("_hair_tie")],
    [33, part("_hair_clip")],
    [34, part("_goggles")],
    [35, part("_blindfold")],
    [36, part("_headscarf")],
    [37, part("_hat")],
    [38, part("_familiar")],
  ];
  for (const [i, t] of slots) record(`layers[${i}]`, t);

  // Back to front: the layers in order, the chest and the under-arms layers spread where the Python spreads them.
  const ordered: (string | null)[] = [];
  for (const [i, t] of slots) {
    ordered.push(t);
    if (i === 10) ordered.push(...chest);
    if (i === 13) ordered.push(...underArms);
  }
  const joined = join(ordered.filter((t) => t !== ""), "\n  ");
  let text: string | null = joined;
  record("body", text);
  if (text !== null && soft(p)) text = softStrokeWidths(text);
  record("body_soft", text);
  const prefix = opts.id_prefix ?? "";
  if (text !== null && truthy(prefix)) text = namespaceIds(text, prefix);
  record("body_ns", text);
  record("doc", text === null ? null : documentWrap(sk, text, opts.background ?? null, truthy(opts.metadata) ? metadataBlock(typed) : ""));
  return { stages, missing: [...missing].sort() };
}

/**
 * Draw one character and return the whole SVG document as a string (`render_character`), with Python's parameters in
 * Python's order: the character (`None` draws the default one), a skeleton (`None` builds the character's own), a
 * background paint, whether to embed the metadata block, and a prefix for every id the drawing defines.
 */
export function renderCharacter(
  p?: CharacterParams | null,
  sk?: Skeleton | null,
  background: unknown = null,
  metadata: unknown = false,
  id_prefix: unknown = "",
): string {
  const { stages, missing } = renderStages(truthy(p) ? (p as CharacterParams) : characterParams(), { sk: sk ?? undefined, background, metadata, id_prefix });
  if (missing.length > 0) throw new NotPorted(missing);
  return stages.get("doc") as string;
}

/** `renderCharacter` with named options, for callers that pass only a few. */
export const renderCharacterWith = (p?: CharacterParams | null, o: RenderOptions = {}): string =>
  renderCharacter(p, o.sk, o.background, o.metadata, o.id_prefix);
