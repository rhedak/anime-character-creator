// The traced head data of each adult hairstyle: what the adult head parts (body-adult-parts.ts) draw for the face's visible skin, the hair
// silhouette, the strand lines, the skin beside the face and the ears. The data is a consequence of the hair (the hairline, which skin shows
// between the locks, whether the ears are covered), so it is chosen by the hairstyle, and a character on the adult body gets its cut from
// `hairstyle`. Franzi's `swept_ponytail` is the default and every other name falls back to it; each cut is traced from its character's
// reference (harness/franzi_hair/ for hers, harness/risa_adult/ for Risa's).

import type { Lock } from "./core-head-tables.ts";
import type { Chain } from "./tables.ts";
import type { CharacterParams } from "./params.ts";
import { ADULT_HAIR_STRANDS } from "./body-adult-head-data.ts";
import { ADULT_EAR_CONCHA_L, ADULT_EAR_CONCHA_R, ADULT_HAIR_SILHOUETTE, ADULT_SKIN_EAR_L, ADULT_SKIN_EAR_R, ADULT_SKIN_FACE, ADULT_SKIN_STRIPS } from "./body-adult-outline-data.ts";
import { ADULT_EAR_FOLDS_L, ADULT_EAR_FOLDS_R, ADULT_EAR_FOLD_WIDTHS_L, ADULT_EAR_FOLD_WIDTHS_R } from "./body-adult-ear-data.ts";
import { mirrorChain, shiftChain, symmetricJaw } from "./body-adult-cut-level.ts";
import { RISA_BROWS, RISA_BROW_WIDTHS, RISA_HAIR_EDGE_STRANDS, RISA_FRINGE_HAIR, RISA_FRINGE_LINES, RISA_FRINGE_LINE_WIDTHS, RISA_HAIR_SILHOUETTE, RISA_HAIR_STRANDS, RISA_SKIN_FACE } from "./body-adult-risa-data.ts";

/** One ear: its skin, the shaded inner part, and the fold lines with their measured thicknesses. A cut that covers the ear has none. */
export interface AdultEar {
  readonly skin: readonly Chain[];
  readonly concha: readonly Chain[];
  readonly folds: readonly Chain[];
  readonly foldWidths: readonly (readonly number[])[];
}

export interface AdultHeadCut {
  /** The visible skin of the face, each chain filled and stroked; its edge is the hairline, the locks' inner edges and the jaw. */
  readonly face: readonly Chain[];
  /** The hair silhouette, drawn behind the whole body; the strands are clipped to it. */
  readonly silhouette: readonly Chain[];
  readonly strands: readonly Chain[];
  /** The strand lines' tone as `shade()` factors of the hair colour (value, saturation) and their weight as `outlineW`'s multiple: Franzi's dark hair has lighter lines, Risa's red hair darker ones. */
  readonly strandTone: readonly [number, number];
  readonly strandWeight: number;
  /**
   * A fringe drawn as a shape of its own over the skin (which then runs up under it): the hair as closed shapes with the real tips and the slits between locks, and the thin
   * lines along its edge where it meets skin with their thicknesses in head radii. The face's own stroke is then not what draws the hairline. null for a cut without one.
   */
  readonly fringe: { readonly hair: readonly Chain[]; readonly lines: readonly Chain[]; readonly widths: readonly (readonly number[])[] } | null;
  /** Lines that run down to the face's edge and end on it, blunt (the face's skin is drawn over what passes the edge), and their weight as `outlineW`'s multiple. */
  readonly edgeStrands: readonly Chain[];
  readonly edgeStrandWeight: number;
  /** The weight of the stroke round the face's visible skin, as `outlineW`'s multiple: Risa's reference draws the hairline and the jaw thin. */
  readonly faceWeight: number;
  /** Brows drawn as thin tapering lines (the viewer's left then right) instead of the filled brow shapes of body-adult-brow-data.ts, with their thicknesses and `shade()` factors of the hair colour; null keeps the traced shapes. */
  /** Where the hair clip sits, in head radii about the head's centre, for a cut whose hair the shared placement (beside the hair's edge) does not suit; null keeps the shared placement. */
  readonly clip: readonly [number, number] | null;
  /** The iris centre of each eye (key -1 the viewer's left, 1 the right) in reference pixels, the origin of the eye's frame: where the head's eyes sit and how far the head is turned. */
  readonly irisAt: Readonly<Record<number, readonly [number, number]>>;
  /** The eye's colour of the white and the weight of the soft outline round the lower half of the aperture, as a multiple of the traced eye's. */
  readonly eye: { readonly sclera: string; readonly lowerLine: number; readonly lidThickness: number; readonly lidColor: string | null; readonly lashWeight: number };
  /** The cheeks' flush, in reference pixels (the face's calibration): centre, radii and a turn in degrees, left then right; null keeps Franzi's. Risa's right eye sits 12 px higher than her left (the head is tilted), so her right cheek is higher than Franzi's. */
  readonly cheeks: readonly { readonly c: readonly [number, number]; readonly rx: number; readonly ry: number; readonly turn: number }[] | null;
  /** Where the nose and the mouth sit, as a shift in reference pixels from the traced (Franzi's) placement: a cut whose eyes sit elsewhere moves them with its eyes. [0, 0] for Franzi's. */
  readonly featuresAt: { readonly nose: readonly [number, number]; readonly mouth: readonly [number, number] };
  /** Whether the mouth is made symmetric (the traced line's right half rises further than its left, a smirk on a straight face): the left half is mirrored for the right. */
  readonly symmetricMouth: boolean;
  readonly brows: { readonly lines: readonly Chain[]; readonly widths: readonly (readonly number[])[]; readonly tone: readonly [number, number] } | null;
  /** Small skin regions beside the face, drawn over the hair after the body. */
  readonly strips: readonly Chain[];
  readonly earL: AdultEar;
  readonly earR: AdultEar;
  /** The soft finish's clumps, in head radii about the head's centre; none draws none. */
  readonly locks: readonly Lock[];
}

/** The soft finish's clumps on Franzi's hair, in head radii about the head's centre (hand placed on a grid over the render, as the chibi cuts' `Lock`s are): the crown's two arcs from the parting, the curtains' and the ponytail's falls. */
const SWEPT_PONYTAIL_LOCKS: readonly Lock[] = [
  ["lit", [[0.12, -1.0], [0.4, -0.92], [0.68, -0.7], [0.84, -0.35]], 0.18, 0.94],
  ["lit", [[-0.12, -1.0], [-0.42, -0.92], [-0.68, -0.7], [-0.84, -0.35]], 0.18, 0.94],
  ["shadow", [[0.1, -0.9], [0.3, -0.82], [0.52, -0.62], [0.62, -0.35]], 0.12, 0.9],
  ["shadow", [[-0.1, -0.9], [-0.3, -0.82], [-0.52, -0.62], [-0.62, -0.35]], 0.12, 0.9],
  ["shadow", [[-0.86, -0.3], [-0.88, 0.1], [-0.8, 0.6], [-0.66, 1.1]], 0.14, 0.92],
  ["lit", [[-0.7, 0.0], [-0.68, 0.4], [-0.6, 0.8]], 0.1, 0.9],
  ["shadow", [[0.8, 0.0], [0.86, 0.5], [0.8, 1.0], [0.68, 1.35]], 0.16, 0.92],
  ["lit", [[0.62, 0.2], [0.7, 0.6], [0.66, 1.0], [0.58, 1.3]], 0.11, 0.9],
];

const SWEPT_PONYTAIL: AdultHeadCut = {
  face: ADULT_SKIN_FACE,
  silhouette: ADULT_HAIR_SILHOUETTE,
  strands: ADULT_HAIR_STRANDS,
  strandTone: [2.6, 0.9],
  strandWeight: 0.5,
  fringe: null,
  edgeStrands: [],
  edgeStrandWeight: 0.5,
  faceWeight: 1,
  clip: null,
  cheeks: null,
  eye: { sclera: "#ffffff", lowerLine: 1, lidThickness: 1, lidColor: null, lashWeight: 1 },
  irisAt: { [-1]: [606, 325], 1: [718.5, 321.5] },
  featuresAt: { nose: [0, 0], mouth: [0, 0] },
  symmetricMouth: false,
  brows: null,
  strips: ADULT_SKIN_STRIPS,
  earL: { skin: ADULT_SKIN_EAR_L, concha: ADULT_EAR_CONCHA_L, folds: ADULT_EAR_FOLDS_L, foldWidths: ADULT_EAR_FOLD_WIDTHS_L },
  earR: { skin: ADULT_SKIN_EAR_R, concha: ADULT_EAR_CONCHA_R, folds: ADULT_EAR_FOLDS_R, foldWidths: ADULT_EAR_FOLD_WIDTHS_R },
  locks: SWEPT_PONYTAIL_LOCKS,
};

const NO_EAR: AdultEar = { skin: [], concha: [], folds: [], foldWidths: [] };

// Risa's face made straight and symmetric (body-adult-cut-level.ts). Her reference has the head tilted and turned a little (her right eye 12 px above the left, the chin right of the eyes'
// midline), so the eyes are put level about one midline, the left brow is mirrored for the right, the jaw is made symmetric and the nose and mouth are on the midline.
const RISA_MID = 672.2;
const RISA_EYE_Y = 313.5;
const RISA_EYE_HALF = 55.2;
const RISA_LEFT_IRIS_Y = 319.6;
const RISA_BROW_RIGHT = mirrorChain(shiftChain(RISA_BROWS[0] as Chain, 0, RISA_EYE_Y - RISA_LEFT_IRIS_Y), RISA_MID, RISA_BROW_WIDTHS[0]);
const RISA_FACE_STRAIGHT: readonly Chain[] = RISA_SKIN_FACE.map((c) => symmetricJaw(c, RISA_MID, 315, 30));

/** Risa's hair: long and straight with a blunt fringe, hanging behind the shoulders and the arms with both ears under it. */
const LONG_STRAIGHT_FRINGED: AdultHeadCut = {
  face: RISA_FACE_STRAIGHT,
  silhouette: RISA_HAIR_SILHOUETTE,
  strands: RISA_HAIR_STRANDS,
  strandTone: [0.42, 1.0],
  strandWeight: 0.45,
  fringe: { hair: RISA_FRINGE_HAIR, lines: RISA_FRINGE_LINES, widths: RISA_FRINGE_LINE_WIDTHS },
  edgeStrands: RISA_HAIR_EDGE_STRANDS,
  edgeStrandWeight: 0.5,
  faceWeight: 0.45,
  clip: [0.637, -0.213],
  cheeks: [
    { c: [RISA_MID - 61.2, 355], rx: 25, ry: 10, turn: -8 },
    { c: [RISA_MID + 61.2, 355], rx: 25, ry: 10, turn: 8 },
  ],
  // Her white is a warm light tone (the median of the reference's, (242, 228, 222)) and the line under her eye is faint.
  // Her lid is a fine dark-brown line in the reference, not Franzi's heavy black band: thinner (about half), brown, and with finer lashes.
  eye: { sclera: "#f2e4de", lowerLine: 0.35, lidThickness: 0.5, lidColor: "#2e1a14", lashWeight: 0.7 },
  // Measured on the reference's green iris blobs (harness/risa_adult/eye_metrics.py); her eyes sit further right and her right eye higher than Franzi's, the head being turned and tilted a little.
  // The traced irises were (617, 319.6) and (727.4, 307.4); they are now level about the midline.
  irisAt: { [-1]: [RISA_MID - RISA_EYE_HALF, RISA_EYE_Y], 1: [RISA_MID + RISA_EYE_HALF, RISA_EYE_Y] },
  // Franzi's nose and mouth sit about her eyes' midline (662.25, 323.25) with the nose a little left of it and the mouth a little right; hers go about Risa's, centred on the midline.
  symmetricMouth: true,
  featuresAt: { nose: [RISA_MID - 660, RISA_EYE_Y - 323.25], mouth: [RISA_MID - 666.5, RISA_EYE_Y - 323.25] },
  brows: {
    lines: [shiftChain(RISA_BROWS[0] as Chain, 0, RISA_EYE_Y - RISA_LEFT_IRIS_Y), RISA_BROW_RIGHT.chain],
    widths: [RISA_BROW_WIDTHS[0] as readonly number[], RISA_BROW_RIGHT.widths as readonly number[]],
    tone: [0.38, 1.0],
  },
  strips: [],
  earL: NO_EAR,
  earR: NO_EAR,
  locks: [],
};

/** The adult hairstyles and the cut each is drawn with. */
export const ADULT_HEAD_CUTS: Readonly<Record<string, AdultHeadCut>> = {
  swept_ponytail: SWEPT_PONYTAIL,
  long_straight_fringed: LONG_STRAIGHT_FRINGED,
};

/** The cut a character's adult head is drawn with: its hairstyle's, and Franzi's for a hairstyle that has none. */
export const adultCutOf = (p: CharacterParams): AdultHeadCut => (Object.hasOwn(ADULT_HEAD_CUTS, p.hairstyle) ? (ADULT_HEAD_CUTS[p.hairstyle] as AdultHeadCut) : SWEPT_PONYTAIL);
