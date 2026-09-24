# Bust status

The record for `bust-plan.md`: what has been measured, predicted and decided,
newest first. The plan says what to do; this says where it stands. The method
lessons live in `bust-strategy.md`.

## RESUME (for a fresh context)

- **Now:** step 9b, loose garments hang from the fullest point. 9a was tried
  and deferred (see its finding). Then 5b, 4, 7, 8.
- **Owner's calls 2026-09-24 (after 5a):** 5a signed off; the realistic build
  needs its own fix pass later, deferred; step 6 then 5b then 4; the fixed
  clip ids get fixed at the appropriate time.
- **Tree:** clean at `e3b65e5` when preparation began.
- **Measure** with `harness/bust/drawn_widths.py` (the drawn ink). Never quote
  a `Skeleton` field as a body measurement.
- **Run harness scripts** with `./harness/run.sh harness/bust/<script>.py`.
- **Check a change that should move no pixel** with
  `./refresh-ref-out.sh --pixels`; `ref-out/bases/` is not covered by it and
  is compared by hand with `compare_pixels.py`.
- **Owner sign-off** is needed after each step before the next.
- **Commits:** one line, repo style, no trailer.

## Scoreboard

| step | state | acceptance met |
| --- | --- | --- |
| B0 sweep harness | done, readings void | harness stands |
| B1 parameter and anchor | done, `bust_half_w` to be replaced | plumbing only |
| 1 reach, not width | done, signed off | continuity and armpit tests green |
| 2 pixel check | done | 0 of 54 on a clean tree; catches a bust |
| 3 body layer | 3a, 3b done; 3c deferred (owner) | 5 of 54 PNGs moved, a finding |
| 4 line under the bust | not started | |
| 5 bust over the arm | 5a done (chibi); 5b Keiko waits | zero case byte-identical |
| 6 traced cuts follow | done, signed off | zero case byte-identical; widening tested |
| 9 fit and drape (added 2026-09-25) | 9a tried, deferred to the realistic pass; 9b next | |
| 7 cast values | not started | |
| 8 integration | not started | |

## Step 1 preparation

### Who reads the anchor (grep at `e3b65e5`)

- `character.py` `_tunic`, the `rib()` closure: the only reader of
  `bust_half_w` and `bust_y` in `src/`.
- `skeleton.py`: `_BUST_ALONG`, `_BUST_REACH`, the two `Skeleton` fields and
  their computation in `build_skeleton`.
- `harness/bust/bare.py` prints `sk.bust_half_w`; `sweep.py`, `why_hidden.py`
  and `drawn_widths.py` set `bust=` only.
- **No test mentions bust.** B1's status said a test asserts
  `build_skeleton(bust=0.0) == build_skeleton()`; it was never written. Step 1
  writes it, along with the continuity test.

### Where the bust sits (measured at `e3b65e5`, head radii below the head centre)

| body | shoulder | armpit (`_sleeve_hem_y`) | `bust_y` | waist |
| --- | --- | --- | --- | --- |
| chibi, long torso (satoko, keiko, satoshi) | 1.118 | 1.788 | 1.905 | 2.713 |
| chibi, `tall_chibi` (katherina) | 1.130 | 1.657 | 1.981 | 2.384 |
| realistic | 1.280 | 2.561 | 2.653 | 4.330 |

`bust_y` is 45% of shoulder to waist, which puts it 13% of the way from the
armpit to the waist on the long-torso chibi and 5% at the realistic build: hard
up under the armpit, where a bulge merges with the sleeve cap. On `tall_chibi`
it is 60% of the way, so one constant lands differently on two chibi bodies.
**Open for step 1:** measure `bust_y` from the armpit. The armpit today is a
garment function (`_sleeve_hem_y`), not an anchor, so either it becomes one or
the bust's height is expressed in a way that does not need it. Decide by
reading `_sleeve_hem_y` first.

### Predictions for step 1, written before any change

With `bust_reach = head_r * lerp(0.10, 0.20, t) * bust` added to the torso
curve's own width at the bust row, chibi half-widths at that row:

| `bust` | 0 | 0.01 | 0.5 | 1.0 |
| --- | --- | --- | --- | --- |
| torso now | 0.583 | 0.950 | 1.013 | 1.080 |
| torso predicted | 0.583 | 0.584 | 0.633 | 0.683 |

Realistic: 1.077 at zero to about 1.277 at 1.0. The arm's ink starts at 0.587
(chibi) and 0.631 (realistic), so **as rendered, the whole bulge is predicted
to be under the arm at both builds for every value above about 0.04.** Step 1
is judged in `why_hidden.py`'s view (arms at a third), and the owner should
expect the rendered sweep to look unchanged.

### Delegation plan

- Step 1's shape, the continuity test and the `bare.py` crop: kept, since the
  shape is the judgment and the rest is a few lines.
- Step 2's pixel check: independent of step 1 and fully specifiable, so it
  can go to a `general-purpose` agent on `sonnet` in a worktree while step 1
  runs, brief in `bust-strategy.md`'s template.
- Nothing is read-only-trace shaped yet; no `Explore` needed.

## Open items outside the steps

- None. (`harness/run.sh`'s cairo path was fixed in `f61c3c1`.)

## Findings, newest first

### 2026-09-25: step 9a, the bust starting below the armpit: tried, not kept

**Owner's calls before it:** step 6 signed off; fit is a property of the
garment kind, not a new knob (for 9b).

**Tried.** The plain side from the armpit down to an onset 35% of the way to
the fullest point, then an S of two tangent-matched quadratics out to it (a
slight hollow where the arm's front fold meets the chest, then the swell).
The fullest point, reach and tuck unchanged, so the bust-row widths were
predicted and measured unchanged (0.579, 0.631, 0.687); `ref-out/` unchanged.

**Looked at, rejected at both builds** (`out/bust/onset.png`,
`onset_real.png`):
- **Chibi:** the chibi has 0.28 head radii between the armpit and the fullest
  point, against 0.53 at the adult build. An upper chest plus a 0.11 swell in
  that height pinched into a hook just below the armpit, at 0.5 as well as
  1.0. A smooth run from one near-vertical line to another set outward has to
  be an S or a corner, so no tuning fixes it. The bust starting at the armpit
  is the chibi's style, which is the anatomy review's own point 4.
- **Adult build:** the S read as a knob, a tight hollow then a small bump, and
  that build's bust is under the arm until its own fix pass anyway.

**Kept:** the refactor it needed. `_Bust` now carries its outline as a chain
of quadratic pieces (`outline`, `pieces()`), which `_rib`, `_bust_over_arms`
and `_bust_bulge` all walk, and which 9b needs. Output identical to the
previous commit on 18 renders (Satoko, Keiko, Katherina; bust 0.25, 0.5, 1.0;
both builds). 9a itself is **deferred to the realistic build's fix pass**.

### 2026-09-25: step 6, traced cuts follow the bust

**Change** (`8e47780`). `_body_knots` gained seven knots at fixed fractions of
the armpit-to-waist run (`_BUST_KNOTS`, 0 to 0.6), each as wide as the
straight shoulder-to-waist line plus the body's own bulge there
(`_bust_bulge`, read off `_bust_shape`). A traced garment then swells in the
bust's shape, not to a point at one knot. At the same fractions on every body
and adding nothing without a bust, they lie on the line the other knots draw:
`ref-out/` byte-identical, and the identity-on-the-traced-body test still
passes.

**Measured.** A traced point 1.0 head radius out at the reference's bust
height, on Katherina: 0.998 flat, 1.072 at `bust = 0.5`, 1.147 at 1.0. More
than the body's own reach (0.11 at 1.0), because placement scales a point by
the knot widths' ratio and this point lies outside the knot line there, so a
garment's side swells a little more than the body under it. New test: a cut
widens at the bust and not at the shoulder or the waist.

**Looked at** (`out/bust/cuts.png`, chest crops at 3x):
- **Katherina** (traced jacket, worn over the arms): the jacket's sides swell
  over the chest and come back in to the waist, smoothly. Works.
- **Keiko** (lab coat, worn under the arms): the bust's outline still sits
  inside her coat's panel like a bracket. Her panel's edge is the armhole
  seam, which is the arm's inner edge, while the over-arm lobe is anchored at
  the torso's side, which lies under her panel. That is 5b's problem, with a
  proposal to the owner: anchor the over-arm lobe at the arm's inner edge
  rather than the torso's side. At the chibi those are within 0.01 of each
  other on a plain tunic, so nothing already signed off would move, and on a
  coat whose panel ends at the sleeve the bust's edge becomes the panel's
  edge bulging over the sleeve, which step 6's knots now make it do.

### 2026-09-24: step 5a, the bust over the arms (taken before step 4)

**Owner's call:** step 3c deferred until a garment exposes the body (no preset
shows any torso today, per the pixel check), and step 5 before step 4, since
the line under the bust is easier to judge once the bust shows.

**Change.** `render_character` builds the chest layers (`_tunic` through
`_crystal_harness`, plus the traced coat worn under the arms) once, draws them
in place, and after `_arms` draws them again inside `_bust_over_arms`: masked
to the lobe a bust adds to the torso (the bust's outline, closed back along
the plain side a stroke inside it), then the outline stroked over the arm.
The katana and staff are left out, being held at the side. `_bust_shape`
holds the bust's points for `_rib` and the lobe alike. Nothing is added at
`bust = 0`; `ref-out/` byte-identical.

**Looked at** (`sweep.py`, 4x zooms):
- **Chibi, plain tunic:** the bust reads, from 0.5 clearly, over both arms,
  tucking back into the side. The notch deferred at step 1 is gone, replaced
  by the under-bust contour as predicted. A small crease at the armpit where
  the sleeve's hem meets the bust.
- **Realistic, tried and rejected.** The arm hangs 0.45 head radii across the
  torso. A lobe to the plain side left a detached strip of chest over the
  arm's middle. Carried in past the arm's inner edge at full depth it hid a
  strip of arm even at a tiny bust, against continuity. Scaled with the bust,
  it floated as a green pad over the arm at 0.25 to 0.75 and read as a ledge
  at 1.0. That is the adult arm's placement, not the bust; the over-arm bust is
  **chibi-range only** (`build < 0.5`, the traced cuts' switch), and at the
  realistic build the bust stays under the arm. Tested.
- **A clip bled.** Clipping applies per layer, so along the soft edge each
  layer under the top one showed through: on Keiko, a grey seam (215 against
  the coat's 238) where her dark dress lies under the white coat. Group opacity
  nearly fixed it (235) but shifts colour; a **mask** composites the chest
  first and leaves no seam (238). Masked, with a user-space region the size of
  the canvas, and an id hashed from the lobe so figures on one sheet cannot
  borrow each other's.
- **Keiko** (coat and traced cut): the bust's outline floats inside the coat
  like a bracket, because her traced coat does not yet bulge with the bust
  (step 6) and her coat and sleeve order is the Keiko-specific part of this
  step (5b). Both wait for the owner.

**Also found, outside this plan:** the eye clips (`eye-l`, `eye-r`) and the
hair clips (`hair-tips`, `hair-front`) use fixed ids, so on a cast sheet every
figure's clip shares one id. It renders because the figures are similar; a
clip that differed per figure would be taken from whichever one the renderer
resolves. Not touched.

Suite: 525 passed, 1 skipped.

### 2026-09-24: step 3b, garments read the body

**Change.** Mostly landed with 3a's refactor (`ba66b6a`): `_tunic` reads the
shared measures and `_rib`, the same ones `_torso` draws. The remaining exact
copies were in the cap sleeve's helpers: `_cap_underside_y` recomputed the
armpit width and `_cap_tip_y` the shoulder drop; both now read
`_torso_at_armpit` and `_shoulder_slope`. `refresh-ref-out.sh --check`:
nothing changed, so not one float moved.

**Scope closed, and what it left.** The robe front (`torso_at_shoulder =
_sleeve_half_w * 0.80`), the coat, the belt (`waist_half_w * 1.03`) and the
apron use their own fractions of the anchors. Those are each garment's own
ease, not copies of the torso line, and putting them on the body would move
pixels, against this step's acceptance. Per the plan they move onto the body
as each is reshaped: the coat and whatever lies over the chest at step 5.

### 2026-09-24: step 3a, the body layer

**Owner's calls before it** (on step 1's sheets): the shape is accepted as a
base; the notch below the arm is deferred to step 5, which turns it into the
visible under-bust contour; steps in the recommended order (3 before 4);
`harness/run.sh` fixed (`f61c3c1`).

**Change.** A byte-identical refactor first (`ba66b6a`): the torso's measures
(`_shoulder_slope`, `_torso_at_armpit`, `_rib_ctrl_y`) and its armpit-to-waist
run with the bust (`_rib`) moved out of `_tunic` into shared module functions.
Then `_torso(sk, p)`: skin, outlined, drawn just before `_neck`, reading no
`Outfit` field (tested). `_BODY_INSET = 1.5` strokes inside the garments.

**Predicted: 0 of 54 PNGs change**, with the slanted cap, a coat and the traced
jacket as the likely exceptions. **Measured, first version: 54 of 54.** Chased
from the smallest (Kyoko's chibi, 6 pixels), three causes, none predicted:

1. The torso's side on the tunic's own curve drew the outline twice, and the
   second pass darkens the first one's antialiased rim along every shared edge.
   A body exactly under a garment can never be pixel-identical; it has to sit
   under the fill. Fixed by the inset.
2. At the realistic build the slanted cap stops short of the arm's outer edge,
   and a shoulder out to the sleeve's width showed past it as a skin crescent.
   Fixed by giving the body the arm's own shoulder: out to the arm's outer edge
   where it leaves the body (`_arm_line`), then down the diagonal to the armpit
   that the arm's top edge follows.
3. The bottom outline showed between the tops of Kyoko's legs.

**Second version: 28 of 54**, two clusters. The nine trouser-wearers at the
chibi showed a skin wedge beside each hip: their trousers are straight columns
at leg width, narrower than `hip_half_w`, which is the owner's standing call in
`_seat_notch_d`, and below a tucked tunic the body is already the legs'
(`_bare_seat`). So the torso now stops in the belt band, where a tucked tunic
ends and the seat starts, at the bare seat's width (both from skeleton-only
functions). The rest were slivers along sloping shoulders, where an inset
measured straight down is less than the same inset square to the line; the
shoulder line is now inset twice as far.

**Third version: 5 of 54**, 5 to 11 pixels each, all at the left stand-collar
tab's corner on the realistic Elara, Krista, Reinhard, Tenno and Viktor: the
tunic left a wedge of page under less than a pixel wide there, and the torso's
outline fills it. **Accepted as a finding**, per the plan's rule, and
arguably cleaner; left side only because of how the tunic's path closes.
`ref-out/` refreshed: the 37 SVGs gain the layer, those 5 PNGs move, no
other PNG does. `ref-out/bases/` (not covered by `--pixels`) refreshed and
compared by hand with `compare_pixels.py`: 0 of 2 differ.

**For step 3c, where the body shows** (`harness/bust/torso.py`, garments off):
the neck's side lines run on down onto the chest; at the chibi a wedge of
page shows between the shoulder tip and the arm; a gap shows between the
torso's end and the legs where nothing covers the seat; the realistic torso
is straight-sided. At `bust = 1.0` the bust shows on the bare body, since
nothing covers the side the sleeve cap used to.

Suite: 524 passed, 1 skipped.

### 2026-09-24: step 2, the pixel check

**Built by a delegate** (`general-purpose`, `sonnet`, in a worktree, 85k
tokens), reviewed and brought in: `./refresh-ref-out.sh --pixels` renders to
the staging area as the other modes do, then `compare_pixels.py` compares every
PNG it would publish (54: chibi, on-white, realistic, three pages) as decoded
RGBA, reporting changed pixels and their box per file. Writes nothing; exits 1
on any pixel change; still prints the SVG byte count, for information.

**Acceptance.** Clean tree: 0 of 54 differ. The delegate's test (a skin colour
changed on Satoko) flagged her PNGs, Kyoko's (derived from her) and the sheet.

**First use, which is also a measurement.** `bust=1.0` set on Satoko for one
run and reverted:

| file | SVG | pixels changed |
| --- | --- | --- |
| `satoko.png` (chibi) | differs | 1113, box (293, 450) to (480, 587) |
| `real/satoko.png` | differs | **0** |
| `kyoko.png`, `real/kyoko.png` | differ | 0 (her coat covers it) |
| `sheet.png` | differs | 602 |

At the realistic build a full bust changes no pixel at all: the arm hides all
of it. At the chibi, 1113 pixels, the notch below the arm. Step 1's
prediction, now counted.

**Also answered by the delegate.** `test_ref_out_matches_the_code`
(`tests/test_smoke.py`) compares SVG text only. A pixel variant in pytest is
feasible (cairosvg and Pillow are in the dev group) but needs the system cairo
library; recommended as a separate test that skips without cairo. Not built;
step 3 is where it would first matter.

### 2026-09-24: step 1c, the shape below the bust

**Change.** The bust is three pieces on `_tunic`'s own rib curve: armpit out to
the fullest point (the curve's point at `bust_y` plus the reach), down and back
in to an under-bust point `_BUST_DROP = 2.0` reaches lower, and the curve's own
remainder to the waist. The tuck arrives on a 45 degree diagonal. New helpers
`_quad_crossing` and `_quad_split` beside `_tunic`.

**Looked at, three versions** (`why_hidden.py`, arms taken away):
1. 1b's shape, reach added on both sides of the split, tapered all the way to
   the waist: a barrel ribcage, not a bust.
2. The tuck arriving level: a bust, but a right-angled shelf against the
   torso's side, which showed as a step just below the arm as rendered.
3. The tuck on the diagonal: a rounded bust coming back into the side. Kept.

**Bug found by looking, fixed, tested.** The first version named the tuck's
lean `slope`, which `_tunic`'s shoulder already reads further down, so every
sleeve tip grew a horn at `bust > 0`. New test
`test_a_bust_changes_nothing_above_the_armpit`, confirmed failing with the
clash put back (3 failed) and passing without it.

**Measured.** Bust-row widths identical to 1b (chibi 0.579, 0.579, 0.631,
0.687; realistic 1.070, 1.070, 1.172, 1.274), as predicted, since the fullest
point is the same point.

**As rendered** (`sweep.py`, whose crop now runs shoulder to waist at every
build; the old fixed window cut the realistic row above the bust): the bust is
under the arm at every value on both builds, as predicted in step 1's
preparation. The only visible trace at the chibi is a small diagonal notch
where the tuck comes back out past the arm's inner edge, from about 0.5 up.
Keiko's traced coat hides all of it. For the owner to judge.

**Zero case.** `refresh-ref-out.sh --check`: nothing changed. Suite: 520
passed, 1 skipped.

### 2026-09-24: step 1b, the bust's height from the armpit

**Change.** `Skeleton.armpit_y` (0.42 of shoulder to waist, the arithmetic
`_sleeve_hem_y` already used, which now reads it) and `bust_y` at
`_BUST_ALONG = 0.30` of armpit to waist, a first guess. Previously 0.45 of
shoulder to waist.

**Predicted vs measured** (torso half-width at the bust row):

| | 0 | 0.01 | 0.5 | 1.0 |
| --- | --- | --- | --- | --- |
| chibi predicted, row 2.066 | 0.580 | 0.581 | 0.635 | 0.690 |
| chibi measured, row 2.065 | 0.579 | 0.579 | 0.631 | 0.687 |
| realistic predicted, row 3.092 | 1.073 | 1.075 | 1.173 | 1.273 |
| realistic measured | 1.070 | 1.070 | 1.172 | 1.274 |

Within 0.004 everywhere: the split now lands about 28% along the curve, no
clamp, and the full reach shows at the row. The arm's ink at the new row still
starts at 0.587 (chibi) and 0.637 (realistic), so as predicted the bulge is
under the arm at every value above about 0.07 (chibi).

**Zero case.** `refresh-ref-out.sh --check`: nothing changed, so moving
`_sleeve_hem_y` onto `armpit_y` changed no float.

### 2026-09-24: step 1a, reach rather than width

**Change.** `Skeleton` stores only the knob, `bust`; `bust_y` and
`bust_reach` are properties derived from the final shoulder, waist and build.
`_tunic` splits its armpit-to-waist quadratic where it crosses `bust_y` and
moves the split point and both neighbouring controls out by the reach, so the
join stays smooth and the halves become the original curve as the reach goes
to zero. At zero it still emits the original single curve.

**Second defect found and fixed with it.** `BodyProfile.applied` and
`waist_shift` replace the shoulder and waist, but the stored `bust_y` and
`bust_half_w` were computed from the unprofiled skeleton, so on every
profiled body the bust sat at a height unrelated to that body's own waist, and
its reach rode the profile's `heads` rather than the chibi build the figure is
pinned to. Derived properties make both impossible.

**Predicted vs measured** (torso half-width at the bust row, head radii,
`drawn_widths.py`):

| | 0 | 0.01 | 0.5 | 1.0 |
| --- | --- | --- | --- | --- |
| chibi predicted | 0.584 | 0.585 | 0.639 | 0.694 |
| chibi measured | 0.583 | 0.583 | 0.624 | 0.668 |
| realistic predicted | 1.077 | 1.079 | 1.177 | 1.277 |
| realistic measured | 1.077 | 1.077 | 1.153 | 1.236 |

Continuity holds. The shortfall at 1.0 (0.026 chibi, 0.041 realistic) is the
bust height: `bust_y` sits so close to the armpit that the crossing lands at
about 5% of the way along the curve, and the split is clamped at 10%, so the
peak lies below the row being measured. That is step 1b's variable, and this
number is the evidence for it.

**Zero case.** `refresh-ref-out.sh --check`: nothing changed. Suite: 513
passed, 1 skipped, before the new tests; the three new tests (skeleton
equality, the bust following a profile and a waist shift, continuity and
monotonic growth) pass.

### 2026-09-24: the first draft read anchors as the figure

Mechanism, measurement and scope in `bust-plan.md`, "What the first draft got
wrong". Taken with `harness/bust/drawn_widths.py` at `504edc3`.
