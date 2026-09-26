# Tunic bust plan

Make the clothed bust agree with the bare one. Written 2026-09-26 at the
owner's request, straight after the bare body plan (`bare-body-plan.md`),
whose step 4b gave the bare breasts their own shape.

The record goes in `bare-body-status.md` under its own heading, and the
procedure is `bare-body-strategy.md` and `bust-strategy.md`: predict before
measuring, one change per measurement, look in the right view, only the
owner signs off.

## The problem (`harness/bare/tunic_vs_bare.py`, `out/bare/tunic_vs_bare.png`)

The bare breast (`_bare_breast_spine`) is an ellipse widest at the fullest
point, reaching `bust_reach` past the plain side, dropping the fold's depth
times 1.25, outlined from the arm's inner corner round the outside, the
bottom and up the inner side. The tunic still draws the bust as the bust
campaign left it: the torso's side bent out at the fullest point and hanging
from there (`_bust_shape(drape=True)`), and under it `_bust_lines`, a
shallow fold tuned for cloth before the bare breast existed. Drawn over the
tunic in red, the bare outline disagrees on every woman:

1. **Depth**: the bare curve drops lower and rounder (clearest on Krista,
   Keiko, Chiyo); the tunic's line is shallower and higher.
2. **The outer side**: the bare outline runs round the outside from the
   armpit; the tunic's line starts on the side at the fullest point's height,
   so the breast's lower outer curve is missing clothed.
3. **The inner end**: the bare curve rises further toward the sternum.
4. **The side silhouette** (the drape over the arm) roughly agrees already.

## What should stay

- Cloth hangs from the fullest point rather than tucking under (the anatomy
  review, `bust-plan.md`, step 9b): the tunic's silhouette below the widest
  point stays a drape, not the bare tuck.
- An outer layer (a coat, a robe front, the lab coat) covers the line under
  the bust; its own outline is the cue there (`bust-plan.md`, step 4).
- Flat colour, line work only; no shading under the bust.
- Men and every figure with no bust stay byte-identical.

## The order

### T1. Study (no source change)

Variants on the six adult women, clothed, beside the bare row, for the owner
to pick from:

- **a** the current fold, for reference;
- **b** the line under the bust taken from the bare ellipse itself, at the
  same depth, starting on the tunic's side outline where the ellipse leaves
  it and tapering up the inner side, tapered at the outer end as a fold;
- **c** as b, a little shallower (cloth bridging the fold, 0.85 of the bare
  depth);
- **d** b plus the silhouette: the tunic's side from the armpit to the
  widest point on the bare outline's curve, then the drape as now.

**Recommendation to confirm on the sheet:** d, or c's depth with d's side,
so a character reads the same with the tunic on or off.

### T2. The line under the bust

Build the chosen line in `_bust_lines` from `_bare_breast_spine`'s geometry,
so the two can no longer drift apart. Clothed women move; that is the point.
**Acceptance:** men and the bust-0 presets byte-identical (`--check`), the
pixel diff confined to the chest of the nine presets with a bust, the cast
sheet looked at, a test that the tunic's line and the bare outline share
their ellipse.

### T3. The silhouette (if d is chosen)

`_bust_shape(drape=True)` takes the bare outline's curve from the armpit to
the widest point and drapes below. Everything reading the drape follows it
at once: the tunic, `_bust_over_arms` at the chibi (the lobe over the arm),
the traced cuts (`_bust_bulge`). **Acceptance:** as T2, plus Keiko's coat,
Katherina's jacket and Reika's robe front looked at at 4x, and the continuity
test (a bust of 0.01 moves nothing by more than 0.01) still green.

### T4. The cast and the downstream

The whole cast clothed at the chibi, `ref-out/` refreshed and its report
read, the realistic build rendered (not judged), the docs. Then, on the
owner's say-so, `../valley_of_mist` regenerated.

## Deferred, as before

- Kyoko's parametric `_coat` and Reika's `_robe_front` do not swell with the
  bust (`bust-plan.md`, deferred).
- The realistic build's own fix pass.
