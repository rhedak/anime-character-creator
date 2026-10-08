# Hands status

The record for `hands-plan.md`. Procedure: `detail-strategy.md`.

## RESUME

H0 to H5 are built, and **the options are in `src/`** (2026-10-08, after the owner
chose G2 and to keep every hand as an option). Left: **V8, the preset assignment**
(which preset takes which hand and grip, the owner's call; every preset still wears
the mitten) and H6 (docs, a roster look, and a regeneration of the consumers only if
asked). Sheets for the shipped styles: `out/hands/v8/` (A mitten, B notched, C
stroked, D curled, E open, F fist).

What shipped: `CharacterParams.hand_style` is the relaxed hand, one of `HAND_STYLES`
= mitten (the default), notched, stroked, curled, traced; the new
`CharacterParams.grip_style` is how a staff-holding hand is drawn, one of
`GRIP_STYLES` = mitten (the default), fist. The old `hand_style="grip"` still reads
(mitten hands, fist grip). **Deviation from the plan:** no `HAND_POSES` registry
class and no pose per side. The styles are two tuples and a builder table
(`_HAND_BUILDERS`), because nothing yet needs a pose per side (the owner assigns per
preset). The traced fist's data and the old relaxed hand's drawing are gone; the
traced relaxed data stays, now squared and used as `_HAND_OPEN`. The web tool has a
"Hands" and a "Staff grip" control.

Every preset wears the mitten (`hand_style` and `grip_style` default to "mitten").

**Candidate T's inputs (H3 only), updated 2026-10-08 after the owner's `git pull`
(`cd934c7` "katherina ref").** The existing reference is now in the repo:
`ref/katherina/katherina_grok.jpg` (and `.png`, `katherina_kou_grok.*` with the
bat, and `ref/katherina/segments/layer-*.png`), all 1264 by 1568. `gate.py`
hardcodes `ref-local/katherina_grok/katherina_grok.jpg`, so a copy was made there
(`ref-local/` is ignored; the copy is not tracked). **Control, predicted first and
held:** `gate.py` on the pulled image against itself reads scale 173.7 px per head
radius with 0.0% disagreement and soles 5.941, hem 4.231, skirt half-width 1.019,
all differences +0.000, PASS. So it is the image the gate was calibrated on. Still
needed from the owner for T: the new hand reference. Still absent and optional:
`katherina_grok_real/`. The sibling repos are not needed.

**What the canon's chibi hands look like** (`ref/katherina/katherina_grok.jpg`,
seen, not measured): small, chunky closed fists and mitten shapes, with at most a
couple of finger lines. The relaxed hand is a rounded mitten; the staff hand a
fist with a few finger lines across the pole. This is closer to K2 and K3 than to
the traced hand taken off the realistic reference.

## Scoreboard

| step | state |
|---|---|
| H0 baseline and tools | done; V0 answered 2026-10-08 |
| H1 candidate S, shrink and simplify | done: failed, the owner chose wider (W) |
| H2 candidate K, constructed hands | done: shipped as notched, stroked, curled |
| H3 candidate T, traced from a chibi reference | not needed: the owner kept the options and fixed the fist by construction |
| H4 candidate G, the grip | done: G2 chosen, shipped as `grip_style="fist"` |
| H5 R, the options in `src/` and a guard | done (no registry class, see RESUME); V8 the assignment, open |
| H6 close | not started |

## Owner's answers

One line per checkpoint, dated, as the owner answers.

- **V0, 2026-10-08.** The traced hands "look too thin, almost skeletal". They
  "don't connect to the arms well (we'd probably see this better with clothes
  off)". "For katherina they don't even fit and have parts missing (the fist)."
  Gate numbers: not commented on; kept as proposed, still open. What "parts
  missing" points at is to be asked of the owner: see the Katherina findings
  below.

## H0, 2026-10-08

- Promoted the audit's scripts to `harness/hands/` (README there). **Control:**
  run on all 19 presets, `metrics.py` reproduces the audit's figures exactly:
  mitten bounding box 0.342 by 0.436 head radii, aspect 0.78, outline 26.1%;
  traced 0.557 by 0.342, aspect 1.63, outline 45.0%. `ablate.py pieces`
  reproduces 45.0%, 42.9%, 42.5%.
- The gate, applied to every preset: the mitten passes on all 19; the traced
  relaxed hand fails all four measures on all 19 (Katherina's right hand too).
  Katherina's traced grip is flagged "judged by eye", because the gate covers
  hanging hands only. Before that scoping the gate failed the grip on height,
  outline share and narrowest run, though it is the one traced hand that reads
  well, so the scoping is deliberate.
- The byte snapshot, `out/hands/before`, is 114 renders. The older docs say
  105; the snapshot has grown since.
- `harness/README.md` says numpy is not a dependency. It is: `pyproject.toml`
  lists `numpy>=1.26`. That README line is stale; not changed here.
- `ref-local/` and `../valley_of_mist`, `../time_slider_katherina`,
  `../short_stories` are absent from this machine.

## H1 and H2, 2026-10-08

**Predictions, written first, and what happened** (`harness/hands/metrics.py`,
the five sheet presets):

- **S** (the traced relaxed hand brought to height 0.36 head radii of hand, its
  wrist filling the whole cuff opening). Predicted: passes the footprint gate,
  fails by eye. **Result: it fails the gate too.** Height and aspect pass (0.41,
  1.11) but the outline share rose from 45% to **55%** and its skin area fell to
  0.031, a third of the mitten's (0.089); narrowest run 0.07 and join 0.88 of the
  mitten's still fail. Shrinking a hand whose line weight is fixed makes it
  thinner, not better, which is the owner's "skeletal". By eye it reads as small
  claws. So the audit's claim, that size alone is not the fix, is now confirmed
  by a candidate and not only by widening.
- **K1** (mitten, tip notched into three fingers). Predicted: passes, reads as a
  hand at full size. **Result: passes on Krista, Gero, Satoko and Keiko** (height
  0.355, aspect 0.82, outline 29%, narrowest run 1.64, join 1.00). **On Katherina
  the narrowest run is 1.47 against the gate's 1.5**, a narrow miss (her hand is
  larger, so the same notch is relatively tighter).
- **K2** (the mitten's silhouette, unchanged, with two finger strokes).
  Predicted: passes. **Result: passes everywhere**, narrowest run 2.3 to 2.5.
- **K3** (a half-closed hand). Predicted: the one at risk of looking clenched.
  **Result: the gate caught it, and so did the eye.** The first version, with a
  closed thumb shape of its own and three curled finger strokes, failed outline
  share (39%) and narrowest run (0.2), and its thumb read as a ring at the cuff.
  Revised three times (the mitten's own thumb bump, a short thumb crease, two
  parallel finger arcs, the crease moved off the outline): **now passes**,
  outline 31%, narrowest run 1.98. The first two revisions failed only on
  narrowest run (about 1.0); what fixed it was moving the thumb crease's start
  away from the thumb's outline.
- **At chapter-insert size** K1 to K3 are indistinguishable from the mitten,
  which is acceptable and was predicted.
- **The owner's three criteria**, on the sheets: all three K hands close the bare
  forearm with a cuff line at the mitten's width (join 1.00; `v6_bare.png`) and
  fill Katherina's wide cuff (`v7_katherina.png`). S inherits the traced hand's
  open wrist.

**Not verified.** Whether the owner reads K1 to K3 as hands rather than as
mittens with marks: the gate cannot say.

## V1 follow-up: why S shrank the hand, and W, 2026-10-08

The owner asked why S made the hands smaller, saying they need to be wider to
fit, "especially visible in `v6_bare.png`".

**Why S shrank it.** The plan defined S as the control for "is it just size?",
and the gate's height range (0.30 to 0.42 head radii, taken from the mitten's
0.34) put the traced hand's 0.56 out of range, so S scaled it down uniformly. That
was the wrong lever for the owner's complaint. The complaint was too thin, and S
moved the other way: outline share rose from 45% to 55% and skin area fell to
0.031, a third of the mitten's. The V0 audit had also already shown widening
helped, and I had undersold it (corrected above).

**Prediction for W, written first.** W (the traced relaxed hand at the gate's
height, stretched across 1.6 times, the wrist widened to fill the arm) passes
height, aspect and join, and may still fail the finger-width measure, because
stretching widens the fingers and the gaps between them together. W2 is the same
at 2.0 times.

**Result** (five sheet presets, `metrics.py`; Katherina's join is not read, her
mitten being tilted along the cuff):

| | height | aspect | skin area | outline share | narrowest run | join vs mitten |
|---|---|---|---|---|---|---|
| mitten | 0.34 | 0.79 | 0.089 | 26% | 9.9 | 1.00 |
| traced | 0.56 | 1.63 | 0.062 | 45% | 0.07 | 0.82 |
| S | 0.41 | 1.11 | 0.031 | 55% | 0.07 | 0.88 |
| W (1.6x) | 0.41 | 1.00 | 0.052 | 46% | 0.07 | 0.99 |
| W2 (2.0x) | 0.41 | 0.99 | 0.066 | 42% | 0.07 | 1.01 |

The prediction held: the join and the footprint are fixed, outline share and
finger width are not. **By eye** (`out/hands/v1b/v6_bare.png`): W and W2 meet the
forearm at its full width with no step, and W2 reads as a relaxed curled hand.
What remains is the fingertips, whose lines collapse into one dark knot at the
tip. So width was the owner's right call; the fingertip detail is the open fault.

**Caveats.** W and W2 stretch the traced shape across only, a per-axis scale the
trace-reference skill forbids for fidelity to a reference. It is used here
because the target is the chibi's proportions, not the reference's, and the
result would be a hand authored on its own terms, not a faithful trace. W2 also
changes Katherina's staff grip, which is not judged here. Not yet checked: W and
W2 on the other views (insert size, heights, dark skin, Katherina's cuff).

## H5, built into `src/`, 2026-10-08

**Byte guard, predicted first and held:** `harness/tall_chibi/snapshot.py` before and
after, 114 renders, `cmp` finds 0 differing; `./refresh-ref-out.sh --check` reports
`ref-out/` matches the code; `./refresh-catalogue.sh` changed `ref-out/catalogue.json`
by listing the new styles only. **Port control:** the shipped styles reproduce the
prototypes' gate numbers to the digit (notched 0.355 tall, 29.1% outline; stroked
29.0%; curled 30.7%; traced 0.416 tall, 38.0%). **Tests added** (`tests/test_smoke.py`):
a footprint guard for every relaxed style on three presets (height 0.28 to 0.46 head
radii, height over width 0.6 to 1.3), each style draws and differs from the mitten, the
fist grips a held staff only and the old "grip" name reads, the fist stays level as the
arm swings (the mapping's angle changes by exactly 0.85 of the swing), and the open
hand is squared. **Mutation checks:** the footprint guard fails on the old traced hand
(0.536 tall, aspect 1.35) and the squared-wrist test fails on the bevelled outline (flat
top -0.05 to 0.16 against a wrist -0.21 to 0.18), so neither is vacuous. Two assertions
were written too weak first (one trivially true, one that the old outline also passed)
and tightened.

## H4, the grip: G1 and G2, 2026-10-08

The owner: keep all of these as options and fix the traced fist so it looks like a
proper fist "rather than whatever it is now".

**What the canon's fist is** (`ref/katherina/katherina_grok.jpg`, the staff hand,
cropped at 3x and set beside ours at the same head scale, 173.7 px per head
radius; seen, and the sizes read off the crops): about 0.48 head radii each way;
four short rounded finger rolls stacked on the pole side with three short
crease strokes; a big rounded back of the hand with the thumb folded into it;
the pole visible at the left edge. **Our traced grip** (seen): about the same
size (0.58), so size is not the fault. The shape is: a skinny thumb jutting out,
angular rolls, parts clipped by the cuff, off the adult reference's hand. At
Katherina's wide cuff its wrist is 47% of the opening.

**G1** is a constructed fist in the canon's language, built in the traced grip's
own hand frame (so the placement, the cuff fit and the staff channel are
unchanged): a finger block with three crease strokes, a rounded back of the hand
with a thumb crease, outlines from a closed quadratic B-spline through a
superellipse. **Prediction, written first:** it reads as a fist and fills the
cuff better (its wrist end spans about 80% of the opening against 47%).
**Result:** it reads as a proper fist, at zoom, beside the canon's. **G2** is G1
kept upright against the arm's swing (it counter-rotates by 0.85 of the swing),
so the creases stay level as the canon's do. A first version with a fixed
bend of -30 degrees looked right on Katherina's 36-degree arm but would be wrong
on an arm hanging straight, so it became a rule.

**Generality** (`g2_general.py`, seen): on Katherina's arm swung 0, 20, 36 and 50
degrees and on a staff given to Krista (a different outfit, arm 25), G1 and G2
read as a fist each time; at swing 0 G2 is identical to G1.

**Not verified.** That the owner prefers the cuff-aligned fist (G1) or the upright
one (G2). The cuff joint looks clean at 14x; the sleeve's own cuff band is mostly
hidden by the fist's back, which may differ from the canon's visible band: to look
at. The metrics are not run on the grip (the gate covers hanging hands).

## W3: the transition clipping and the fingertip knot, 2026-10-08

The owner on W2: better, but "the transition area still has some clipping".

**Hypotheses, written first.** H-A: the ticks at the wrist are the traced
outline's own geometry, present in the unstretched hand too. H-B: they come from
W's stretch and wrist widening. If H-A, the traced outline's wrist end is not
square.

**Result: H-A, supported.** `_HAND_RELAXED[0]`'s outline runs flat along the top
(x -0.05 to 0.16 hand lengths, y -0.033) but on the left it runs diagonally down
to (-0.205, 0.018): the trace followed the reference's forearm meeting the hand
at an angle. The corners of that bevel draw as ticks below a cuff or on a bare
arm. The unstretched traced hand shows the same step in `v6_bare.png` (column B).

**W3** replaces the wrist end with a square cross-cut (each side carried straight
up from its own outline point, a flat top at -0.033) and drops the two fingertip
sliver pieces and the interior lines. **The fingertip knot was those pieces**:
it is gone, leaving one pointed hand with a single curled-finger line. W3k keeps
the tips and squares the wrist only, to separate the two changes.

| | height | aspect | skin area | outline share | narrowest run | join vs mitten |
|---|---|---|---|---|---|---|
| W2 | 0.41 | 0.99 | 0.066 | 42% | 0.07 | 1.01 |
| W3 | 0.42 | 0.98 | 0.068 | 38% | 0.14 | 1.03 |

W3 still fails two gate measures: outline share (38%, limit 35%) and finger
width, because a pointed fingertip is narrow by nature.

**By eye** (`out/hands/v3/`): W3 reads as a relaxed hand with a hooked, pointed
tip; the K hands are chunkier and cleaner at this size. **Two tiny corner nubs
remain** where the squared top edge's stroke meets the sides (about a pixel),
which would go if the hand were drawn as an open path with no top edge on a bare
arm. Left for the owner to decide whether it matters.

**Caveats.** My first square-wrist cut had the corners in the wrong order and
sloped sides, which drew a stub and a wedge; fixed by carrying each side
straight up from its own point. W, W2 and W3 also stretch Katherina's staff grip
into a long flat hand, because the patch covers both traced poses; that is not
judged here and is H4's. Katherina's right hand reads 0.44 tall, over the gate's
0.42, because her wide cuff scales it up.

## V0 follow-up, 2026-10-08

Tests of the owner's second and third complaints, run before building anything.

**Verified.**

- **The join with a bare arm.** On the two neutral bases with every garment off
  (`out/hands/v0/v6_bare.png`), the traced hand starts with an open, unstroked
  wrist that is narrower than the forearm, and the forearm ends in a flat edge
  with a step down to it. The mitten closes the forearm with a cuff line.
  Measured on the female base: arm half-width 0.199 head radii, the traced hand
  drawn at 0.162 where it starts (0.9 of the 0.180 cuff opening), after being
  traced at 0.098. By the new `join_vs_mitten` measure the traced hand is 0.81
  of the mitten's width at the join on every plain-sleeve preset.
- **Katherina's staff arm, the fit.** Her wide cuff opens 0.228 head radii
  either side. The traced grip's wrist is 0.106, **47% of the opening**, so the
  fist sits in a cuff more than twice its width, and the cuff runs over the back
  of the hand (`v7_katherina.png`). Her other arm's hand is widened to 90% of
  the opening (0.205) from a traced 0.098, then tapers to a thin hand.
- **Katherina's fist, drawing.** All four grip pieces are drawn (four outlines
  and three lines in the SVG) and all four show when the fist is rendered
  alone with its arm's 36 degree rotation. So "parts missing" is not a draw
  failure I can reproduce; the cuff covering the back of the hand is the only
  thing I can see hiding part of it.
- **The other hand on Katherina** is a thin sliver whose outline all but
  vanishes against the dark skirt (seen, not measured).

**Caveat found in the harness.** An arm swung out is drawn inside a
`rotate(...)` group, and `metrics.py` rasterises each hand without it. That
only changes Katherina's staff arm (swung 36 degrees); every other hand is
unrotated, so the 18 other presets' numbers stand. The gate excludes the grip,
so no verdict depends on it.

**Not verified.** What the owner means by "parts missing (the fist)": the
cuff covering the back of the hand, the small size against the cuff, the
pinky not showing, or something else. To ask.

## Audit, 2026-10-08

Method: every preset rendered with `hand_style` "mitten" and "traced", both
hands cropped at 5x; each hand's own SVG isolated and measured; a counterfactual
widening; the traced pieces dropped one at a time; the upper body at the
chapter-insert size. The scratch scripts were `hands_audit.py`,
`hand_metrics.py`, `hand_counterfactual.py` and `hand_pieces.py`, promoted in
H0. The pytest suite was not run.

**Verified.**

- The traced relaxed hand against the mitten, identical on every preset except
  Katherina (her wide sleeve and staff): length 0.50 against 0.29 head radii,
  bounding box 0.34 by 0.56 against 0.44 by 0.34, height over width 1.63
  against 0.78, skin area 0.062 against 0.089 (0.70 times), outline share 45%
  against 26%.
- At head radius about 21 px the traced relaxed hands read as thin dark ticks;
  the mitten reads as a hand.
- Ruled out: the fingertip pieces and interior lines as the cause. Dropping
  them moved the outline share from 45.0% to 42.9%. The piece count is three:
  the main outline (31 segments, 2 interior lines) and two fingertip slivers
  (9 and 7 segments).
- Width alone: **corrected 2026-10-08, see "V1 follow-up" below.** The audit
  called this mostly ruled out. That was too strong: widening by 1.3 and 1.6 did
  fill the hand, and a properly joined wide version fixes the join and the
  footprint. It is necessary, not sufficient.
- The traced grip on Katherina's staff reads as a fist round the staff at 8x.
  It is the best of the traced hands.

**Observed in the code, not by experiment.**

- No `HAND_POSES` registry exists in `src/`; there is `HAND_STYLES` and the
  constants `_HAND_RELAXED` and `_HAND_GRIP`.
- The grip is tied to `side == -1 and p.outfit.staff_color is not None`
  (`character.py`, `_hand_traced`, `_traced_placement`, `_hand_centre`).
- No preset sets `hand_style`. The one test of the traced hands is a smoke
  test that they draw (`tests/test_smoke.py:2449`).

**Not verified.**

- That the cause of the silhouette is that both poses were traced off
  `katherina_grok_real`, a realistic-body reference. The plan of D4d says they
  were; `ref-local/` was missing on the audit's clone, so the original
  reference was not re-measured.
- Heights 0.8 and 1.3, dark skin and swung arms were not re-checked. D4d
  recorded checking them.
