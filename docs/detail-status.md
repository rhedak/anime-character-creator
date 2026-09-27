# Detail status

The record for `detail-plan.md`. Procedure: `detail-strategy.md`.

## RESUME

D0 and D1 done (2026-09-27), and the second eye style retired. Next: D2,
the eyes (a study first). `../valley_of_mist` is not regenerated yet: the
plan's first checkpoint is after D2. The baseline is
`harness/detail/baseline.py` (writes `out/detail/`); the height range is
`harness/tall_chibi/height_range.py`; the inventories are in
`docs/detail-inventory/`. The plan is committed at 7b8a2f7.

## Scoreboard

| step | state |
|---|---|
| D0 inventory and baseline | done |
| D1 line weights | done |
| D2 eyes | not started |
| D3 face maturity | not started |
| D4 body at height | not started |
| D5 hair | not started |
| D6 garment line work | not started |

## Findings, newest first

### D1: the line weights built (2026-09-27)

The owner's pick: outlines at 0.75 of the old weight, interior lines at
0.55. `_stroke_w` keeps the old weight, since 18 places size geometry off
it; the drawn weight goes through `_outline_w` and `_interior_w`
(`_OUTLINE_SCALE`, `_INTERIOR_SCALE`), all 100 drawn sites classed by hand:

- **By meaning, not by the study's value rule.** An outline is a part's
  edge at whatever fraction it was drawn (the hands, cuffs, pouches, belt
  pieces, strap, robe front, the eyes' aperture and the brows); an interior
  line divides or decorates inside a part. So those edges come out 0.75 of
  their old weight where the study showed 0.55.
- **Kept**: the bust mask's widening stroke and the goggles' rim (a band
  sized off the lens).
- **Filled lines** (the bust fold, the bare breasts' line, the male chest
  lines) take the outline scale in their width: they meet the body's
  outline and have to match it there.
- **Every geometry use of the weight is untouched**, including the offsets
  that tuck a fill under a line (the bust over the arms, the arm's joint
  cap, the bare foot's ankle patch, the belt).
- Drawn weights print to two decimals now, not one, which cost up to 8% on
  the thinnest lines.

**Predicted:** with `stroke-width` stripped every SVG identical but the
three filled lines; the stroke ratios at 0.55 and 0.75, and 1 on the kept
sites. **Measured** (`harness/detail/d1_check.py` over two snapshot runs):
the only geometry changes are those filled lines and the coat-bust masks
whose content-hashed ids hold the bust line; ratios 0.53 to 0.56 and 0.72
to 0.77 (the old values' one-decimal rounding), 1.00 on 29 strokes. By eye
(`harness/detail/d1_look.py`): the whole figure lightens evenly; at 4x the
bust over the arm, the base layer, the belt, the hand and the bare foot show
no gap or overhang. `ref-out/` and the bases refreshed; 479 passed, 1
skipped.

**Seen, not caused by D1:** a short grey vertical mark at the bottom of
Keiko's coat-at-the-arm zoom, before and after alike. Left for D6.

### D1: the line-weight study (2026-09-27, at 9079ad7)

`harness/detail/line_weight.py` rescales only the drawn `stroke-width`
attributes (geometry untouched, as the change will be), silhouette strokes
(within 5% of `_stroke_w` or above) and interior strokes separately, on
Satoko, Krista, Keiko (a white coat on a light card, the worst case) and
Katherina. Variants (outline, interior): (1.0, 1.0) today, (0.75, 0.75),
(0.6, 0.6), (0.75, 0.55), (0.6, 0.4).

**Predicted:** (0.6, 0.4) closest to the reference at full size; at the
smallest size, 1x, the 0.6 outline goes faint.

**Measured, by looking:**

- Full size: (0.6, 0.4) reads closest to the reference, as predicted.
- Smallest size, 1x (`line_weight_small_zoom.png`): every variant's
  silhouette still reads, since the flat fills carry it; the prediction
  was wrong there. What fades is the interior: at 0.4, Keiko's lapels and
  glasses frame and the hair strands go near-invisible grey. At 0.55 they
  hold.
- **The reference's own weight**, measured on its chin line (a dark run of
  2 to 3 px across columns 610 to 665) at the calibrated 83.9 px per head
  radius: about 0.030 head radii, 0.70 of ours. Its finger lines measure
  the same.

**Recommendation: (0.75, 0.55).** It is within 7% of the reference's
measured line, and the interior survives the smallest view. (0.6, 0.4)
looks lighter still at full size but loses the interior in the chapter
inserts.

### The second eye style retired (2026-09-27)

`_eye_anime`, its `eye_glow` knob, the `eye_style` field and the
`EYESTYLES` registry are gone; `_eye_realistic` is now `_eye`, the one eye
D2 redraws. The web tool's eye style select went with the catalogue entry;
an old link carrying `eye_style` or `eye_glow` loads with the one eye
(`urlstate`, tested). **Predicted:** every render byte-identical, since no
preset used the style; the suite at 483 minus the 6 eye-style tests plus 2
old-link tests. **Measured:** `harness/tall_chibi/snapshot.py`, 105 renders
`cmp`-identical to the committed tree's (its two `eyes.*` cases dropped);
`./refresh-ref-out.sh --check` matches; 479 passed, 1 skipped.

### D0: the line-weight inventory (2026-09-27)

Full list: `docs/detail-inventory/strokes.md` (a Sonnet delegate's read,
109k tokens; its UNSURE classes are marked there). 105 `stroke-width` sites
plus 18 places the weight is used as geometry:

| class | sites | multipliers of `_stroke_w` |
|---|---|---|
| silhouette | 53 | 1.0 on 37; 0.7 to 0.9 on the rest |
| interior | 44 | 0.4 to 0.7 mostly; 1.0 on 2 |
| feature (eyes, brows, mouth, glasses) | 11 | eyes 0.85 (`_EYE_OUTLINE_W`); brows from `FaceStyle.brow_weight` |
| geometry, not ink | 18 | offsets, radii, thresholds, clamps |

What it means for D1, checked by reading:

- **Interior lines are already split off by a factor** almost everywhere, so
  "lighter silhouette" and "lighter interior" are two separate levers: the
  base in `_stroke_w`, and the interior factors.
- **The weight doubles as geometry in 18 places**, and not all of it should
  follow a lighter line. Offsets that cover or meet a drawn stroke (the bust
  over the arms, the arm joint cap's half stroke, the bare foot's ankle
  patch, the body inset under a garment) should follow the ink. Sizes and
  thresholds should not: the navel's size, the placket button's radius, the
  underskirt's and hakama's pleats (drawn only when wider than four
  strokes), the crystal spacing, the staff's and familiar's canvas clamps.
  D1 therefore gives the ink its own weight and keeps the current value for
  the geometry that must not move, site by site.
- **`hat_hair_margin`** allows for the stroke with a literal 0.06 head
  radii, not `_stroke_w`. A lighter line leaves it generous, which is
  harmless and keeps the canvas; leave it.
- **Existing lighter silhouettes**: the robe front (0.7), several at 0.85.
  A lighter base would make them lighter still; D1's study checks they
  still read.
- **Not tracking the weight**: the goggles' lens rim (from `lens_r`) and the
  staff crystal's outline (full weight on a small shape).

**The owner's answers (2026-09-27):** retire `_eye_anime`; commit as each
step lands with the usual one-liners.

### D0: the baseline (2026-09-27, at 7b8a2f7)

**Calibration** (`out/detail/calibration.txt`). Our face (Katherina, the
hat off, the skin component): widest visible row at 0.446 head radii below
the head centre, half-width 0.852, chin at 0.987. The reference's face
component: widest row y 330, x 564 to 707, chin y 399.

- Scale from face width: 83.9 px per head radius; the reference's head
  centre at (636, 293).
- Scale from the widest row to the chin: 127.7. They disagree by 52%, by
  design: at one face width the reference's chin is at 1.26 head radii
  against our 0.99, a longer lower face ending in a point. That is D3's
  direction (a chin that drops and narrows), not a calibration fault.
- The review's by-eye crop (88 px) was 5% off; the calibrated sheet is
  `out/detail/face_vs_reference.png`.

**The smallest view** (`out/detail/smallest.png`). `../valley_of_mist`'s
chapter inserts are `sheet.sh` sheets, up to four columns, 2576 px wide;
its reader (`.chapter-end`, `max-width: 40rem`) shows them about 600 CSS px
wide, a scale of 0.233. A tile scales the figure by `0.86 * 400 /
canvas_h`, so the head radius there is about 21 px at 1x (Satoko 21.6,
Katherina 20.3; the review's "13 px" was a guess) and today's line (0.0427
head radii) about 0.9 CSS px, 1.8 device px on a 2x screen. Halving it
leaves about 0.45 CSS px at 1x: D1's lighter weights must be judged at this
size first.

### D0: the face, body and hair inventory (2026-09-27)

Full list: `docs/detail-inventory/face-body-hair.md` (a Sonnet delegate's
read, 131k tokens); the load-bearing lines, checked by reading:

- **The realistic lerp is still in place, running at the pinned build.**
  `_head_pt` (the skull: `_SKULL_NARROW * build`, `jaw_pull = 0.20 * build`,
  `chin_drop = 0.05 * build`), `_eye_placement` (`eye_dx` and the eye's size,
  openness, width and corner scale with `sk.build`; `eye_y = cy + 0.16 r` has
  no build term), `_arms` (elbow and wrist taper by `0.15` and `0.34 *
  build`), `_legs_and_boots` (`taper = sk.build`). With `sk.build` pinned at
  0.1 each runs at a tenth. **D3 and D4b can drive these terms** from face
  maturity and height instead of drawing new shapes, keeping today's value
  at the default so the default stays byte-identical. The realistic values
  they lerp toward were measured off `ref/satoko-real.jpg`; D3's study
  decides how far along each the slider goes.
- **No nose exists anywhere**: D3's nose tick is new.
- **One hand shape**, `_hand`, a mitten with a thumb bump ("still no
  fingers"); props sit over it at `_hand_centre`.
- **`_KEEP_WS` holds all eight width fields** and `stretched()` rescales
  them with `head_r` only; D4a's follow-through goes there, and the hands,
  feet, belt, skirt and torso all read those fields, so they follow free.
- **Every hairstyle already draws strands** (open quadratic chains as thin
  strokes); `long_traced` has the fewest (4), `short_crop` the most (10).
- **`_eye_anime`**: no preset uses it, but the catalogue's eye style option
  lists it and two tests iterate `EYESTYLES`; retiring it is three small
  touches. An owner question for D2.
- **Discontinuities**: `eyes_closed`, `scar_side`, `eye_style` switch by
  design; no stray thresholds in the face.
