# Katherina accessories plan

Plan for closing the gap between the current `katherina` preset and the
owner's AI reference (`../time_slider_katharina/style-anchors/katherina_grok/katherina_grok.jpg`),
across four milestones: hairstyle, witch hat, staff, and Kou (her bat
familiar). Written 2026-09-17. Each milestone is its own piece of work,
not a quick pass, per the owner's explicit framing: this is a campaign,
the same shape as `character-roster-plan.md`'s phases, not four small
edits in one sitting.

## What the reference is, and isn't

Same distinction `character-roster-plan.md` already draws for the
fourteen-character roster references, and it applies here without
modification: **the grok image is a reference for the design, not for
the style.** What it settles is what Katherina is wearing and holding;
it says nothing about how this generator draws anything, which stays
flat, hard-edged, skeleton-relative SVG per `CLAUDE.md`'s hard
constraints.

Two things this rules out, stated plainly because they're easy to reach
for by accident:

- **No pixel from the reference, or from the `katherina_grok/layer-*.png`
  files, is imported or composited in.** *Retracted in part, 2026-09-17:*
  this bullet first said they could not be *traced* either; the owner
  corrected that, and tracing (measuring shapes with code and fitting
  flat curves to them) is this repo's established method, see
  `.claude/skills/trace-reference/SKILL.md`. The layer exports are
  regenerated variants rather than crops of the composite, so shapes are
  traced off `katherina_grok.jpg` itself.
- **Texture does not survive.** The reference's wood grain on the staff,
  the gem facets, the cel-shaded hair sheen: all style, discarded the
  same way the roster plan discarded the fourteen references'
  brushwork. What transfers is silhouette and flat color only.

## What's already close, so this isn't a recolor job

Sampled directly off `katherina_grok.jpg` (median color over a small
patch, picked by eye against a coordinate grid overlay, not a single
pixel or a histogram bucket):

| Surface | Current `KATHERINA` preset | Sampled from reference |
| --- | --- | --- |
| Hair | `#4b2c5e` | `#3b2550` / `#3e2656` |
| Jacket (`coat_color`) | `#12152a` | `#171c2f` |
| Collar (`collar_color`) | `#c9a13b` | `#c48f3d` |
| Skirt | `#241f30` | `#261e36` |
| Belt | `#3a3226` | `#31281e` |

All five are within a few hex points of what's already shipping. The
palette is not the gap. The gap is entirely structural: no hat, no
staff, no familiar, and a hairstyle that doesn't match the reference's
silhouette. Don't spend a milestone re-deriving colors that already
work; each part below inherits the existing preset palette unless its
own section says otherwise.

## The four milestones, and why this order

1. **Hairstyle.** Already proven, see below: swapping `hairstyle` from
   `long_traced` to the existing `long_center_part` lands the reference's
   symmetric center-part bangs with no new geometry at all. Goes first
   because it's the cheapest possible confirmation that the reference is
   actually a good target before any real design work starts on it.
2. **Witch hat.** A head accessory. This generator has precedent for
   exactly this shape of thing: Keiko's glasses, Krista's goggles, and
   Chiyo's headscarf are all "something worn on the head, sized against
   the hair mass or the skull, at a specific z-order relative to the
   hair" (`character-roster-plan.md`, "The cap and the glasses" and
   "Krista's goggles"). The hat is new geometry, but not a new *kind* of
   problem. Goes second because the existing pattern gives it a real
   head start.
3. **Staff.** A held prop. This generator has **no** held-prop
   machinery anywhere. `character-roster-plan.md` task 28, "Revisit
   props" (Tenno's cane, Daizen's chest), is still open and unchecked:
   nobody has built one yet. Katherina's staff is this generator's
   first prop, not just her third accessory, which is why it's a
   separate milestone from the hat rather than "two accessories, do them
   together." Goes third: after the hat, so the hat milestone's
   z-order/sizing lessons are fresh, but before Kou, because a static
   held object is a smaller unknown than a whole second figure.
4. **Kou.** No precedent at all. Every part this generator draws so far
   is a piece of a human skeleton (`Skeleton`, `head_r`/`shoulder_y`/etc.)
   or something worn on one. A bat familiar is neither. This is the
   milestone most likely to need a real design decision before any SVG
   gets written (see its own section below), so it goes last, after the
   other three have each banked one more instance of "how does a new
   accessory anchor itself to the skeleton without drifting the way the
   goggles/ponytail collision did."

## Milestone 1: hairstyle

**Status: tried and reverted, 2026-09-17. Skipped for now, not
retried without a new ask.** Applied `long_center_part`, wired it into
the preset and the book's cover, looked at both builds: matched the
reference's symmetric center-part bangs as predicted, tooling stayed
green throughout. The author then looked at it beside the original
`long_traced` cut and preferred the original, so it was reverted (`git
checkout` in both repos; nothing had been committed). This is a
preference call, not a defect: nothing about the render was wrong, the
reference match itself held up, the owner just liked the prior cut
more once both were in front of them. Leaving `long_traced` in place.
The proof-of-concept finding below is kept for the record; it's still
true, it's just not what's shipping.

Task:

- [ ] **1a.** Change `KATHERINA.hairstyle` from `"long_traced"` to
      `"long_center_part"` in `presets.py`. Update the preset's own
      comment block, which currently doesn't explain the hairstyle
      choice at all (it explains `hair_tail` instead, for a ponytail
      that this milestone doesn't touch); add a line citing the grok
      reference and this doc.
- [ ] **1b.** Re-render `style-anchors/katherina.png`/`.svg` and the
      cover in `../time_slider_katharina` (`tools/generate_cover.py`,
      per that repo's own docstring) so the book's checked-in art
      actually reflects the change.
- [ ] **1c.** Look at both builds (chibi and realistic), per this
      repo's own standing rule to check both whenever anything above
      the neck changes.

## Milestone 2: the witch hat

**Status: done, 2026-09-17 (third pass): approved, committed
(`1592dc7`), and in the book's cover and style anchors.** The first two
passes (committed as `1f82b8c`, "witch hat") placed hand-measured
landmarks, and the author's read was that the hat did not look traced
and did not fit her head. Both complaints had one cause, recorded here
rather than deleted: the calibration was wrong (142.9 px per head radius
with the centre 45 px left of the face, off an eye-to-chin run that
assumed proportions the chibi does not have), and the result was then
squashed by a different factor per axis to fit a canvas ceiling set for
hair. The third pass:

- Calibrated off the face itself: the reference's widest face row and
  chin against our own rendered chibi face give 173.7 px per head radius
  on *both* axes independently, which is the check that the scale is
  right.
- Traced every region's actual contour (crown, band, the three pieces of
  the bow, brim top, underside), isolated as connected components of the
  reference's non-outline fill, with `trace_lib.boundary`/`fit_closed`,
  plus the three crease strokes by the curl. No hand-placed points and no
  rescale.
- Made the canvas give way instead of the hat: `build_skeleton` takes a
  `min_hair_margin` floor, and `character.hat_hair_margin(p)` supplies it
  wherever a character's skeleton is built (`render_character`'s default,
  `cover.py`). `sheet.py` is deliberately left alone: a cast sheet holds
  every member at one body scale, and no sheet has a hat-wearer.
- Split the brim across the figure: `_hat_underside` (the far side, drawn
  first, behind the hair) and `_hat` (the near side with crown, band and
  bow, drawn last). Our hair is narrower under the brim than the
  reference's, and with one layer the page showed through the gap.
- Colors are the reference's own region medians: `#201e29` for the hat,
  `#3c2456` for the band, the underside a `shade()` of the hat landing on
  the reference's `#12121c`.

The checklist below is the original plan, kept for the record; 2b's
"sized against `_hair_edge_x`" did not survive contact: the brim is wider
than every haircut's crown, so the hat's own traced shape is the answer.

Reference geometry, read off the crop in this session: a wide brim that
curls asymmetrically (down on the wearer's left, up into a small
pointed lift on the right), a tall crown that bends forward partway up
rather than standing straight, and a band around the base in a color
close to the hair's own purple, with a small dark buckle or bow on the
band. The hat sits low enough that hair still shows in front of it
(the fringe) and past it (the long fall), which is the same "hair
inside, garment outside" relationship the headscarf already solves for
Chiyo.

Design questions to settle before writing shapes, in the "Open
questions" section below rather than guessed at here:

- [ ] **2a.** New field(s) on `CharacterParams` (most likely a
      `hat_color` and a `hat_band_color`, neutral-default-off per
      `CLAUDE.md`'s rule that a preset difference lives in the params,
      never hardcoded into the part function). Decide whether a single
      `has_hat: bool` gate is needed or an unset/empty color is enough
      of a signal, matching how `Outfit`'s optional garments already
      work.
- [ ] **2b.** `_hat` part function. Brim width and crown height sized
      against `_hair_edge_x` (the same function the headscarf already
      uses to read the hairstyle's own mass contour rather than the
      bare skull), so it fits `long_center_part` correctly and doesn't
      silently break if the preset's hairstyle ever changes again.
- [ ] **2c.** Z-order. The brim likely draws after the hair mass but
      before the fringe/front strands, the same layering headscarf
      uses, so the reference's peekaboo strand in front of the hat
      band still reads. Check this doesn't collide with the small
      ring/loop hair accessory already in the current design, the same
      class of problem the goggles-vs-ponytail-tie collision was.
- [ ] **2d.** Render against the reference at tile size (the
      "judged at the size it's seen" rule from the roster plan), both
      builds.
- [ ] **2e.** Wire into `KATHERINA`, rewrite the preset's existing
      comment ("no hat shape exists in this tool yet; deliberately left
      off" is no longer true once this lands), re-render the book's
      cover and style anchors.

## Interlude: her body (between milestones 3 and 4)

**Status: done, 2026-09-17, as a reusable body type; not yet in the
book's cover/style anchors (author's call to hold the cover).** The shared
chibi is 2.4 heads; her reference is 3.47, with a high belt and tall boots.
A per-preset `heads` would not have worked: every tool renders by build
name (`--build chibi`, `BUILDS[p.build]`) and would put her back at 2.4.
Instead:

- `BodyProfile` (skeleton.py): a figure height plus whichever landmarks
  were measured, in head radii, laid over a built skeleton; `build` stays
  the named build's, so the face and limb tapers are the chibi's.
- `BODY_TYPES["tall_chibi"]` (character.py) and `CharacterParams.body`, a
  name like `hairstyle` so URL state stays flat, applied by
  `character.skeleton_for(p, heads)` at the chibi build only. It replaced
  the hat-margin call sites (`render_character`, `cover.py`, the snapshot
  test); `sheet.py` still builds its own, deliberately. Exposed as
  `--body`, as `bodies` in the catalogue (`BODY_LABELS`), and as a Body
  select beside the build slider in the web tool.
- Landmarks were solved from the reference's fill components through the
  parts' own formulas (belt band -> waist and hip, boot shaft -> ankle and
  knee, skirt flare -> hip and hem widths). The body type keeps only what
  describes a figure. What belongs to Katherina's design stays on her
  preset, fitted by measuring our render against the reference:
  `coat_length` 0.49 (hem 3.27 vs 3.30), `hair_length` 0.83 (ends 2.61 vs
  2.60), `right_arm_out` 42 (grip 0.21 head radii off the reference's; a
  straight arm cannot bend at the elbow). A fitted `arm_x` was tried and
  dropped as design-specific. Scripts: `harness/body/`.
- Not proportion, so not done here: the reference's lapelled coat and shirt
  collar are garment design, left as the shared coat and collar.
- **Not usable yet.** The shared garments look mangled on this body from the
  neck to the hem; porting the clothes and neck is its own campaign,
  `katherina-clothes-plan.md`, between this interlude and milestone 4.

## Milestone 3: the staff

**Status: done, 2026-09-17: approved, committed (`195094a`), and in the
book's cover and style anchors.** Decisions,
recorded where the checklist below asked for them:

- **3a, anchor: not a general `Prop`.** A staff shape plus two `Outfit`
  colours (`staff_color`, `staff_crystal_color`, catalogued as
  `STAFF`/`STAFF_CRYSTAL`), placed off `_hand_centre(sk, p, -1)`, the
  character's own right hand. Generalizing to Tenno's cane stays with
  roster-plan task 28; `_hand_centre` and the arm swing are the reusable
  parts.
- **3b, pose: an arm swing was needed after all.** The hanging chibi hand
  sits inside the hair's width (x = -0.84 head radii against the
  reference's -1.85), so a staff through it put the ornament over the
  hair. The author chose holding the arm out: `CharacterParams.right_arm_out`
  / `left_arm_out` (degrees, 0 byte-identical), rotating tube, cuff and
  hand about the sleeve hem, with a joint cap. `KATHERINA` uses 44, which
  puts the hand at (-1.69, 2.41).
- **3c, geometry: traced, not drawn.** Same calibration as the hat. Wood =
  the reference's brown fill components, the shaft bridged across the rows
  its fist hides; strands = the same fills split at a darker threshold
  (structural lines separate them, grain does not); crystal cut from its
  glow by colour, with dark and light faces from smoothed brightness bands.
  Placement (`_staff_placement`): the grip goes to the hand; above it one
  scale puts the ornament's top at the reference's height against the
  head; below it the shaft is shortened along its own axis to reach the
  ground (0.42 at chibi, since the reference's figure is ~3.5 heads and
  ours 2.4), after smoothing that stretch so its knots don't bunch into
  spikes; a minimal inward shift keeps the ornament on the hat-narrowed
  canvas. Scripts: `harness/trace_staff/`.

The checklist below is the original plan, kept for the record.

Reference: a dark, gnarled wooden shaft with forking, branch-like prongs
near the top, cradling a faceted amber/orange crystal. Per the
texture rule above, the wood grain and facet lines don't survive; what
transfers is a dark brown shaft, a forked silhouette at the top, and a
warm amber crystal shape, in flat color with `shade()` doing what
little dimensional work a crystal needs (the same derivation the
goggles' lens already gets: a base color and its `shade()`-derived
tone, not a hand-picked second color).

This is a machinery task before it's a Katherina task, per
`character-roster-plan.md`'s own stated rule ("machinery gets its own
task, before its first wearer"):

- [ ] **3a.** Decide the anchor. A held prop needs a point on the
      skeleton to hang off (most likely off the hand/wrist anchor
      `_arms` already uses), and a decision on whether it's generic
      (a `Prop` concept other characters could reuse for Tenno's cane
      later) or specific to this preset for now, with generalization
      explicitly deferred the way task 28 already defers Tenno's and
      Daizen's props. Record the decision either way; don't leave it
      implicit in the code.
- [ ] **3b.** Decide the pose. `CLAUDE.md` states plainly that "poses do
      not exist" in this generator yet. The reference holds the staff
      upright at her side, gripped low, which is closer to "planted
      beside her" than "raised and casting," so this probably doesn't
      need a new arm pose at all, just a shaft anchored near the closed
      hand and rising past the shoulder. Confirm this by rendering it,
      not by assuming it.
- [ ] **3c.** Geometry: shaft, fork, crystal, as flat shapes.
- [ ] **3d.** Render, iterate at tile size, both builds.
- [ ] **3e.** Wire into `KATHERINA`, re-render the book's cover and
      style anchors.

## Milestone 4: Kou

No part of this generator has ever drawn anything that isn't a human
figure or something worn or held by one. Kou is a small bat-like
creature, established in the book's own prose
(`../time_slider_katharina/docs/continuity_reference.md`'s Kou entry):
small, dark-furred, wings that fold tight or snap flat depending on his
mood, usually perched on Katherina's shoulder (repeatedly stated on the
page, e.g. "Kou landed light on my shoulder"). That last detail is
worth leaning on: a shoulder perch is a fixed, small, skeleton-relative
anchor point, which sidesteps the "no poses" problem the staff milestone
also has to navigate, since a perched creature doesn't need a pose so
much as a place to sit.

This milestone needs a real design pass before any shape code, not a
geometry guess:

- [ ] **4a.** Decide what "drawing a bat" means in this generator's
      idiom: does Kou get his own tiny internal skeleton (a body,
      folded wings, ears) built the way `Skeleton` builds a human figure,
      or is he a fixed small compound shape (a handful of flat paths)
      scaled and positioned off Katherina's own shoulder anchor, closer
      to how a prop attaches than how a person is built? The second is
      almost certainly right for a first pass, matching the "minimum
      recognisable list" discipline the roster plan used for garments:
      small dark body, folded wings, is likely enough to read at tile
      size, and a full second skeleton is the kind of thing that eats a
      milestone budget meant for four.
- [ ] **4b.** New field(s), most likely on `CharacterParams`
      (`familiar_color` or similar), neutral-default-off.
- [ ] **4c.** Geometry: small dark-furred body, wings (folded tight by
      default, matching his most common on-page state rather than the
      alarmed flat-back one), perched at the shoulder anchor.
- [ ] **4d.** Render, iterate at tile size, both builds. Check he
      doesn't collide with the hat brim or a long hair fall at the
      shoulder, the same collision-checking discipline every accessory
      milestone above already needs.
- [ ] **4e.** Wire into `KATHERINA`, re-render the book's cover and
      style anchors.

## Open questions

- **2a/4b's exact field shape** (booleans vs. colors-as-signal) isn't
  settled here on purpose; it's a five-minute decision best made
  looking at `CharacterParams`'s current field list, not guessed at in
  a planning doc.
- **3a: does the staff become a real, reusable `Prop` concept**, or a
  one-off? Recommend deferring the generalization decision the same way
  task 28 already does, and revisiting it if and when Tenno's cane
  actually gets built.
- **4a is the one genuinely open design question in this whole plan.**
  Everything else here is "apply an existing pattern to new geometry."
  Kou is the one milestone where the pattern itself doesn't exist yet,
  and it's worth the owner's own look before code gets written, not
  just an execution check-in after.

## Tasks

Mirrors the numbering style above; kept as one combined checklist here
since, unlike the fourteen-character roster, there's no independent
ordering to argue about, milestones 1-4 in order.

- [ ] 1. Hairstyle (1a-1c)
- [ ] 2. Witch hat (2a-2e)
- [ ] 3. Staff (3a-3e)
- [ ] 4. Kou (4a-4e)
