// The core-head module's tables: the hair cuts' traced contours, locks and strands, and the numbers they are placed by.
// Generated once by harness/ts_port/gen_core_head.py from character.py (never typed), then owned by hand.

import { degrees, pyAcos } from "./pynum.ts";
import type { Chain, Point, Segment } from "./tables.ts";

// One clump of hair for the soft finish: its role ("shadow" or "lit"), the points of its centre
// line in head radii (x right, y down, origin at the head centre, the units the chains use), its
// widest width in head radii, and how far down the line it runs, 0 to 1.
export type Lock = readonly [string, readonly Point[], number, number];

// No hair ink may reach above -1.36 head radii from the head centre, and the
// stroke's outer half counts as ink. That is the headroom `build_skeleton`'s
// `hair_margin` leaves above the skull, and nothing derives the bound from the
// shapes here, so a taller crown silently comes out sliced flat against the
// canvas edge, which is how both chibis shipped before it was measured. The
// tallest point below is the short cut's crown, painted edge about -1.30.
//
// Hair is described in two zones. Above the cheek line it is pinned to the
// skull, so those points are literal head-radius units. Below it the shape is
// a fall whose points are given as a fraction of the way to the tips, so
// `hair_length` restyles the whole thing without touching the crown, and the
// hair keeps its relationship to the body when proportions change.
export const HAIR_CHEEK_Y = 0.72;
// How far a lock's line runs on past its tip (`Hairstyle.tip_lines`), in head
// radii: the parted cut's reference carries it 0.09 to 0.16 past where its
// colour stops, on the front locks, the one place it shows against its page.
export const HAIR_TIP_LINE = 0.12;
// Where a two-tone head of hair changes tone, as a fraction of its own height
// from the crown down to its lowest tips. Half and half is the owner's ratio.
//
// A fraction of the whole silhouette, not of the fall: the fall lengthens with
// the body while the crown stays pinned to the skull, so one fall fraction
// comes out at different heights per build. The line that sat three quarters
// of the way down the chibi's hair sat two thirds of the way down the adult's,
// which is the same character coloured differently at each build. Stated this
// way one number holds for both cuts at every build, and moving the fade is
// moving this.
export const HAIR_FADE = 0.50;
// Top of the long cut's silhouette, which is the crown anchor in
// `_hair_mass_shape`. The short cut's own top is its crown radius, `_CROWN_R`.
export const HAIR_CROWN_Y = -1.16;
// The short cut's crown is an arc of a circle about the head centre, so 0.28 head
// radii of hair over a skull of radius 1. It runs temple to temple, the temple
// being the point on that circle at y = -0.30, below which the mass flares out to
// the cheek and the side locks begin.
export const CROWN_R = 1.28;
export const CROWN_TO_TEMPLE = degrees(pyAcos(0.30 / CROWN_R));
// The long cut's fall, as the five x values its outer edge is built from, in head
// radii. They live here because three separate places have to agree on them: the
// mass draws this edge, `_fall_edge` hands the same edge to the front lock, and
// the hairline's closing path meets it at the cheek. Moving one and not the others
// opens a sliver of mass outside the lock with a stroke down each side of it,
// which is the double line the hair contract warns about, and it is what happened
// the first time this was tried.
//
// `_CHEEK` is the one that decides how much hair shows beside the face, which is
// the fall's visible width where it matters most.
// A fourth thing has to move with them, which is not expressible here: the two
// strand lines down each fall sit at fixed head radii, so widening the edge
// without pushing them out leaves one of them lying outside the new lock and
// reading as the fall's boundary. `_long_strands` carries a matching offset.
export const FALL_TEMPLE_X = 1.22;
export const FALL_CHEEK_X = 1.26;
export const FALL_MID_X = 1.36;
export const FALL_WIDE_X = 1.44;
export const FALL_FLARE_X = 1.52;
export const FALL_TIP_X = 1.22;
// Satoko's traced cut.
//
// Both boundaries come off `ref/satoko-chibi-hair.png`, her hair cut out of the
// chibi reference by the owner, and the signal is **the drawn black outline**
// rather than the crop's alpha. The alpha is a rough selection: some of the page
// came through opaque and the face opening's edge is a staircase. The ink is the
// artist's own line and is exact wherever the selection is not.
//
// Reading ink works on a crop of the hair alone and does not on a whole face,
// because brows and eyes are the only other dark things on one. Here the
// furthest ink along a bearing is the mass and the nearest is the hairline, with
// nothing between them that could be either. `out/trace/satoko.py` carries it,
// and the crop places back into the reference at a mean squared error of 1.
//
// 18 and 8 segments: the finest levels with no edge under two stroke widths at
// either build, the same bound the other traced cuts were chosen on.
export const LONG_EDGE_START: Point = [-0.782, 1.677];
export const LONG_EDGE: Segment[] = [
  [[-0.933, 1.651], [-1.050, 1.557]],
  [[-1.165, 1.666], [-1.171, 1.612]],
  [[-1.250, 1.572], [-1.306, 1.502]],
  [[-1.362, 1.434], [-1.388, 1.341]],
  [[-1.283, 0.169], [-1.232, -0.307]],
  [[-1.183, -0.490], [-1.094, -0.657]],
  [[-0.997, -0.821], [-0.858, -0.953]],
  [[-0.721, -1.070], [-0.561, -1.150]],
  [[-0.342, -1.242], [-0.109, -1.251]],
  [[0.140, -1.229], [0.386, -1.187]],
  [[0.556, -1.141], [0.701, -1.040]],
  [[0.878, -0.907], [1.002, -0.728]],
  [[1.128, -0.525], [1.186, -0.296]],
  [[1.230, 0.160], [1.338, 1.338]],
  [[1.314, 1.432], [1.260, 1.501]],
  [[1.199, 1.562], [1.127, 1.609]],
  [[1.126, 1.670], [1.006, 1.550]],
  [[0.883, 1.665], [0.710, 1.672]],
];
export const LONG_LINE_START: Point = [-0.767, 1.674];
export const LONG_LINE: Segment[] = [
  [[-0.881, 1.265], [-0.927, 0.794]],
  [[-0.936, 0.396], [-0.884, -0.000]],
  [[-0.588, -0.091], [-0.315, -0.237]],
  [[-0.083, -0.378], [0.103, -0.587]],
  [[0.237, -0.364], [0.440, -0.205]],
  [[0.624, -0.074], [0.838, 0.015]],
  [[0.886, 0.371], [0.881, 0.724]],
  [[0.876, 0.756], [0.785, 0.756]],
  [[0.877, 0.756], [0.877, 0.792]],
  [[0.828, 1.275], [0.716, 1.676]],
];
// How far above the mass's own lower edge the gold gives way to the pale tips.
// Larger than the crop's because these are falls rather than blades: the tips
// run a long way and the canon turns them pale over roughly their last third.
export const LONG_BASE_TIP = 1.677;
export const LONG_TONE_LIFT = 0.62;
// How far the hairline's two ends are pulled toward the centre, in head radii.
export const LONG_LINE_TUCK = 0.04;
// Which segment ends on the crown's apex, so the two sides can be taken apart.
export const LONG_CROWN_AT = 9;
// The clumps the soft finish lays over the long traced cut (`Hairstyle.locks`), placed by hand on
// `harness/soft_hair/grid.py` at a fall of 2.0 and re-stretched to the fall the cut is drawn at the
// way `_long_scaled` stretches the contour: only y below the cheek line, x as authored. Per side:
// the crown along the contour, the sweep off the parting, the outer curtain and the inner curtain.
// The flow is the cut's own: from the parting out over the skull and down. See `_FRINGED_LOCKS`.
export const LONG_LOCKS_FALL = 2.0;
export const LONG_LOCKS: Lock[] = [
  ["lit", [[-0.10, -1.02], [-0.55, -0.95], [-0.92, -0.62], [-1.08, -0.25], [-1.14, 0.05]], 0.19, 0.97],
  ["shadow", [[-0.30, -0.90], [-0.60, -0.68], [-0.82, -0.34], [-0.98, -0.02]], 0.12, 0.90],
  ["lit", [[-1.17, 0.15], [-1.19, 0.80], [-1.22, 1.30], [-1.25, 1.75]], 0.17, 0.96],
  ["shadow", [[-1.00, 0.40], [-1.02, 0.90], [-1.00, 1.40], [-0.92, 1.90]], 0.13, 0.88],
  ["lit", [[0.08, -1.04], [0.52, -0.96], [0.90, -0.64], [1.06, -0.26], [1.12, 0.05]], 0.17, 0.95],
  ["shadow", [[0.36, -0.90], [0.62, -0.70], [0.84, -0.36], [0.99, -0.02]], 0.13, 0.94],
  ["lit", [[1.16, 0.15], [1.19, 0.80], [1.23, 1.30], [1.27, 1.75]], 0.20, 0.98],
  ["shadow", [[0.99, 0.40], [1.01, 0.90], [0.99, 1.40], [0.92, 1.90]], 0.15, 0.90],
];
// The clumps the soft finish lays over the short layered cut's front hair (`Hairstyle.locks`),
// placed by hand on `harness/soft_hair/grid.py`. The cut is pinned to the skull above the cheek
// line, where nothing stretches with the fall, so they are used as authored. The flow is the
// crop's own: from the crown out and down over the temples, the fringe falling in pieces off it.
export const SHORT_LOCKS: Lock[] = [
  ["lit", [[-0.10, -1.20], [-0.55, -1.12], [-0.92, -0.82], [-1.10, -0.40], [-1.18, 0.05]], 0.19, 0.97],
  ["shadow", [[-0.25, -1.10], [-0.62, -0.90], [-0.88, -0.55], [-0.98, -0.20]], 0.14, 0.92],
  ["lit", [[-0.20, -1.05], [-0.35, -0.80], [-0.45, -0.50], [-0.42, -0.22]], 0.13, 0.90],
  ["shadow", [[-1.14, 0.02], [-1.17, 0.26], [-1.12, 0.50]], 0.10, 0.90],
  ["shadow", [[0.10, -1.10], [0.18, -0.80], [0.25, -0.50], [0.20, -0.30]], 0.12, 0.90],
  ["lit", [[0.30, -1.10], [0.65, -0.92], [0.90, -0.58], [1.00, -0.28]], 0.15, 0.94],
  ["lit", [[0.12, -1.20], [0.58, -1.12], [0.95, -0.82], [1.12, -0.40], [1.19, 0.05]], 0.18, 0.96],
  ["shadow", [[1.14, 0.02], [1.17, 0.26], [1.12, 0.50]], 0.10, 0.90],
];
// The clumps for the traced crop (`Hairstyle.locks`): a spiky crown swept to the viewer's right with a
// fringe of four pieces, placed by hand on `harness/soft_hair/grid.py`. Pinned to the skull above the
// cheek line, so used as authored. Drawn on the mass too, since its spikes stand outside the front piece.
export const CROP_LOCKS: Lock[] = [
  ["lit", [[-0.10, -1.45], [0.40, -1.30], [0.90, -0.95], [1.25, -0.55]], 0.20, 0.96],
  ["shadow", [[-0.30, -1.25], [-0.70, -1.05], [-1.00, -0.70], [-1.15, -0.40]], 0.17, 0.92],
  ["lit", [[-0.05, -1.30], [-0.45, -1.18], [-0.85, -0.95], [-1.20, -0.75]], 0.14, 0.88],
  ["shadow", [[-0.55, -1.00], [-0.60, -0.75], [-0.62, -0.50]], 0.12, 0.92],
  ["lit", [[-0.20, -1.00], [-0.25, -0.75], [-0.30, -0.50]], 0.12, 0.90],
  ["shadow", [[0.20, -1.00], [0.28, -0.70], [0.30, -0.45]], 0.12, 0.90],
  ["lit", [[0.55, -1.00], [0.62, -0.70], [0.68, -0.45]], 0.13, 0.92],
  ["shadow", [[0.30, -1.20], [0.70, -1.05], [1.00, -0.75], [1.20, -0.50]], 0.15, 0.90],
];
// The clumps for the parted cut (`Hairstyle.locks`): the bangs off the parting and, down each side, the
// one long lock in front of the shoulder, placed by hand on `harness/soft_hair/grid.py` at a fall of
// 2.62 (Katherina's) and re-stretched to the fall drawn the way `_long_traced_locks` is. Most of the
// crown sits under the hat in the presets that wear one, so the clumps are on the parts that show.
export const PARTED_LOCKS_FALL = 2.62;
export const PARTED_LOCKS: Lock[] = [
  ["lit", [[-0.15, -0.90], [-0.40, -0.60], [-0.60, -0.30], [-0.82, -0.05]], 0.12, 0.92],
  ["lit", [[-1.14, 0.15], [-1.15, 0.80], [-1.10, 1.50], [-0.98, 2.10]], 0.13, 0.95],
  ["shadow", [[-0.98, 0.20], [-0.98, 0.80], [-0.90, 1.50], [-0.78, 2.10]], 0.10, 0.92],
  ["shadow", [[0.15, -0.85], [0.40, -0.60], [0.60, -0.35], [0.80, -0.10]], 0.12, 0.90],
  ["lit", [[1.08, 0.15], [1.12, 0.80], [1.05, 1.50], [0.92, 2.00]], 0.13, 0.96],
  ["shadow", [[0.95, 0.20], [0.93, 0.80], [0.85, 1.50], [0.74, 2.00]], 0.10, 0.90],
];
// The parted cut (`docs/detail-status.md`, D5 plan).
//
// Traced off `ref-local/katherina_grok_nohat/`: `katherina_grok`, the reference
// `BODY_TYPES["tall_chibi"]` was measured off, redrawn with only the hair changed.
// So the body under the hair is ours and nothing below the chin is mapped, which
// is where the two traces of realistic references failed (the 2026-10-03 audit).
// It passed `harness/hair_audit/gate.py` and its hair segment is an exact cut of
// it; `harness/hair_parted/regions.py` and `trace.py` measure it in head radii on
// that check's calibration, 172.5 px per head radius, and `emit.py` writes the
// block between the markers below.
//
// The reference draws the hair in three layers and so does this cut: the mass,
// the whole silhouette, behind the body; the front, the crown, the fringe, the
// curtains and one lock a side down over the shoulder to a point near the belt,
// over the body; and between each lock and the outer fall, darker hair behind,
// beside the neck and in a strip that opens below the shoulder (the underside).
// Each lock's outer edge starts inside the hair beside the temple, not on the
// silhouette, so above it the curtain and the outer fall are one surface. The
// front is cut from it by a seam straight out from the edge's top to the
// silhouette: a fill boundary with no line, beside the skull, where no part of
// the body reaches at any height.
//
// Every chain was fitted at 0.012 head radii with no segment under two stroke
// widths (0.0854), the rule the crop and `long_traced` were cut by. Nothing is
// mirrored: the reference's right side stands 0.15 head radii further out.
// BEGIN parted trace (harness/hair_parted/emit.py)
// The silhouette, from the left outer fall's inner tip up the left side, over the crown and down to the right's.
export const PARTED_EDGE: Chain = [
  [-1.223, 2.804],
  [
    [[-1.281, 2.749], [-1.316, 2.694]],
    [[-1.369, 2.581], [-1.414, 2.468]],
    [[-1.444, 2.300], [-1.461, 2.132]],
    [[-1.461, 2.028], [-1.461, 1.923]],
    [[-1.540, 2.094], [-1.553, 2.294]],
    [[-1.553, 2.439], [-1.536, 2.584]],
    [[-1.600, 2.509], [-1.617, 2.404]],
    [[-1.628, 2.277], [-1.640, 2.149]],
    [[-1.633, 2.071], [-1.629, 1.993]],
    [[-1.595, 1.865], [-1.576, 1.738]],
    [[-1.500, 1.471], [-1.432, 1.205]],
    [[-1.411, 1.066], [-1.379, 0.926]],
    [[-1.359, 0.735], [-1.339, 0.544]],
    [[-1.343, 0.173], [-1.304, -0.198]],
    [[-1.287, -0.357], [-1.252, -0.517]],
    [[-1.212, -0.653], [-1.171, -0.789]],
    [[-1.134, -0.864], [-1.101, -0.940]],
    [[-1.029, -1.056], [-0.945, -1.172]],
    [[-0.872, -1.244], [-0.800, -1.316]],
    [[-0.652, -1.430], [-0.504, -1.502]],
    [[-0.397, -1.535], [-0.290, -1.566]],
    [[-0.235, -1.569], [-0.180, -1.577]],
    [[0.087, -1.584], [0.354, -1.566]],
    [[0.464, -1.536], [0.574, -1.496]],
    [[0.623, -1.468], [0.672, -1.444]],
    [[0.765, -1.385], [0.858, -1.305]],
    [[0.954, -1.205], [1.037, -1.114]],
    [[1.074, -1.047], [1.119, -0.980]],
    [[1.170, -0.861], [1.223, -0.743]],
    [[1.265, -0.606], [1.304, -0.470]],
    [[1.320, -0.346], [1.345, -0.221]],
    [[1.377, 0.185], [1.403, 0.590]],
    [[1.428, 0.709], [1.443, 0.828]],
    [[1.491, 1.048], [1.547, 1.268]],
    [[1.638, 1.532], [1.727, 1.796]],
    [[1.769, 1.976], [1.785, 2.155]],
    [[1.783, 2.274], [1.768, 2.393]],
    [[1.741, 2.465], [1.716, 2.538]],
    [[1.679, 2.481], [1.692, 2.184]],
    [[1.648, 2.045], [1.611, 1.906]],
    [[1.585, 1.831], [1.553, 1.784]],
    [[1.569, 1.941], [1.582, 2.097]],
    [[1.591, 2.251], [1.565, 2.404]],
    [[1.543, 2.457], [1.542, 2.509]],
    [[1.509, 2.590], [1.472, 2.671]],
    [[1.431, 2.752], [1.362, 2.804]],
  ],
];
// Which segments of `_PARTED_EDGE` end on the left seam's outer end, the crown's apex and the right seam's.
export const PARTED_SEAM_L = 13;
export const PARTED_CROWN_AT = 21;
export const PARTED_SEAM_R = 30;
// The lowest point of the trace, which `fall` scales against.
export const PARTED_BASE_TIP = 2.804;
// The hairline, from the left front lock's lowest tip up past the face and down to the right's.
export const PARTED_LINE: Chain = [
  [-0.707, 2.242],
  [
    [[-0.641, 2.096], [-0.672, 1.935]],
    [[-0.769, 1.384], [-0.852, 0.834]],
    [[-0.873, 0.596], [-0.893, 0.359]],
    [[-0.893, 0.182], [-0.893, 0.005]],
    [[-0.782, 0.054], [-0.591, -0.140]],
    [[-0.479, -0.244], [-0.383, -0.354]],
    [[-0.272, -0.499], [-0.185, -0.644]],
    [[-0.187, -0.528], [-0.226, -0.412]],
    [[-0.263, -0.302], [-0.319, -0.192]],
    [[-0.244, -0.218], [-0.185, -0.314]],
    [[-0.116, -0.421], [-0.064, -0.528]],
    [[-0.041, -0.595], [-0.012, -0.662]],
    [[0.015, -0.783], [0.046, -0.905]],
    [[0.094, -0.760], [0.162, -0.615]],
    [[0.242, -0.470], [0.365, -0.325]],
    [[0.432, -0.260], [0.498, -0.198]],
    [[0.563, -0.193], [0.452, -0.349]],
    [[0.414, -0.444], [0.371, -0.540]],
    [[0.415, -0.537], [0.487, -0.395]],
    [[0.559, -0.305], [0.632, -0.215]],
    [[0.747, -0.093], [0.858, 0.017]],
    [[0.911, 0.109], [0.893, 0.330]],
    [[0.881, 0.524], [0.869, 0.718]],
    [[0.843, 0.906], [0.823, 1.095]],
    [[0.766, 1.408], [0.713, 1.721]],
    [[0.698, 1.863], [0.701, 2.004]],
    [[0.714, 2.080], [0.736, 2.155]],
    [[0.755, 2.103], [0.742, 2.022]],
    [[0.791, 2.061], [0.806, 2.173]],
    [[0.830, 2.249], [0.893, 2.283]],
  ],
];
// The left front lock's outer edge, from the seam's inner end to its tip.
export const PARTED_LOCK_L: Chain = [
  [-1.113, -0.192],
  [
    [[-1.123, -0.050], [-1.130, 0.092]],
    [[-1.127, 0.330], [-1.124, 0.567]],
    [[-1.112, 0.840], [-1.090, 1.112]],
    [[-1.076, 1.303], [-1.049, 1.494]],
    [[-1.026, 1.605], [-1.003, 1.715]],
    [[-0.973, 1.805], [-0.939, 1.894]],
    [[-0.906, 1.955], [-0.875, 2.016]],
    [[-0.829, 2.017], [-0.910, 1.796]],
    [[-0.830, 1.878], [-0.759, 2.074]],
    [[-0.732, 2.158], [-0.707, 2.242]],
  ],
];
// The right front lock's outer edge, from the seam's inner end to its tip.
export const PARTED_LOCK_R: Chain = [
  [1.119, -0.221],
  [
    [[1.140, 0.217], [1.136, 0.654]],
    [[1.127, 0.802], [1.119, 0.950]],
    [[1.112, 1.051], [1.107, 1.153]],
    [[1.082, 1.422], [1.026, 1.692]],
    [[0.982, 1.831], [0.927, 1.970]],
    [[0.849, 2.090], [0.893, 2.283]],
  ],
];
// Which segment of each lock's edge ends where the dark strip opens beside it.
export const PARTED_APEX_L = 2;
export const PARTED_APEX_R = 1;
// The left outer fall's inner edge, from the dark strip's top to its tip.
export const PARTED_UNDER_L: Chain = [
  [-1.177, 1.112],
  [
    [[-1.221, 1.468], [-1.275, 1.825]],
    [[-1.288, 2.002], [-1.304, 2.178]],
    [[-1.305, 2.346], [-1.287, 2.515]],
    [[-1.249, 2.659], [-1.194, 2.804]],
  ],
];
// The right outer fall's inner edge, from the dark strip's top to its tip.
export const PARTED_UNDER_R: Chain = [
  [1.200, 0.944],
  [
    [[1.290, 1.555], [1.385, 2.167]],
    [[1.393, 2.300], [1.391, 2.433]],
    [[1.342, 2.626], [1.362, 2.804]],
  ],
];
// The outer falls' tips (`tips_find.py`), drawn with the mass: apex and direction.
export const PARTED_TIPS_BEHIND: [Point, Point][] = [
  [[-1.536, 2.584], [0.399, 0.917]],
  [[1.716, 2.538], [0.114, 0.994]],
  [[-1.223, 2.804], [0.555, 0.832]],
  [[1.362, 2.804], [-0.392, 0.920]],
];
// The front's tips, drawn with it: apex and direction.
export const PARTED_TIPS_FRONT: [Point, Point][] = [
  [[-0.319, -0.192], [-0.752, 0.659]],
  [[0.736, 2.155], [-0.030, 1.000]],
  [[-0.707, 2.242], [-0.068, 0.998]],
  [[0.893, 2.283], [0.604, 0.797]],
];
// END parted trace
// How far the underside's region runs up into the front's fill along the seam,
// so the two fill edges never land on the same pixels and leave a seam line.
export const PARTED_SEAM_LIFT = 0.03;
// `_LONG_TONE_LIFT` for this cut: how far above the mass's lower edge a two-tone
// head of hair turns, at the traced length.
export const PARTED_TONE_LIFT = 0.62;
// How far the two-tone edge is pushed out from the centre line before it is
// lifted (`_parted_tip_edge`).
export const PARTED_TONE_WIDEN = 1.15;
// Satoshi's traced crop.
//
// The outline here is not authored, it is measured. `out/trace/` pulls the canon's
// hair silhouette off `ref/satoshi-real.jpg` as a radius per bearing in head-radius
// units, simplifies it with Douglas-Peucker and least-squares fits one control
// point per span, which is exact for a quadratic with its endpoints pinned. So
// these numbers are the canon's own contour rather than anyone's idea of it, and
// the way to change them is to re-trace rather than to nudge.
//
// 26 segments because that is the finest level whose every edge is at least two
// stroke widths long. Below it the fit is more faithful on paper and worse on the
// page: `_stroke_w` is figure-relative, so a feature shorter than the line that
// draws it closes up, and no amount of rendering bigger helps. See
// `docs/gap-analysis.md` gap 1 and the PITFALLS entry in the gap-analysis skill.
//
// The contour is asymmetric because the canon's is. Nothing here mirrors, which
// the contract has always allowed and no cut had used.
export const CROP_START: Point = [-0.706, 0.872];
export const CROP_EDGE: Segment[] = [
  [[-0.751, 0.829], [-0.687, 0.687]],
  [[-0.837, 0.784], [-0.869, 0.756]],
  [[-0.798, 0.522], [-0.839, 0.428]],
  [[-1.071, 0.514], [-1.062, 0.473]],
  [[-0.938, 0.293], [-0.949, 0.202]],
  [[-0.984, 0.159], [-1.112, 0.117]],
  [[-1.009, 0.049], [-0.990, -0.000]],
  [[-1.105, -0.110], [-1.070, -0.227]],
  [[-1.040, -0.452], [-0.899, -0.630]],
  [[-1.119, -0.811], [-1.069, -0.805]],
  [[-0.886, -0.809], [-0.798, -0.856]],
  [[-0.596, -1.027], [-0.351, -1.149]],
  [[-0.200, -1.199], [-0.042, -1.189]],
  [[-0.003, -1.374], [0.045, -1.301]],
  [[0.238, -1.296], [0.360, -1.109]],
  [[0.551, -1.176], [0.707, -1.089]],
  [[0.780, -1.109], [0.714, -0.947]],
  [[0.900, -0.712], [1.172, -0.474]],
  [[1.213, -0.464], [1.011, -0.368]],
  [[1.018, -0.188], [1.152, -0.000]],
  [[1.233, 0.023], [0.989, 0.035]],
  [[0.949, 0.190], [1.092, 0.463]],
  [[1.124, 0.515], [0.890, 0.434]],
  [[0.839, 0.530], [0.907, 0.761]],
  [[0.902, 0.801], [0.727, 0.678]],
  [[0.797, 0.836], [0.724, 0.863]],
];
// Which segment ends on the crown's apex, so the two sides can be taken apart.
export const CROP_CROWN_AT = 13;
// Which segments end on the temple either side, where the fringe meets the
// silhouette. Both sit above the ear's top at 0.03, which is what leaves the ear
// somewhere to be seen; move them down and the front hair swallows it again.
export const CROP_TEMPLE_L = 7;
export const CROP_TEMPLE_R = 19;
// The lowest point of the trace as measured, which is what `fall` scales against:
// a cut whose tips reach `fall` is the trace at `fall / _CROP_BASE_TIP`.
export const CROP_BASE_TIP = 0.872;
// Satoshi's realistic-build crop, traced directly off `ref/satoshi-real.jpg`
// rather than the chibi trace above at `v` near 1. `_CROP_BASE_TIP` is
// calibrated so `v` already sits at 1.0002 at the realistic build, which
// means the chibi-traced crown was never actually being scaled there at
// all, just reused outright on a head with much less room for the same
// absolute shape, the same "hair rides the build and the crown does not"
// mismatch `STATUS.md` already had measured (crown-to-hairline band 1.035
// head radii at chibi, 0.683 at realistic, against a fixed fringe). Traced
// with `harness/trace/real/satoshi_real.py`, the same region-grown method
// `satoko_real.py` uses.
//
// The first version of this trace (2026-08-11) grew from one seed near the
// crown and stopped at both ears: the reference draws a separate sideburn
// tuft below each ear, a few small pointed locks with no hair-coloured
// pixels joining them to the crown mass, so a single seed's flood fill
// never reached them and the resulting silhouette simply stopped above the
// ears, leaving the jaw unframed. That read as worse than the chibi-scaled
// shape it replaced, which happened to reach nearly to the jaw already
// (its own trace goes to 0.86 head radii on the side against this one's
// 0.36), the wrong kind of "more faithful": faithful to the crown, wrong
// about how far the hair actually goes. Confirmed disconnected rather than
// assumed: a fresh flood fill seeded inside either tuft gives a blob a few
// hundred pixels wide, nothing like the ~14000-pixel main mass. Four more
// seeds, two per side, since each side's tuft is itself two separate blobs,
// fixed it; the trace now reaches the jaw on both sides, matching the
// reference and the chibi build, which already framed the head properly.
//
// `_CROP_REAL_TEMPLE_L/R` and `_CROP_REAL_CROWN_AT` are this trace's own
// version of `_CROP_TEMPLE_L/R`/`_CROP_CROWN_AT`, picked by the same rule
// those were, the segment ending just above the ear and the one ending
// nearest the crown's own centre: the index numbers do not carry over,
// since this list is 42 segments long against the chibi trace's 26, most
// of the extra length being the two sideburn tufts this trace did not use
// to carry at all.
export const CROP_REAL_START: Point = [-0.411, 0.968];
export const CROP_REAL_EDGE: Segment[] = [
  [[-0.429, 0.963], [-0.436, 0.935]],
  [[-0.455, 0.935], [-0.498, 0.977]],
  [[-0.517, 0.870], [-0.548, 0.812]],
  [[-0.581, 0.845], [-0.615, 0.878]],
  [[-0.633, 0.790], [-0.648, 0.719]],
  [[-0.684, 0.735], [-0.745, 0.771]],
  [[-0.714, 0.550], [-0.747, 0.449]],
  [[-0.859, 0.414], [-0.895, 0.326]],
  [[-0.965, 0.341], [-1.036, 0.357]],
  [[-0.993, 0.196], [-0.998, 0.070]],
  [[-1.046, 0.064], [-1.094, 0.057]],
  [[-1.012, -0.066], [-1.016, -0.179]],
  [[-1.176, -0.228], [-1.123, -0.239]],
  [[-1.099, -0.377], [-1.050, -0.512]],
  [[-0.994, -0.609], [-0.926, -0.698]],
  [[-0.990, -0.760], [-1.053, -0.823]],
  [[-0.898, -0.845], [-0.814, -0.904]],
  [[-0.634, -1.072], [-0.404, -1.172]],
  [[-0.288, -1.201], [-0.171, -1.216]],
  [[-0.072, -1.202], [0.021, -1.184]],
  [[0.033, -1.246], [0.046, -1.307]],
  [[0.102, -1.283], [0.154, -1.255]],
  [[0.223, -1.186], [0.277, -1.110]],
  [[0.323, -1.132], [0.375, -1.153]],
  [[0.468, -1.163], [0.554, -1.136]],
  [[0.537, -1.078], [0.519, -1.019]],
  [[0.653, -0.969], [0.751, -0.863]],
  [[0.848, -0.661], [1.009, -0.514]],
  [[0.952, -0.475], [0.895, -0.437]],
  [[0.926, -0.268], [0.998, -0.105]],
  [[1.052, -0.091], [0.882, -0.062]],
  [[0.862, 0.115], [0.930, 0.357]],
  [[0.850, 0.392], [0.770, 0.427]],
  [[0.756, 0.513], [0.757, 0.635]],
  [[0.691, 0.589], [0.625, 0.543]],
  [[0.594, 0.595], [0.635, 0.757]],
  [[0.631, 0.795], [0.534, 0.709]],
  [[0.516, 0.772], [0.504, 0.873]],
  [[0.478, 0.865], [0.432, 0.812]],
  [[0.402, 0.856], [0.388, 0.961]],
  [[0.380, 0.992], [0.337, 0.925]],
  [[0.318, 0.948], [0.299, 0.979]],
];
// The two sideburn tufts sit close enough to the skull's own jaw/cheek
// edge that at `_CROP_REAL_SCALE` alone, most of each tuft lands behind
// the head shape drawn over it rather than past it: checked directly
// against `_head_edge_x`, several of the tuft's own points sit inside the
// skull's edge, not outside it, and several more clear it by only a few
// hundredths of a head radius, thin enough that the tuft still reads as a
// broken scribble rather than visible hair. This is the same "clear the
// skull" problem `_EAR_OUT` already exists to solve for the ear, and it
// gets the same kind of fix: an outward push, x only, since y is already
// the tuft's own measured reach and does not need moving. The ranges are
// this trace's own two tufts and stop exactly where each one already
// cleared the skull on its own: edge indices 0-7 (left) and 32-41
// (right); `_CROP_REAL_START` is the left tuft's own tip, pushed the same
// way.
//
// Pushing every point in those ranges the same amount overshot in one
// direction and undershot in another. `_ears` draws only the sliver
// standing clear of the skull, from the skull's own edge out to
// `_EAR_OUT` past it, within `_EAR_TOP_Y` to `_EAR_BOT_Y`; checked
// directly at the realistic build, the only build this trace ever runs
// at, that sliver spans about `_CROP_REAL_EAR_X` in head radii. A first
// pass read the tangle at that height as hair and ear fighting over the
// same pixels and pulled the hair back to the skull's own edge there,
// which cleared the tangle but was the wrong read of the reference: the
// canon does not leave the ear in a clean skin-only window, it runs the
// hair on past the ear, behind it, and the ear sits in front of that,
// poking out of a continuous mass rather than out of a gap in one. Pulled
// back to the skull, the mass could not do that, and read as thinner at
// the ear than anywhere else on the tuft instead of continuous through
// it. So at ear height the mass now pushes *out*, past the ear's own
// outer edge with a margin (`_CROP_REAL_EAR_MARGIN`, picked by rendering
// 0 to 0.2 and reading the results, not calculated), rather than back to
// the skull: far enough that the ear's own fill fully covers the seam
// between them, so the ear reads as sitting on top of the hair instead of
// next to a gap in it. Everywhere else in the two ranges the push is
// still the simple outward scale.
export const CROP_REAL_SIDEBURN_PUSH = 1.3;
// -1 stands for `_CROP_REAL_START` itself, the left tuft's own tip.
/** A Python `range(start, stop)`. */
export interface PyRange {
  readonly start: number;
  readonly stop: number;
}
/** `i in range(...)` for an int `i`. */
export const inRange = (i: number, r: PyRange): boolean => r.start <= i && i < r.stop;
export const CROP_REAL_SIDEBURN_L: PyRange = { start: -1, stop: 8 };
export const CROP_REAL_SIDEBURN_R: PyRange = { start: 32, stop: 42 };
export const CROP_REAL_EAR_X = [0.717, 0.967];
export const CROP_REAL_EAR_MARGIN = 0.1;
// The push to the floor is a big jump for a point that was not already
// close to it, and applying it only exactly within `_EAR_TOP_Y`/
// `_EAR_BOT_Y` left one such jump right at the boundary on the right
// side: the last unpushed point above the ear stood at 0.886, the first
// pushed one immediately below it at 1.072, and that one segment's own
// curve folded back on itself, which is a self-crossing path, not a
// rounding error, and left a small hole of bare canvas exactly at the
// fold. `_CROP_REAL_EAR_BUFFER` extends the floor a little above and
// below the ear's own height, so the point that used to make that jump
// now gets pushed too and the step disappears; picked as the smallest
// buffer that rendered with no such hole on either side, checked at 4x.
export const CROP_REAL_EAR_BUFFER = 0.1;
export const CROP_REAL_TEMPLE_L = 10;
export const CROP_REAL_TEMPLE_R = 29;
export const CROP_REAL_CROWN_AT = 20;
// The `fall` this trace was measured at: Satoshi's own `hair_length=0.65` (the
// range's neutral value, the length the crop was traced at in the first
// place) run through the realistic build's chin-hip span. `fall` already
// folds build and hair_length together, so this is only valid at the
// specific silhouette it was read off. Tomohiro shares it unchanged.
export const CROP_REAL_FALL = 0.87215;
export const CROP_REAL_TOL = 0.01;
// Scaled up from the head centre: a silhouette sized exactly to the
// reference reads thin next to a chibi's generous hair, and the shape that
// fixed the crown-vs-fringe mismatch is worth keeping at a bigger size
// rather than re-measuring bigger. Capped
// under where the crown's own apex (1.307 head radii here) would cross
// `build_skeleton`'s realistic-build hair ceiling of 1.36. That ceiling
// bounds all hair ink, the outline stroke's outer half included (see
// `hair_margin`'s own comment), and `_stroke_w` at the realistic build is
// 0.058 head radii, so the apex has only 1.36 - 0.029 = 1.331 to clear
// rather than the full 1.36: 1.331 / 1.307 is about 1.018, tighter headroom
// than Satoko's trace had. An earlier version of this comment compared
// against the full 1.36 and read 1.04, and 1.03 sat here on that basis, past
// the true limit; it painted a few antialiased pixels into row 0 of the
// exported canvas. 1.005 clears it (checked by rendering and reading the
// PNG's own top row back, not by the math alone: antialiasing bleeds the
// stroke a pixel or so past its analytic centre, so the margin computed
// above still isn't quite enough on its own).
export const CROP_REAL_SCALE = 1.005;
// The fringe, traced off `ref/satoshi-chibi-fringe.png`: the canon's fringe cut
// out of the chibi reference by the owner, background removed.
//
// That crop is what made this measurable. Five readings off the full drawing all
// failed and each failed differently, because the canon's pale tips sit
// colorimetrically between its gold and its skin, so no threshold puts all three
// on the right side of it. What the crop changes is not its alpha, which is a
// coarse outer selection with the gaps between blades left opaque, but what it
// leaves out: no brows and no eyes. On the full drawing the deepest ink in a
// column is the brow, which is why reading the drawn line found eyebrows. In the
// crop the deepest ink can only be the blade that made it.
//
// The crop is placed back in the reference by template match rather than by an
// eyeballed offset, and matches to a mean squared error of 1, so the calibration
// is the reference's own. `out/trace/fringe3.py` carries it.
//
// Fixed rather than scaled by the build: the mass grows and the fringe does not,
// because it sits on a brow that has not moved.
export const CROP_FRINGE_START: Point = [-1.039, -0.181];
export const CROP_FRINGE: Segment[] = [
  [[-0.924, -0.200], [-0.817, -0.215]],
  [[-0.741, -0.290], [-0.641, -0.356]],
  [[-0.641, -0.237], [-0.624, -0.237]],
  [[-0.435, -0.272], [-0.278, -0.385]],
  [[-0.275, -0.288], [-0.272, -0.192]],
  [[-0.080, -0.219], [0.068, -0.351]],
  [[0.068, -0.249], [0.080, -0.249]],
  [[0.193, -0.291], [0.289, -0.374]],
  [[0.397, -0.477], [0.448, -0.618]],
  [[0.512, -0.439], [0.653, -0.311]],
  [[0.711, -0.271], [0.772, -0.237]],
  [[0.783, -0.237], [0.783, -0.356]],
  [[0.812, -0.328], [0.840, -0.300]],
  [[0.885, -0.215], [0.885, -0.112]],
  [[0.919, -0.112], [0.919, -0.243]],
  [[0.985, -0.204], [1.061, -0.186]],
];
export const CROP_NOTCHES: Point[] = [
  [-0.641, -0.356],
  [-0.278, -0.385],
  [0.068, -0.351],
  [0.448, -0.618],
  [0.783, -0.356],
  [0.919, -0.243],
];
// How far inside the silhouette the front hair's own fill boundary is pulled,
// in fractions of the radius. It only ever has to be enough that the fill cannot
// cross the outline between two traced points; the mass paints the strip left
// over in the same colour, so nothing shows.
export const CROP_FILL_INSET = 0.06;
// How far above the fringe's own edge the gold gives way to the pale tips, in
// head radii. The blades run about 0.5 from notch to tip, so this is roughly how
// much of each blade comes out pale.
//
// **0.26 is the design, not an approximation of the reference.** It was cut to
// 0.14 on 2026-08-09 to bring it closer to `ref/satoshi.png`, which shows gold
// nearly to the tips, and the owner reversed that the same day: at 0.14 the white
// on his fringe is barely noticeable, and the wider split reads better. So this
// is one of the places the reference is deliberately not the target, and the
// standing rule applies, that the references are guides and the final call is by
// eye. Do not "correct" it toward the canon again.
//
// It is also the only thing that sets his boundary. Sweeping `_HAIR_FADE` across
// its whole range leaves his fringe byte-identical, because the lifted edge
// already sits below the level line and so wins; Satoko is the mirror image,
// untouched by this and set entirely by the clamp. The two cuts are independent
// here, which is why his could be put back without moving her.
export const CROP_TONE_LIFT = 0.26;
// How far the lock divisions lean off vertical, and how far they run up from
// their notch. Short: a division marks a join, it does not have to travel, and
// full-length ones hang off the fringe as a curtain of needles.
export const CROP_SWEEP = 0.06;
export const CROP_STRAND_RUN = 0.34;
// Satoshi's tousled crop.
//
// Built from its locks rather than from an outline with texture drawn on it,
// which is what the other two cuts are. The canon crop is a bundle of pointed
// locks, each gold at the root and pale toward its own tip, and the difference
// that makes is structural rather than decorative: one tone boundary running
// level across a whole head can only say "pale below this height", so a cut whose
// locks point in different directions comes out with a band painted across it.
// `tip_edge` returning a region per lock is what this cut needs and what it is
// for.
//
// The fringe is one list of points used three ways: the hairline chains through
// it, the pale wedges are cut from it, and the strand lines aim at its notches.
// Spelling those out separately is what let the old cut's lines drift off its
// own locks.
export const TOUSLE_NOTCHES: Point[] = [
  [-0.98, -0.30],
  [-0.78, -0.52],
  [-0.50, -0.70],
  [-0.16, -0.76],
  [0.20, -0.70],
  [0.56, -0.58],
  [0.86, -0.40],
  [0.98, -0.30],
];
// One per gap in the list above. Deliberately uneven in width, length and
// direction: a row of equal points is a comb. The canon's fringe is longest at
// the temples and shortest either side of the parting, which sits right of
// centre, and its notches cut most of the way back up the forehead, so each lock
// is a blade with dark either side of it rather than a tooth on a band.
export const TOUSLE_TIPS: Point[] = [
  [-0.90, -0.04],
  [-0.64, -0.20],
  [-0.33, -0.40],
  [0.02, -0.34],
  [0.38, -0.26],
  [0.72, -0.14],
  [0.92, 0.00],
];
// Where the crown meets the side, and how far out the temple spike flicks. The
// canon crop is widest here, at the temples, and narrows below; the cut it
// replaces was widest at the bottom of its mass, because that mass was a circle.
export const TOUSLE_TEMPLE: Point = [1.18, -0.46];
// The crown, as the lock tips and the notches between them, each a bearing in
// degrees clockwise from straight up and a radius in head radii. Tips stand out
// at 1.28 to 1.40, notches cut back to 1.10 to 1.18, and the run is walked with
// straight lines, so every tip is a corner rather than the top of an arc.
//
// That distinction is the whole of what was learned from the reverted attempt.
// Bumps added *onto* a circular crown read as wobble, because a circle with a
// lump on it is a circle with a lump on it however the lump is drawn. A silhouette
// that is nothing but tips and notches has no circle left in it to spoil.
//
// The cowlick is the 20-degree mark, thin because its notches sit close either
// side of it, and tall enough to clear the rest by 0.10 head radii but no more:
// `test_hair_stays_under_the_canvas_ceiling` is about 0.01 away at this height.
export const TOUSLE_CROWN: [number, number][] = [
  [-70.0, 1.24],
  [-58.0, 1.12],
  [-40.0, 1.20],
  [-20.0, 1.24],
  [-4.0, 1.26],
  [10.0, 1.14],
  [18.0, 1.36],
  [25.0, 1.08],
  [35.0, 1.28],
  [46.0, 1.06],
  [60.0, 1.18],
];
// BEGIN fringed trace
// Traced by `harness/risa/trace_hair.py` off `segments/long-black-hair.png` and
// `segments/bangs.png` (`docs/risa-plan.md`, M8). Head radii on the figure's own head, x
// from its centre line, so a cut is the same hair on any body; `_fringed_q` stretches
// the part below the cheek line to `hair_length`.
export const FRINGED_BASE_TIP = 3.441;
// The hair in front: the fringe, the face opening and the two long curtains of locks as
// one closed outline, the stroke's centre line.
export const FRINGED_FRONT: Chain = [
  [0.164, -1.475],
  [
    [[0.271, -1.462], [0.378, -1.445]],
    [[0.453, -1.421], [0.528, -1.391]],
    [[0.595, -1.362], [0.663, -1.322]],
    [[0.756, -1.256], [0.848, -1.182]],
    [[0.932, -1.088], [1.007, -0.991]],
    [[1.050, -0.923], [1.088, -0.855]],
    [[1.158, -0.709], [1.200, -0.563]],
    [[1.251, -0.313], [1.261, -0.064]],
    [[1.262, 0.328], [1.262, 0.721]],
    [[1.277, 1.031], [1.306, 1.341]],
    [[1.398, 1.940], [1.531, 2.539]],
    [[1.561, 2.728], [1.575, 2.917]],
    [[1.580, 3.013], [1.568, 3.109]],
    [[1.553, 3.245], [1.516, 3.380]],
    [[1.511, 3.399], [1.500, 3.408]],
    [[1.483, 3.416], [1.480, 3.399]],
    [[1.498, 3.282], [1.511, 3.159]],
    [[1.507, 3.095], [1.501, 3.031]],
    [[1.497, 2.991], [1.478, 2.952]],
    [[1.460, 2.922], [1.434, 2.921]],
    [[1.397, 2.946], [1.395, 2.995]],
    [[1.369, 3.222], [1.315, 3.441]],
    [[1.302, 3.456], [1.279, 3.427]],
    [[1.279, 3.325], [1.250, 3.216]],
    [[1.233, 3.173], [1.211, 3.131]],
    [[1.190, 3.045], [1.178, 2.959]],
    [[1.116, 2.296], [1.046, 1.633]],
    [[1.020, 1.530], [0.962, 1.438]],
    [[0.934, 1.410], [0.906, 1.420]],
    [[0.875, 1.441], [0.872, 1.476]],
    [[0.860, 1.630], [0.842, 1.783]],
    [[0.832, 2.061], [0.833, 2.339]],
    [[0.828, 2.453], [0.798, 2.567]],
    [[0.784, 2.628], [0.749, 2.675]],
    [[0.742, 2.648], [0.705, 2.586]],
    [[0.643, 2.630], [0.633, 2.666]],
    [[0.649, 2.103], [0.691, 1.519]],
    [[0.686, 1.487], [0.679, 1.455]],
    [[0.691, 1.419], [0.705, 1.384]],
    [[0.736, 1.002], [0.798, 0.621]],
    [[0.801, 0.589], [0.795, 0.557]],
    [[0.768, 0.524], [0.758, 0.492]],
    [[0.773, 0.453], [0.790, 0.414]],
    [[0.817, 0.218], [0.824, 0.022]],
    [[0.813, -0.012], [0.777, -0.039]],
    [[0.706, -0.064], [0.635, -0.107]],
    [[0.548, -0.104], [0.465, -0.115]],
    [[0.429, -0.205], [0.371, -0.288]],
    [[0.348, -0.288], [0.340, -0.263]],
    [[0.347, -0.187], [0.336, -0.129]],
    [[0.313, -0.156], [0.250, -0.223]],
    [[0.210, -0.239], [0.171, -0.238]],
    [[0.144, -0.240], [0.127, -0.213]],
    [[0.116, -0.140], [0.107, -0.127]],
    [[0.046, -0.227], [0.009, -0.342]],
    [[-0.056, -0.559], [-0.073, -0.777]],
    [[-0.078, -0.801], [-0.100, -0.806]],
    [[-0.128, -0.797], [-0.138, -0.763]],
    [[-0.160, -0.673], [-0.186, -0.584]],
    [[-0.227, -0.346], [-0.237, -0.142]],
    [[-0.236, -0.200], [-0.258, -0.292]],
    [[-0.264, -0.316], [-0.285, -0.317]],
    [[-0.306, -0.309], [-0.314, -0.285]],
    [[-0.333, -0.189], [-0.361, -0.103]],
    [[-0.406, -0.080], [-0.453, -0.112]],
    [[-0.471, -0.136], [-0.474, -0.171]],
    [[-0.475, -0.267], [-0.480, -0.363]],
    [[-0.485, -0.388], [-0.506, -0.388]],
    [[-0.524, -0.383], [-0.531, -0.363]],
    [[-0.551, -0.234], [-0.589, -0.108]],
    [[-0.664, -0.058], [-0.749, -0.045]],
    [[-0.789, -0.017], [-0.825, 0.015]],
    [[-0.843, 0.036], [-0.846, 0.057]],
    [[-0.816, 0.286], [-0.745, 0.513]],
    [[-0.757, 0.546], [-0.781, 0.585]],
    [[-0.786, 0.621], [-0.784, 0.656]],
    [[-0.741, 1.020], [-0.705, 1.384]],
    [[-0.693, 1.419], [-0.679, 1.455]],
    [[-0.687, 1.501], [-0.699, 1.548]],
    [[-0.687, 1.929], [-0.691, 2.311]],
    [[-0.683, 2.457], [-0.662, 2.603]],
    [[-0.624, 2.661], [-0.622, 2.715]],
    [[-0.626, 2.729], [-0.643, 2.724]],
    [[-0.700, 2.696], [-0.752, 2.684]],
    [[-0.798, 2.616], [-0.815, 2.539]],
    [[-0.843, 2.029], [-0.872, 1.519]],
    [[-0.873, 1.481], [-0.900, 1.451]],
    [[-0.923, 1.434], [-0.948, 1.457]],
    [[-0.981, 1.529], [-1.009, 1.605]],
    [[-1.028, 1.694], [-1.039, 1.783]],
    [[-1.095, 2.457], [-1.183, 3.131]],
    [[-1.230, 3.253], [-1.251, 3.284]],
    [[-1.278, 3.236], [-1.289, 3.180]],
    [[-1.316, 3.006], [-1.328, 2.831]],
    [[-1.332, 2.812], [-1.348, 2.803]],
    [[-1.362, 2.799], [-1.373, 2.812]],
    [[-1.400, 2.848], [-1.406, 2.888]],
    [[-1.414, 2.970], [-1.425, 3.052]],
    [[-1.429, 3.148], [-1.429, 3.245]],
    [[-1.422, 3.302], [-1.409, 3.359]],
    [[-1.410, 3.389], [-1.427, 3.390]],
    [[-1.478, 3.327], [-1.488, 3.237]],
    [[-1.513, 3.059], [-1.504, 2.881]],
    [[-1.489, 2.731], [-1.466, 2.581]],
    [[-1.376, 2.139], [-1.281, 1.697]],
    [[-1.253, 1.537], [-1.235, 1.377]],
    [[-1.214, 1.098], [-1.205, 0.820]],
    [[-1.236, 0.318], [-1.233, -0.185]],
    [[-1.223, -0.324], [-1.196, -0.463]],
    [[-1.164, -0.591], [-1.121, -0.720]],
    [[-1.068, -0.827], [-1.008, -0.934]],
    [[-0.918, -1.041], [-0.844, -1.147]],
    [[-0.752, -1.241], [-0.649, -1.302]],
    [[-0.471, -1.399], [-0.292, -1.446]],
    [[-0.182, -1.464], [-0.071, -1.475]],
    [[0.046, -1.476], [0.164, -1.475]],
  ],
];
// The silhouette behind the body: the same outline with the gap between the curtains
// closed across, below the chin, where the blazer hides it.
export const FRINGED_MASS: Chain = [
  [0.157, -1.475],
  [
    [[0.267, -1.463], [0.378, -1.445]],
    [[0.453, -1.421], [0.528, -1.391]],
    [[0.684, -1.322], [0.841, -1.188]],
    [[0.977, -1.046], [1.064, -0.898]],
    [[1.154, -0.730], [1.200, -0.563]],
    [[1.251, -0.313], [1.261, -0.064]],
    [[1.262, 0.328], [1.262, 0.721]],
    [[1.277, 1.031], [1.306, 1.341]],
    [[1.398, 1.940], [1.531, 2.539]],
    [[1.561, 2.728], [1.575, 2.917]],
    [[1.580, 3.013], [1.568, 3.109]],
    [[1.553, 3.245], [1.516, 3.380]],
    [[1.511, 3.399], [1.500, 3.408]],
    [[1.483, 3.416], [1.480, 3.399]],
    [[1.498, 3.282], [1.511, 3.159]],
    [[1.507, 3.095], [1.501, 3.031]],
    [[1.497, 2.995], [1.482, 2.959]],
    [[1.467, 2.930], [1.440, 2.921]],
    [[1.406, 2.927], [1.402, 2.967]],
    [[1.369, 3.221], [1.311, 3.447]],
    [[1.293, 3.447], [1.279, 3.427]],
    [[1.279, 3.314], [1.244, 3.195]],
    [[1.230, 3.166], [1.198, 3.167]],
    [[0.014, 3.166], [-1.169, 3.167]],
    [[-1.196, 3.166], [-1.211, 3.189]],
    [[-1.231, 3.259], [-1.246, 3.291]],
    [[-1.275, 3.248], [-1.289, 3.180]],
    [[-1.316, 3.006], [-1.328, 2.831]],
    [[-1.333, 2.806], [-1.355, 2.802]],
    [[-1.407, 2.840], [-1.410, 2.909]],
    [[-1.421, 3.020], [-1.430, 3.131]],
    [[-1.434, 3.245], [-1.409, 3.359]],
    [[-1.410, 3.389], [-1.427, 3.390]],
    [[-1.478, 3.327], [-1.488, 3.237]],
    [[-1.513, 3.059], [-1.504, 2.881]],
    [[-1.375, 2.129], [-1.235, 1.377]],
    [[-1.214, 1.098], [-1.205, 0.820]],
    [[-1.236, 0.318], [-1.233, -0.185]],
    [[-1.223, -0.324], [-1.196, -0.463]],
    [[-1.164, -0.591], [-1.121, -0.720]],
    [[-1.068, -0.827], [-1.008, -0.934]],
    [[-0.918, -1.041], [-0.844, -1.147]],
    [[-0.752, -1.241], [-0.649, -1.302]],
    [[-0.471, -1.399], [-0.292, -1.446]],
    [[-0.068, -1.486], [0.157, -1.475]],
  ],
];
// The hair behind the neck, in the second tone: where the mass shows between the two
// curtains below the cheek. The flaps hang from the curtains' inner edges, behind the
// blazer, so they are the mass's and not the front's.
export const FRINGED_UNDERSIDE: Chain = [
  [-0.813, 0.243],
  [
    [[-0.774, 0.799], [-0.734, 1.355]],
    [[-0.734, 2.261], [-0.734, 3.166]],
    [[0.000, 3.166], [0.734, 3.166]],
    [[0.734, 2.261], [0.734, 1.355]],
    [[0.774, 0.799], [0.813, 0.243]],
    [[0.000, 0.243], [-0.813, 0.243]],
  ],
];
// The strokes that part the hair into locks, open chains.
export const FRINGED_STRANDS: Chain[] = [
  [
    [-0.991, -0.627],
    [
      [[-1.012, -0.559], [-1.027, -0.492]],
    ],
  ],
  [
    [-1.041, -0.427],
    [
      [[-1.073, -0.256], [-1.084, -0.085]],
      [[-1.084, -0.042], [-1.084, 0.000]],
      [[-1.055, 0.093], [-1.041, 0.186]],
    ],
  ],
  [
    [-0.984, 0.207],
    [
      [[-0.968, 0.254], [-0.948, 0.300]],
    ],
  ],
  [
    [-0.963, 0.778],
    [
      [[-0.935, 1.020], [-0.927, 1.262]],
    ],
  ],
  [
    [-0.791, -0.527],
    [
      [[-0.817, -0.395], [-0.834, -0.263]],
      [[-0.829, -0.139], [-0.841, -0.014]],
    ],
  ],
  [
    [-0.713, -0.449],
    [
      [[-0.728, -0.413], [-0.734, -0.378]],
      [[-0.746, -0.274], [-0.749, -0.171]],
    ],
  ],
  [
    [-0.770, -0.128],
    [
      [[-0.776, -0.090], [-0.788, 0.000]],
    ],
  ],
  [
    [-0.791, 2.311],
    [
      [[-0.789, 2.418], [-0.777, 2.524]],
    ],
  ],
  [
    [-0.449, -0.656],
    [
      [[-0.452, -0.620], [-0.502, -0.430]],
    ],
  ],
  [
    [-0.478, -0.484],
    [
      [[-0.476, -0.438], [-0.471, -0.392]],
    ],
  ],
  [
    [-0.250, -0.606],
    [
      [[-0.255, -0.556], [-0.264, -0.506]],
    ],
  ],
  [
    [-0.278, -0.484],
    [
      [[-0.299, -0.424], [-0.314, -0.363]],
    ],
  ],
  [
    [-0.257, -0.484],
    [
      [[-0.259, -0.402], [-0.250, -0.320]],
    ],
  ],
  [
    [-0.064, -1.119],
    [
      [[-0.084, -1.023], [-0.086, -0.927]],
    ],
  ],
  [
    [0.057, -0.812],
    [
      [[0.062, -0.755], [0.071, -0.698]],
    ],
  ],
  [
    [0.271, -0.656],
    [
      [[0.303, -0.552], [0.321, -0.449]],
    ],
  ],
  [
    [0.321, -0.385],
    [
      [[0.335, -0.328], [0.321, -0.271]],
    ],
  ],
  [
    [0.456, -0.827],
    [
      [[0.498, -0.716], [0.528, -0.606]],
      [[0.553, -0.467], [0.578, -0.328]],
    ],
  ],
  [
    [0.642, -0.969],
    [
      [[0.659, -0.909], [0.699, -0.848]],
    ],
  ],
  [
    [0.742, -0.698],
    [
      [[0.774, -0.570], [0.791, -0.442]],
      [[0.798, -0.331], [0.799, -0.221]],
    ],
  ],
  [
    [0.813, -0.199],
    [
      [[0.813, -0.132], [0.813, -0.064]],
    ],
  ],
  [
    [0.706, 2.239],
    [
      [[0.709, 2.353], [0.706, 2.467]],
    ],
  ],
  [
    [0.927, -0.777],
    [
      [[0.960, -0.705], [0.977, -0.634]],
    ],
  ],
  [
    [1.012, -0.484],
    [
      [[1.040, -0.274], [1.055, -0.064]],
    ],
  ],
  [
    [1.048, -0.035],
    [
      [[1.046, 0.079], [1.020, 0.193]],
    ],
  ],
  [
    [0.970, 0.856],
    [
      [[0.963, 0.963], [0.955, 1.070]],
    ],
  ],
  [
    [0.970, 1.091],
    [
      [[0.975, 1.270], [1.005, 1.448]],
    ],
  ],
  [
    [1.362, 2.318],
    [
      [[1.401, 2.492], [1.419, 2.667]],
    ],
  ],
];
// The patches of skin showing through the hair: an ear at each side and a gap in the fringe.
export const FRINGED_OPENINGS: Chain[] = [
  [
    [-1.005, 0.549],
    [
      [[-1.027, 0.528], [-1.048, 0.507]],
      [[-1.067, 0.453], [-1.084, 0.400]],
      [[-1.084, 0.360], [-1.084, 0.321]],
      [[-1.072, 0.286], [-1.041, 0.250]],
      [[-1.027, 0.252], [-1.012, 0.271]],
      [[-1.001, 0.307], [-0.991, 0.343]],
      [[-0.992, 0.432], [-0.984, 0.521]],
      [[-0.991, 0.535], [-1.005, 0.549]],
    ],
  ],
  [
    [1.027, 0.542],
    [
      [[1.013, 0.528], [1.005, 0.514]],
      [[1.011, 0.435], [1.005, 0.357]],
      [[1.012, 0.321], [1.020, 0.286]],
      [[1.011, 0.268], [1.012, 0.250]],
      [[1.023, 0.239], [1.034, 0.229]],
      [[1.048, 0.229], [1.062, 0.229]],
      [[1.078, 0.246], [1.084, 0.264]],
      [[1.093, 0.314], [1.098, 0.364]],
      [[1.086, 0.400], [1.084, 0.435]],
      [[1.057, 0.489], [1.027, 0.542]],
    ],
  ],
];
// The darker hair behind, where it shows in front: regions painted in the second tone.
export const FRINGED_SHADE: Chain[] = [
  [
    [-0.877, 0.421],
    [
      [[-0.808, 0.461], [-0.756, 0.535]],
      [[-0.761, 0.674], [-0.734, 0.813]],
      [[-0.724, 0.852], [-0.756, 0.892]],
      [[-0.792, 0.899], [-0.813, 0.856]],
      [[-0.848, 0.681], [-0.906, 0.507]],
      [[-0.909, 0.482], [-0.913, 0.457]],
      [[-0.901, 0.433], [-0.877, 0.421]],
    ],
  ],
  [
    [0.863, 0.435],
    [
      [[0.887, 0.447], [0.898, 0.471]],
      [[0.895, 0.503], [0.891, 0.535]],
      [[0.847, 0.685], [0.813, 0.835]],
      [[0.792, 0.877], [0.756, 0.870]],
      [[0.727, 0.842], [0.734, 0.813]],
      [[0.767, 0.663], [0.770, 0.514]],
      [[0.808, 0.452], [0.863, 0.435]],
    ],
  ],
  [
    [-1.184, 3.159],
    [
      [[-1.209, 3.134], [-1.226, 3.109]],
      [[-1.232, 3.034], [-1.248, 2.959]],
      [[-1.258, 2.753], [-1.248, 2.546]],
      [[-1.173, 1.954], [-1.070, 1.362]],
      [[-1.027, 0.974], [-1.027, 0.585]],
      [[-1.002, 0.570], [-0.977, 0.557]],
      [[-0.911, 0.988], [-0.870, 1.419]],
      [[-0.897, 1.456], [-0.941, 1.483]],
      [[-0.955, 1.558], [-0.991, 1.633]],
      [[-1.060, 2.196], [-1.098, 2.760]],
      [[-1.133, 2.934], [-1.148, 3.109]],
      [[-1.155, 3.143], [-1.184, 3.159]],
    ],
  ],
  [
    [1.269, 3.223],
    [
      [[1.214, 3.215], [1.184, 3.145]],
      [[1.168, 3.056], [1.148, 2.967]],
      [[1.089, 2.278], [1.012, 1.590]],
      [[0.968, 1.526], [0.955, 1.462]],
      [[0.920, 1.441], [0.884, 1.405]],
      [[0.936, 0.988], [0.970, 0.571]],
      [[0.975, 0.553], [0.991, 0.535]],
      [[1.009, 0.553], [1.027, 0.571]],
      [[1.048, 0.549], [1.070, 0.528]],
      [[1.080, 0.527], [1.091, 0.542]],
      [[1.100, 0.938], [1.141, 1.334]],
      [[1.231, 1.933], [1.305, 2.532]],
      [[1.321, 2.788], [1.312, 3.045]],
      [[1.314, 3.134], [1.269, 3.223]],
    ],
  ],
];
// The clumps the soft finish lays over Risa's front hair (`Hairstyle.locks`), placed by hand on
// `harness/soft_hair/grid.py`'s grid of the traced pieces and judged in the owner's blind pairs
// (`docs/soft-hair-status.md`). Left to right across the fringe, then the two outer falls and the
// two curtains; the base-tone clumps and the two outermost, which hugged the contour and read as a
// seam, are not drawn. The widths and lengths carry a fixed variation so they are not a comb.
export const FRINGED_LOCKS: Lock[] = [
  ["lit", [[-0.14, -1.46], [-0.36, -1.15], [-0.5, -0.7], [-0.56, -0.27]], 0.212, 0.99],
  ["shadow", [[-0.18, -1.42], [-0.56, -1.22], [-0.8, -0.82], [-0.88, -0.3], [-0.85, 0.06]], 0.172, 0.88],
  ["lit", [[-0.3, -1.48], [-0.68, -1.3], [-0.94, -0.9], [-1.05, -0.3], [-1.1, 0.5], [-1.12, 1.3], [-1.2, 2.2], [-1.28, 3.0]], 0.174, 0.87],
  ["shadow", [[-0.84, -0.1], [-0.94, 0.3], [-1.0, 0.9], [-1.03, 1.5], [-1.1, 2.3], [-1.17, 3.05]], 0.183, 0.99],
  ["lit", [[0.06, -1.47], [0.3, -1.15], [0.5, -0.68], [0.6, -0.14]], 0.172, 0.95],
  ["shadow", [[0.2, -1.42], [0.62, -1.2], [0.88, -0.8], [0.98, -0.28], [0.96, 0.1]], 0.187, 0.96],
  ["lit", [[0.3, -1.48], [0.72, -1.28], [0.98, -0.88], [1.08, -0.3], [1.13, 0.5], [1.17, 1.3], [1.27, 2.2], [1.36, 3.05]], 0.223, 0.98],
  ["shadow", [[0.84, -0.1], [0.95, 0.3], [1.01, 0.9], [1.06, 1.5], [1.13, 2.3], [1.22, 3.0]], 0.143, 0.87],
];
// Where the ear meets the skull, top and bottom, in head radii from the head
// centre with y down.
//
// Measured off `ref/satoshi-real.jpg`, which is the one reference that draws the
// ear plainly: the hair hangs around it rather than over it. The life-drawing
// rule of thumb, ear from the brow line to the nose, is *not* what the canon
// draws and following it put the ear 0.16 head radii too high. The canon's ear
// top sits level with the top of the eye aperture, not the brow, and its bottom
// runs to 0.49, which is lower than our own nose at 0.36. Ours and the canon's
// noses do not agree about where they sit against the skull, so the ear is
// placed against the skull and the eye, which do agree, rather than against a
// nose that would drag it up.
//
// The fit is eye centre to drawn chin: our eye sits at 0.16 head radii and our
// chin ink at 1.05, so that run is 0.89 r, and both ends are unambiguous ink in
// the reference. Eye to mouth was tried first and is not usable here, since the
// canon's mouth sits lower against its head than ours does; it gave a head
// radius 38% different from the one eye-to-chin gives.
//
// Stated as named constants because the hair wants them too. A side lock's
// length and flare were being chosen against nothing at all, which is most of
// why they took five rounds and still did not settle; the ear is the landmark
// they were missing, so a lock that should tuck behind it or flick past it now
// has something to say that against.
export const EAR_TOP_Y = 0.03;
export const EAR_BOT_Y = 0.49;
// How wide the aperture runs against its own height, shared by every character
// so `FaceStyle.eye_width` stays what it says it is: one character's deviation
// from the house eye, not the house eye itself. At 1.0 this is a no-op and
// `eye_width` alone decides the shape, which is how it used to work.
//
// The canon eye is a wide almond and ours was nearly circular: measured on the
// chibi, aperture width against height came to 1.12 where the canon draws 1.51.
// 1.28 here lands the aperture's width on the canon's to within a pixel, 0.1137
// of figure height against 0.111. It is a shared number rather than a bigger
// `eye_width` per preset because the roundness was the house shape's, not either
// character's, and the two presets' values differ from each other on purpose.
//
// The aspect still comes out at 1.41 rather than 1.51, because the canon's
// aperture is also about a tenth shorter than ours. That part lives in
// `eye_openness` and `eye_lower_lid`, which are per-character expression values
// the owner set deliberately, so it is left alone rather than tuned to a ratio.
export const EYE_ASPECT = 1.28;
// The half-gap between the eyes against an eye's half-width, and the least room
// between an eye's outer corner and the face's edge, in head radii
// (`_eye_placement`).
export const EYE_GAP = 0.44;
export const EYE_CORNER_CLEAR = 0.05;
// Face maturity's own terms, beyond the retired adult build's that it reaches
// through `Skeleton.face_build` (`docs/detail-plan.md`, D3): how much lower the
// eyes sit at maturity 1, in head radii. The reference's eyes sit lower in a
// longer face than ours (`docs/detail-status.md`, D0).
export const MATURE_EYE_DROP = 0.06;
// And how much of the retired adult build's change to the eye itself (its
// openness, width, corner, size, spacing and pupil) face maturity carries. At
// half, the owner found the grown face's eye too small against the reference's
// (2026-09-27); on the rebuilt Everglow cover, too different within one story:
// the eye's area fell to 0.70 at face age 1. How big a character's eyes are is
// `FaceStyle.eye_size`'s to say; the age now only nudges it
// (`harness/detail/eye_age_study.py`, the owner's pick "light").
export const MATURE_EYE_SHARE = 0.2;
