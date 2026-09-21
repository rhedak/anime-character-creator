# Bust plan

Giving the figure a bust: a skeleton anchor, a silhouette that shows it, and a
per-character size, with male characters at zero and unchanged. Written
2026-09-21 at the owner's request, out of Keiko's clothes campaign
(`keiko-clothes-plan.md`, P7), where the question "should the chest be in front
of the arm" turned out to rest on the figure having a chest at all.

This is a **body** feature, not a garment one. It touches the skeleton and
every garment that draws a torso, which is all seventeen presets, so it is its
own plan rather than another milestone of Keiko's.

**It is also a design task, not a trace.** Keiko's reference is the reason this
came up but it will not settle it: the reference is a chibi and reads close to
flat. `CLAUDE.md`'s direction applies, that references are not a target for new
work and new design is judged by eye against the intent. So the harness in B0
is not a comparison against a reference, it is a sweep to look at.

## What exists now, measured

- **No bust anchor anywhere.** `Skeleton` carries `neck`, `shoulder`, `waist`,
  `hip`, `hem`, `arm`, `leg`, `knee`, `ankle`, `foot`. Nothing between shoulder
  and waist.
- **`_tunic` already curves where a bust belongs.** Its torso runs from
  `torso_at_cuff = waist_half_w + (shoulder_half_w - waist_half_w) * 0.12` at
  the armpit down to `waist_half_w` at the waist, as one quadratic whose
  control sits at `rib_ctrl_y`, 55% of the way down. That curve is the
  insertion point; nothing new has to be invented to hold the shape.
- **`frame` is the precedent for the parameter.** It lives on
  `CharacterParams`, is passed to `build_skeleton(frame=p.frame)` at three call
  sites in `skeleton_for`, and shapes the skeleton's widths rather than being
  read by each part. A bust should thread the same way, so parts read an anchor
  and never a character field.
- **`_body_knots` is how traced cuts would get it for free.** It hands
  `_garment_placement` the landmark heights and half-widths that a cut's
  coordinates are interpolated between. A bust knot there deforms every traced
  garment with the wearer, with no change to any cut's data.
- **The cast is seventeen**: chiyo, daizen, elara, gero, haruto, katherina,
  keiko, krista, kyoko, linnea, reika, reinhard, satoko, satoshi, tenno,
  tomohiro, viktor. Who gets what is B6 and the owner's call.

## The decision this plan rests on: zero is byte-identical

**`bust` defaults to 0.0 and at 0.0 every render in `ref-out/` is unchanged,
byte for byte.** Not "looks the same": identical files. That is the property
that makes a body change safe to land in a cast of seventeen, and it is
checked, not assumed, at the end of every milestone below.

It constrains the design in one useful way: the bust knot added to
`_body_knots` has to sit exactly on the line the existing interpolation already
draws between shoulder and waist when the bust is zero, or the knot alone moves
every traced cut. Anything that cannot be written that way does not go in.

## Milestones

### B0. Decide the shape, and build the sweep

No `src/` change. `harness/bust/sweep.py` renders one character across
`bust = 0, 0.25, 0.5, 0.75, 1.0` side by side at one scale, on white and on
black, at chibi and at realistic, the way `harness/body/head_size_variants.py`
did for the head. Also a second sheet with the same sweep under three
garments: a plain tunic, an open coat, and a traced cut.

Acceptance: the owner picks the range's top end and the look from the sweep
before any of it is wired into a preset. Nothing below is worth building
against a guess about how much is too much.

### B1. The anchor, drawing nothing

`Skeleton` gains `bust_y` and `bust_half_w`. `CharacterParams` gains
`bust: float = 0.0`, threaded through `skeleton_for`'s three
`build_skeleton(...)` calls beside `frame`.

- `bust_y` sits between the armpit and the waist. Its height is a proportion of
  the build like every other anchor, not a character trait: what varies per
  character is the size, not where a bust is on a torso.
- `bust_half_w` at `bust = 0.0` **equals the value the shoulder-to-waist run
  already has at that height**, so the anchor is a no-op until a character asks
  for it.
- `BodyProfile` gains the field too, so a measured body can carry its own.

Acceptance: `refresh-ref-out.sh` reports **nothing changed**, and a test asserts
that a skeleton built with `bust=0.0` is equal to one built without the
argument at all.

### B2. The silhouette

`_tunic`'s armpit-to-waist quadratic reads the anchor: at `bust = 0` it is the
curve it draws today, and above zero it bows out to `bust_half_w` at `bust_y`.
A quadratic reaches only a quarter of the way to its control point, so the
control has to be placed from the wanted width rather than set to it; this is
the same arithmetic `_mock_collar`'s sag needed and it is easy to get wrong by
a factor of four.

Then the other garments that draw a torso silhouette, one at a time, each
looked at before the next: `_coat`, `_robe`, `_apron`.

Acceptance: the sweep from B0 re-rendered at each step; `ref-out/` unchanged at
`bust = 0`; nothing below the waist moves at any value.

### B3. Traced cuts follow the body

A bust knot in `_body_knots`, so `_garment_placement` carries it into every
traced cut. Katherina's jacket and Keiko's lab coat then take the wearer's
bust without their chains being touched.

Acceptance: at `bust = 0` the placement is byte-identical, which is the knot's
no-op property from B1 made visible; above zero, both cuts deform and are
looked at on both wearers.

### B4. Line work, or none

Whether a bust reads at chibi size from silhouette alone, or wants the line
under it that the anime convention draws. `CLAUDE.md` forbids a shading plane
across a garment and allows a second tone only on small elements where it reads
as thickness, so this is a **stroke** if it is anything, drawn like the
placket's centre line, and it is a separate decision from B2 rather than part
of it.

Acceptance: judged at tile size on a cast sheet, not only at 4x. A line that
only works zoomed in is not worth having.

### B5. The chest in front of the arm

The layering question this plan came out of, and it can only be judged once
there is a chest. Observed in Keiko's reference: the coat's own panel edge is
the armhole seam, with the sleeve outside it, and the hand is drawn **over**
the coat, which the hand-shaped notch bitten out of the coat's segment crop
proves. So the reference's order is **sleeve, then coat, then hand**.

That means:

- the traced coat goes back over the arms (`over_arms=True` for `lab_coat`),
  reverting part of Keiko's P5;
- and `_hand` has to come out of `_arms`'s limb list and draw after the coat,
  or the coat covers her hands, which is what happened the first time the coat
  was over the arms.

Acceptance: Keiko's P5, P6 and P7 results re-judged by eye afterwards rather
than assumed to survive, since this reverses the order they were tuned under.
In particular the belt's capless ends, which currently rely on the arm cutting
them off, will terminate inside the panel instead; the reference's belt does
end inside its panel, so that may be right, but it is to be looked at.

### B6. The cast

Values per character, male presets staying at zero. The owner's call, one
sweep per character rather than a number typed in from the roster.

Acceptance: the whole cast sheet, looked at together, which is the only place
the cast's proportions can be compared against each other.

### B7. Integration

The catalogue slider (a `_range` on `CharacterParams`, so `BUILD`'s neighbours
rather than a garment slot), `catalogue.json`, the web tool, the sheets, the
cover, and last `../valley_of_mist`, on the owner's explicit say-so, in that
repo.

## Acceptance, every milestone

- `ref-out/` byte-identical at `bust = 0.0`, checked with `refresh-ref-out.sh`
  and not by eye.
- The B0 sweep re-rendered and looked at, on white and on black, at both
  builds.
- `ruff check`, `ruff format --check`, `pytest` green in the same change.
- The owner's sign-off before the next milestone.

## Risks

- **Seventeen presets.** Every one of them renders through `_tunic`. The zero
  invariant is the only thing standing between this and a cast-wide change, so
  it is a test, not a convention.
- **A bust on a chibi.** The shared chibi is a small child's proportion and the
  cast includes characters written as teenagers. How much of the bust rides the
  build, if any, is a real question and B0 is where it gets answered by
  looking, not here.
- **Traced cuts were traced on a flat body.** Their chains hold the shape the
  reference drew, which has no bust in it. B3 deforms them; whether a jacket
  traced flat still reads right when bowed out is a thing to look at, not a
  given.
- **This reverses part of Keiko's P5.** Her belt and sleeve were tuned with the
  coat under the arms. B5 says to re-judge them rather than assume.
- **Scope.** This is a body feature and the temptation will be to fix the
  figure's other proportions while in there. Her height is still out of scope
  (`keiko-clothes-plan.md`, K7) and stays so.

## Questions for the owner, with recommendations

1. **One knob or two?** Recommended: one, `bust`, for now. Size is what a
   character differs on; separation and projection are a second and third knob
   that can be added later if the sweep says one is not enough.
2. **Does it ride the build?** Recommended: mostly, but not to zero at chibi.
   The cast's chibi is the default render and a bust that only appears on the
   realistic build would not be visible anywhere it matters.
3. **Silhouette only, or line work too?** Recommended: silhouette first (B2),
   decide the line separately (B4) once there is something to judge it against.
4. **Do traced cuts follow the bust?** Recommended: yes (B3), because the
   alternative is a flat jacket on a figure that is not, and the mechanism is
   one knot rather than new data.
5. **Where does Keiko's clothes campaign stand meanwhile?** Recommended: P7's
   second pass is folded into B5 and the campaign waits, rather than building
   an armhole seam that B5 would delete.
