# Bust plan

Giving the figure a bust: a skeleton anchor, a body that carries it, a shape
that shows at chibi size, and a per-character size, with male characters at
zero and unchanged. First written 2026-09-21 at the owner's request, out of
Keiko's clothes campaign (`keiko-clothes-plan.md`, P7), where the question
"should the chest be in front of the arm" turned out to rest on the figure
having a chest at all.

**Rewritten 2026-09-24** after a critical review found that the first draft's
central measurement read skeleton anchors as if they were the drawn figure.
The conclusions built on it are retracted below, in their own section, with
the measured numbers that replace them. The first draft's full text is commit
`257d6b2`. Everything from "The order" down is the current plan; nothing
further down is stale.

This is a **body** feature, not a garment one. It touches the skeleton and
every garment that draws a torso, which is all seventeen presets, so it is its
own plan rather than another milestone of Keiko's.

**It is also a design task, not a trace.** Keiko's reference is the reason this
came up but it will not settle it: the reference is a chibi and reads close to
flat. `CLAUDE.md`'s direction applies, that references are not a target for new
work and new design is judged by eye against the intent.

## Where it stands

The RESUME, scoreboard and findings are in `bust-status.md`; how to work and
the mistakes to avoid are in `bust-strategy.md`. In short, as of 2026-09-25:
steps 1, 2, 3a, 3b, 5a and 6 are done (6 awaiting sign-off), 3c is deferred,
and an anatomy review (below) added step 9, fit and drape, ahead of 5b and 4.
Keiko's clothes campaign waits on 5b.

## Owner's decisions (2026-09-21)

1. **One knob**, `bust`.
2. **It rides the build.** Per-character values are iterated later, not now.
3. **Silhouette first, line work decided separately.** Revisited below: at the
   chibi the line is likely the main lever, so it moves up the order, still as
   its own decision.
4. **Traced cuts follow the bust.**
5. **Keiko's P7 second pass folds into the bust-over-arm step** (step 5) and
   her campaign waits.
6. **Build a real body layer** rather than giving the bust only to garments.

## Owner's decisions (2026-09-24)

1. Step 1's shape is accepted as a base for the steps after it.
2. The notch where the bust shows below the arm is deferred to step 5, which
   makes it the visible under-bust contour.
3. Steps in the recommended order: the body layer (3) before the line (4).
4. Step 3c (where the body shows) deferred until a garment exposes the body;
   no preset shows any torso today.
5. The bust over the arm (5) before the line under it (4).
6. Step 5a signed off at the chibi. The realistic build is broken in its own
   right and gets its own fix pass later; until then its bust stays under the
   arm.
7. The fixed clip ids found at 5a (`eye-l`, `eye-r`, `hair-tips`,
   `hair-front`) are fixed at the appropriate time, not now.

## Owner's decisions (2026-09-25)

1. The anatomy review below is reflected in this plan before any further work.

## What exists now, measured from the ink

All half-widths in head radii from the centre line, right side, rasterized at
4x from `_tunic` and `_arms` drawn on their own (`harness/bust/drawn_widths.py`,
measured at `504edc3`).

| | torso at bust row | arm at bust row | torso at waist | arm at waist |
| --- | --- | --- | --- | --- |
| chibi, `bust = 0` | 0.583 | 0.587 to 1.028 | 0.538 | 0.627 to 1.062 |
| realistic, `bust = 0` | 1.077 | 0.631 to 1.351 | 1.026 | 0.816 to 1.427 |

- **At the chibi the torso's side meets the arm's inner edge** at the bust row
  (0.583 against 0.587) and stands 0.09 clear of it at the waist. The side
  contour is visible, but there is no room beside it: anything that widens the
  torso at the bust row goes straight under the arm.
- **At the realistic build the arm overlaps the torso** by 0.45 at the bust
  row and 0.21 at the waist. A side bulge there is even more hidden.
- **The anchor is not the torso.** `bust_half_w` at zero is 0.930 at the chibi
  against a drawn torso of 0.583, because it is interpolated from
  `shoulder_half_w`, the span across the deltoids. `_tunic`'s own comment
  (`character.py`, above `torso_at_cuff`) says exactly why the ribcage must not
  be derived from that.
- **There is no torso.** This project draws a head, a neck, arms and legs as
  body parts and the torso only as a garment: `_tunic` is the body between
  the shoulders and the hip, and `tunic_color` is not optional.
- **`_body_knots` is how traced cuts would get a bust.** It hands
  `_garment_placement` the landmark heights and half-widths that a cut is
  interpolated between, piecewise linear from shoulder to waist.
- **The cast is seventeen**: chiyo, daizen, elara, gero, haruto, katherina,
  keiko, krista, kyoko, linnea, reika, reinhard, satoko, satoshi, tenno,
  tomohiro, viktor.

## The invariant: at zero, the pixels do not move

**`bust` defaults to 0.0, and at 0.0 every PNG in `ref-out/` is unchanged,
compared as decoded pixels.** The SVG text may change (a body layer adds
elements even where it adds no visible pixel), so `refresh-ref-out.sh`'s byte
report is no longer the whole test; step 2 builds the pixel check. Where a
step adds nothing to the SVG, byte-identical is still expected and checked.

A second property, new in this rewrite: **`bust` is continuous at zero.** A
bust of 0.01 moves no outline by more than 0.01 head radii. The first draft
had no such test, and its silhouette jumped 0.37 at the first step off zero.

## What the first draft got wrong (retracted 2026-09-24)

Each claim as the first draft made it, then what was measured instead. Scope:
these retract the measurements and the conclusions resting on them, not the
owner's decisions or the parameter's plumbing, which stand.

1. **"`bust_half_w` at `bust = 0.0` equals the value the shoulder-to-waist run
   already has at that height, so the anchor is a no-op."** *Retracted.* It
   equals the value on the straight line from `shoulder_half_w` to
   `waist_half_w`, which is what `_body_knots` interpolates, and not what
   `_tunic` draws. It was a no-op only because nothing read it at zero. As
   soon as anything did, the chibi torso at the bust row went 0.583, 0.950,
   1.013, 1.080 for `bust` 0, 0.01, 0.5, 1.0: a slab switched on at the first
   step, with the dial covering only the last 0.13 of it.
2. **"B0's result: the torso at `bust_y` runs 0.930 flat to 1.061 at
   `bust = 1.0`, and the arm hangs from 0.752 to 1.150."** *Retracted.* Both
   pairs were skeleton values (`bust_half_w`, and `arm_x` plus or minus
   `arm_half_w`), not the figure. Drawn, the torso is 0.583 and the arm 0.587
   to 1.028. The conclusion that a side bulge hides behind the arm survives,
   for a different reason: the torso's edge is already touching the arm, not
   buried under it.
3. **"At the chibi the waist sits 0.24 head radii inside the arm, so the whole
   torso from armpit to hip is behind the arms and none of its shape is
   visible. At the adult build the waist is outside the arm's inner edge and
   the shape reads. The invisible-bust problem is the invisible-torso problem,
   and it is specific to the chibi."** *Retracted, and inverted.* Measured
   from the ink, the chibi's waist stands clear of the arm and its taper shows;
   it is the realistic build whose arm overlaps the torso's side.
4. **"A quadratic reaches only a quarter of the way to its control point ...
   easy to get wrong by a factor of four."** *Retracted.* A quadratic's
   midpoint lies half way from its chord's midpoint to its control point; the
   factor is two, which is what `_mock_collar` and the round neckline in
   `_tunic` already use.
5. **The sweep (`out/bust/sweep.png`) and the bare study (`out/bust/bare.png`)
   as grounds for judging the bust's look.** *Void.* Both rendered the jump in
   (1), so every nonzero column showed the slab. In the bare study the only
   visible effect was a notch pinched in at the waist below the arm. Its
   realistic row is also cropped at the collarbone (the crop stops 4.2 head
   radii below the head centre), so the realistic torso was never on the page.
6. **L1 as written, "a torso shaped exactly as `_tunic` draws it, immediately
   before `_tunic`, acceptance pixel-identical."** *Withdrawn.* A copy of a
   shape drawn under the same shape is pixel-identical by construction, so the
   test could not fail. The copy would also carry garment decisions into the
   body (sleeve caps, a neckline depth that depends on the collar, a tucked
   hem, a traced-coat special case), which L2 would then have the tunic read
   back: circular. And "immediately before `_tunic`" is after `_skirt`,
   `_hakama` and `_hanging_sleeves`, which is wrong the moment the torso has a
   shape of its own; on Keiko, whose tunic tucks at the belt, a torso running
   to the hip would paint skin over the top of her skirt.
7. **L5, "the question becomes where does the torso sit in the order".**
   *Withdrawn.* Moving the torso over the arms changes all seventeen presets,
   male ones included, and a front-view torso does not lie over its arms. Only
   the bust does, and only when there is one.

## Anatomy review (2026-09-25)

Asked by the owner after step 6: how anatomically correct is the bust as
built? Stylised and partly right. Each point says where the plan now answers
it. Canon figures are the standard figure-drawing proportions, not measured
here; the rest are this code's numbers.

**What holds up:**

- **In front of the arm.** Seen from the front with the arms hanging, the
  breasts stand forward of the arm's inner edge. Step 5a does this at the
  chibi.
- **Height, at the adult build.** The fullest point is 2.05 head heights down
  from the crown; the canon puts the nipple line at about 2. Approximate,
  since the canon is an 8-head figure and ours is 6.
- **Outline.** A gentle slope in, a fuller rounded lower half, and back in to
  the torso below: the usual teardrop in profile.
- **Size.** At most 0.2 head radii beyond a torso about 1.07 wide at that
  height, about 19%: a moderate bust from the front.

**What does not, in order of how much it costs:**

1. **Clothes follow the body's tuck under the bust.** Only a skin-tight garment
   does that. Loose cloth hangs from the fullest point and falls clear of the
   torso narrowing below it, so the tuck disappears under it. Affects the
   tunic, the coats and the traced cuts (step 6 widens them by the body's own
   profile, tuck included). **New step 9b.**
2. **Only the side outline exists.** From the front a bust reads mostly from
   the curves under each breast and some separation between them. **Step 4,
   widened below**, and what line suits depends on 9b: on a draped garment the
   cue is the cloth's fold from the fullest point, not the anatomical fold.
3. **The bulge starts at the armpit.** The upper chest runs down from the
   armpit first, often a little concave there, before the breast begins; ours
   leaves the armpit already moving out. **New step 9a.**
4. **At the chibi, anatomy mostly does not apply.** The shared chibi is a small
   child's proportion, so there it is stylisation, judged by eye. Recorded so
   the canon is not quoted against the chibi.
5. **The realistic arm hangs 0.45 head radii across the torso.** Hanging arms
   meet the torso's side rather than lying across it, and this is why the
   bust could not come over the arm there (5a). **Deferred** to the realistic
   build's own fix pass.
6. **The body is simple.** No pectoral or upper-chest shape, and nothing for a
   male chest at `bust = 0`. **Deferred** (below); out of this plan's scope.

## The order

One sequence, each step signed off by the owner before the next. As of
2026-09-25 the remaining order is: **step 6's sign-off, then 9 (9a, 9b), then
5b, then 4, then 7 and 8.** Step 9 goes before 5b and 4 because both depend on
it: Keiko's coat is a loose garment whose edge over the sleeve is exactly what
drape reshapes, and the line under the bust is a different line on a draped
garment than on a fitted one.

### Done: B0, the sweep harness

`harness/bust/sweep.py` renders one character across `bust = 0` to `1.0`, on
white and black, at both builds, under a plain tunic and a traced cut. The
harness stands; its readings are void (retraction 5) and it is re-run after
step 1.

### Done: B1, the parameter and the anchor

`CharacterParams.bust` threaded through `skeleton_for`'s three
`build_skeleton` calls beside `frame`, and `Skeleton.bust_y` and
`bust_half_w`. `_BUST_ALONG = 0.45` of the way from shoulder to waist,
`_BUST_REACH` 0.10 head radii at the chibi to 0.20 at the adult build, both
first guesses. `BodyProfile` did not gain the field: it holds measured
proportions and nothing measures a bust yet. `bust_y` and the plumbing stand;
`bust_half_w` is replaced in step 1.

### Step 1. Reach, not width (done 2026-09-24)

The skeleton carries **`bust_reach`**, the extra half-width a bust adds, zero
at `bust = 0`, instead of an absolute `bust_half_w`. Each consumer adds it to
its own base: `_tunic` to the torso curve it already draws, `_body_knots`
(step 6) to its straight line. One number cannot be a no-op for two consumers
that disagree about the width at that height; an offset is a no-op for both.

`_tunic`'s silhouette is rewritten on that base: at the bust row the torso is
its current width plus the reach, and below the bust it comes back in to the
ribcage line rather than running straight to the waist, so a bust reads as a
bulge on the torso and not as a torso widened to a point.

Also here, because the sweep is useless without them: `bare.py`'s crop taken
from the figure's own extent so the realistic torso is on the page, and both
harnesses re-run.

Acceptance:
- A test that `bust = 0.01` moves the torso's widest point at the bust row by
  under 0.01 head radii, and that the width grows monotonically with `bust`.
- `ref-out/` byte-identical at `bust = 0` (no layer is added yet).
- The sweep re-rendered and looked at. Expect the bulge to be mostly under
  the arm at both builds; that is steps 4 and 5's problem, and this step is
  judged on the shape with the arms drawn at a third opacity
  (`why_hidden.py`'s view), not as rendered.

### Step 2. A pixel check for `ref-out/` (done 2026-09-24)

A script that decodes each `ref-out/` PNG and compares pixels against the
committed version, reporting per preset the count of changed pixels and their
bounding box. It exists before any step that changes the SVG without meaning
to change the picture. `refresh-ref-out.sh --check` keeps its byte check; this
sits beside it.

Acceptance: it reports zero for an unchanged tree, and a nonzero count with a
sensible box for a deliberate one-pixel edit made and reverted to test it.

### Step 3. The body layer (3a, 3b done 2026-09-24; 3c deferred)

**3a. A torso from anchors only.** `_torso(sk, p)` in the skin tone, built
from `neck_half_w`, the shoulder, the armpit, `waist_half_w` and
`hip_half_w`, and reading no `Outfit` field at all. Drawn early, with `_neck`
and before the legs and every garment, not beside `_tunic`. At `bust = 0` it
sits inside every garment's coverage.

Acceptance: step 2 reports zero changed pixels on all seventeen presets at
both builds. Here the test can fail: any preset whose pixels move has a
garment that does not cover the body it is on, and that is a finding to
record and look at, not a number to tune away.

**3b. Garments read the body.** The torso line that `_tunic` computes today
(`torso_at_cuff`, the rib control, the waist) moves to one place both read, so
the tunic is the body plus its own allowance rather than a second copy of the
proportions. `_coat`, `_robe_front` and `_apron` follow as each is touched.
Acceptance: pixels still identical.

**3c. Where the body shows.** Necklines, hems, sleeveless arms: the places no
garment covers the body. Looked at on every preset with a neckline, at 4x.

**Done 2026-09-25** at the owner's call: the neck's lines, the torso to the hip,
the shoulder rounded over the arm, a smooth return under the bust
(`bust-status.md`).

### Step 4. The line under the bust

The front-view cues the anatomy review found missing: the curve under each
breast and, where the neckline allows, some separation between them, not only
the one under-bust stroke first planned. Which cue fits depends on step 9b: on
the body and on a fitted garment it is the fold under the breast; on a draped
garment it is the cloth's own fold falling from the fullest point, with the
underside hidden. Originally: at the chibi the side contour is taken by the
arm, so the one cue that needs no layering change is a stroke on the chest's
front, the under-bust curve the anime convention draws. A **stroke**, drawn like the placket's centre line,
never a second tone: `CLAUDE.md`'s no-shading-plane rule applies. It is still
the owner's decision whether to have it at all.

Acceptance: judged at tile size on a cast sheet, not only at 4x. A line that
only works zoomed in is not worth having.

### Step 5. The bust over the arm

The layering question this plan came out of. What goes over the arm is the
bust's own shape, drawn after `_arms` only when `bust > 0`, not the torso: at
zero nothing is drawn and no preset moves.

**5a, done 2026-09-24, signed off:** the chest layers drawn again after the
arms, masked to the lobe the bust adds, with its outline on top. Chibi-range
only; at the realistic build the arm lies across the torso and the bust stays
under it (anatomy review, 5).

**5b, done and reversed 2026-09-25** at the owner's call, replaced by 5c below. It was: (coat over the arms, hands after it, the belt to the coat's edge; the arm-edge anchor below turned out unnecessary, see `bust-status.md`). **As proposed:** anchor the over-arm lobe at the arm's inner
edge rather than the torso's side. On a plain tunic at the chibi the two are
within 0.01 head radii, so 5a does not move; on her coat, whose panel edge is
the armhole seam at the arm's inner edge, the bust's edge becomes the panel's
edge bulging over the sleeve, which step 6 now makes it do. After step 9b,
whose drape changes that edge below the fullest point. Then the rest of her
coat, as follows.

**5c, done 2026-09-25:** the arm in front of the coat and behind the bust. The
lab coat back under the arms (P5's order), and the bust's outline drawn only
where it lies over an arm, so it leaves the arm's inner edge and joins it
again. The hands and belt stay as P5 and P6 left them for Keiko.

What follows is the plan 5b was written from, kept as the record. For Keiko
the same step settles her coat. Observed in her reference: the
coat's panel edge is the armhole seam, with the sleeve outside it, and the
hand is drawn **over** the coat, which the hand-shaped notch bitten out of the
coat's segment crop proves. So the order is sleeve, coat, hand:

- the traced coat goes back over the arms (`over_arms=True` for `lab_coat`),
  reverting part of her P5;
- `_hand` comes out of `_arms`'s limb list and draws after the coat, or the
  coat covers her hands, which is what happened the first time.

Acceptance: Keiko's P5, P6 and P7 results re-judged by eye, not assumed to
survive an order they were not tuned under. In particular the belt's capless
ends, which currently rely on the arm cutting them off, will end inside the
panel instead; her reference's belt does, so that may be right, but it is to
be looked at.

### Step 6. Traced cuts follow the body (done 2026-09-25, awaiting sign-off)

`bust_reach` added to `_body_knots` at `bust_y` (in the reference body's knots
as zero), so `_garment_placement` carries it into every traced cut. At zero the
added knot lies on the existing shoulder-to-waist line and placement is
unchanged; above zero Katherina's jacket and Keiko's lab coat deform without
their chains being touched. Traced cuts only draw at the chibi (`_wears_cuts`).

Acceptance: at `bust = 0` placement byte-identical; above zero both cuts
looked at on both wearers. Cuts were traced on a flat body, so whether a
jacket bowed out still reads right is a thing to look at, not a given.

As built: seven knots at fixed fractions of the armpit-to-waist run, their
widths following the body's own bulge, so a cut swells in the bust's shape.
That includes the body's tuck, which step 9b replaces with drape for the
cuts, since a jacket is a loose garment.

### Step 9. Fit and drape (added 2026-09-25, from the anatomy review)

Numbered 9 because it was added last; it runs before 5b and 4.

**9a. The bust starts below the armpit.** *Tried 2026-09-25 and deferred to the realistic build's fix pass: it pinched into a hook at the chibi and read as a knob at the adult build (`bust-status.md`).* The upper chest runs down from the
armpit before the breast begins, a little concave where the arm's front fold
meets it, and the bulge starts there rather than at the armpit itself.
`_bust_shape`'s upper piece changes; the fullest point, the reach and the
tuck do not. Continuity at zero is kept, and the step 1 shape the owner signed
off is re-judged on the sweep, not assumed to survive.

**9b. Loose garments hang from the fullest point.** Below the fullest point a
loose garment's side falls clear of the body's tuck, straight or gently
tapering to its own waist, instead of following the body in. The body keeps
the tuck; so would a fitted garment, if one is ever made. Recommended: fit is
a property of the garment kind, not a new knob (the body tucks; the tunic, the
coats, the robe front and the traced cuts drape), with a per-outfit `fitted`
flag only when a costume needs one. It reaches three places: `_rib` (the
tunic's path gains a draped form), `_bust_over_arms` (the lobe of a draped
garment runs from the fullest point down until the fall meets the arm or the
waist, not back to an under-bust point) and `_body_knots` (a draped cut's
bulge is held below the fullest point and fades to the waist rather than
returning). The drape grows with the reach, so a bust of 0.01 still moves
nothing by more than 0.01.

Acceptance: `ref-out/` unchanged at `bust = 0`; the continuity test kept; the
sweep and the cuts sheet looked at, and a draped tunic judged at tile size on
a cast sheet beside a bare body, since a drape that only reads at 4x is not
doing its job.

### Step 7. The cast

Values per character, male presets at zero. The owner's call, one sweep per
character rather than a number typed in from the roster.

Acceptance: the whole cast sheet, looked at together.

### Step 8. Integration

The catalogue slider (a `_range` on `CharacterParams`, beside `BUILD`, not a
garment slot), `catalogue.json`, the web tool, the sheets, the cover, and last
`../valley_of_mist`, on the owner's explicit say-so, in that repo.

## Acceptance, every step

- At `bust = 0`: step 2's pixel check reports zero changes; where the step
  adds nothing to the SVG, `refresh-ref-out.sh` reports nothing changed too.
- Continuity at zero holds (step 1's test, kept for every later step).
- Numbers about the figure come from the drawn ink (`drawn_widths.py` or its
  successor), never from skeleton anchors.
- The sweep re-rendered and looked at, on white and black, at both builds.
- `ruff check`, `ruff format --check`, `pytest` green in the same change.
- The owner's sign-off before the next step.

## Deferred, with where each was found

- ~~Step 3c~~, done 2026-09-25. What it left (the arm's slanted top on a bare
  body) is the arm's garment logic, recorded in `bust-status.md`.
- **The realistic build's own fix pass**: the arm across the torso (anatomy
  review, 5), and with it the bust over the arm there (5a).
- **The fixed clip ids** (`eye-l`, `eye-r`, `hair-tips`, `hair-front`), found
  at 5a; fixed at the appropriate time.
- **Chest anatomy beyond the bust**: a pectoral and upper-chest shape, and a
  male chest at `bust = 0` (anatomy review, 6). Out of this plan's scope.

## Risks

- **Seventeen presets.** Every one renders through `_tunic`, and step 3 adds a
  layer under all of them. The pixel invariant is the only thing between that
  and a cast-wide change, so it is a test, not a convention.
- **A bust on a chibi.** The shared chibi is a small child's proportion and the
  cast includes characters written as teenagers. How much rides the build is
  answered by looking at the sweep after step 1, not here.
- **The arm takes the side at both builds.** If neither the line (step 4) nor
  the bust over the arm (step 5) reads at tile size, the remaining lever is
  the arms' own placement, which touches every figure and every garment. Noted,
  not recommended.
- **This reverses part of Keiko's P5.** Step 5 says to re-judge her belt and
  sleeve rather than assume.
- **Drape changes a look already signed off.** Step 5a's chibi bust was
  approved with the tunic tucking under it. 9b removes that tuck from every
  loose garment, so 5a is shown again beside it for the owner to compare,
  not assumed to carry over.
- **Scope.** The temptation will be to fix the figure's other proportions
  while in the body layer. Her height is out of scope (`keiko-clothes-plan.md`,
  K7) and stays so.
