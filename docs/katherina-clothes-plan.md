# Katherina clothes plan

An intermediate campaign between the accessories plan's milestone 3 (staff)
and milestone 4 (Kou): porting her clothes and neck off her design
reference, `../time_slider_katherina/style-anchors/katherina_grok/katherina_grok.jpg`,
by tracing, the method the hat, the staff and the `tall_chibi` body were built
with (`.claude/skills/trace-reference/SKILL.md`). Written 2026-09-17 at the
owner's request: `tall_chibi` has the reference's proportions, but the shared
garments drawn on it look mangled from the neck to the hem, so the body type is
not usable until the clothes match. Each milestone is its own
render/iterate/sign-off pass, not a batch edit.

Campaign status lives at the top of each milestone. The accessories plan
(`katherina-accessories-plan.md`) points here from its body interlude.

## What is wrong now, measured and looked at

Side by side at one head scale (`harness/body/`'s comparison, reference
first), from the neck down:

| Area | Reference | Ours on `tall_chibi` |
| --- | --- | --- |
| Neck and collar | short neck; a pointed shirt collar, two wings and a V notch, tucked under the chin, 0.99 to 1.41 head radii | a wide flat yellow trapezoid straight across under the chin |
| Shoulders | the jacket rounds over sloping shoulders straight into its sleeves | square boxy corners; a stray notch where the swung arm leaves the coat (`_arm_joint_cap`) |
| Front | jacket fronts close in to a narrow strip of dress (about ±0.15 to ±0.25); the belt is worn over the jacket | wide vertical panels; the belt shows only in the gap between them |
| Below the belt | the jacket splits into two panels flaring from ±0.29 to about ±0.87 at its 3.30 hem, dress continuous between them | boxy vertical panels, and a lighter tunic band between belt and skirt |
| Sleeves | come out of the shoulder, wide, with a turned cuff; a darker purple than the jacket's body (the jacket layer shows it) | the tunic's arm tube emerging mid-torso from the sleeve hem |
| Dress | one garment: bodice strip, then an A-line skirt from the belt to a gently curved 4.26 hem, widest ±1.13 | tunic plus skirt, two tones, pleat lines |
| Belt | brown `#31281e`, a keeper loop beside a pale square buckle | right height, but under the coat, no keeper |
| Boots | lace-up, 4.86 to the 5.94 sole, toe turned out | already close (shaft height from `tall_chibi`); not called mangled |

The reference's fill components for each (ids from
`scipy.ndimage.label(rgb.sum(2) > 60)`, see `harness/body/landmarks.py`):
collar 175/176, neck 177, jacket upper panels and sleeves 179/180, dress bodice
182, belt 192-198, jacket lower panels 202/203, dress skirt 204, the hanging
cuff and hand 208/209, legs 212/213, boots 216/218.

## The decision this campaign rests on: traced cuts, anchored to the body

The shared garments are parametric and serve the whole cast; tracing them
per character would fork the generator. The hairstyles already solved the
same problem: `long_traced` is a traced cut that sits in the same registry as
the parametric ones and is chosen by name. Clothes do the same here:

- **Named traced cuts.** A garment keeps its colour field and gains an
  optional cut name (e.g. a `coat_cut`, `collar_cut`, a dress cut), `None`
  drawing the shared parametric garment exactly as today. Katherina's cuts
  are registered under neutral names, so any character can wear them.
- **Traced in the reference's head radii, mapped onto the wearer's body.**
  A traced garment would otherwise only fit the figure it was traced off. The
  mapping is piecewise: y between the reference's landmarks (chin 0.99,
  shoulder 1.13, waist 2.384, hip 2.955, hem 4.26, ankle 5.55, sole 5.94) goes
  to the same landmarks on the target skeleton, and x at each height scales by
  the target's half-width over the reference's at that height (shoulder,
  waist, hip, hem half-widths, interpolated). On `tall_chibi`, which was
  measured off this reference, the mapping is close to the identity, which is
  the check that it is right. On the shared chibi it compresses, which is what
  keeps a cut wearable there.
- **Sleeves are traced relative to the arm, not the body**: along the line
  from the sleeve hem pivot to the wrist, so the same sleeve swings with
  `right_arm_out`/`left_arm_out` instead of being traced twice.
- **The realistic build keeps the shared garments** unless the owner decides
  otherwise (see open questions), the same scope the body type has.

## Milestones, and why this order

Top-down by what a reader's eye meets first, but groundwork before anything
visible, and the jacket's body before its sleeves because the sleeves attach
to it.

### C0. Groundwork (no visible change)

**Status: done, 2026-09-17.** `_garment_placement`, `_body_knots`,
`GarmentCut`/`_draw_cut` in character.py, identity on `tall_chibi` and
landmark-exact on the shared chibi (`test_garment_placement_is_the_identity_on_the_traced_body`);
`GarmentSlot.selects` in the catalogue and the web tool, for cut names; every
existing render byte-identical. The harness is `harness/clothes/compare.py`.
Baseline, `katherina` before any cut (iou / mean contour distance, head radii):

| region | iou | dist |
| --- | --- | --- |
| collar | 0.327 | 0.070 |
| neck | 0.000 | 0.160 |
| jacket_upper | 0.473 | 0.074 |
| dress_bodice | 0.506 | 0.286 |
| belt | 0.400 | 0.048 |
| jacket_lower | 0.598 | 0.075 |
| skirt | 0.758 | 0.142 |
| legs | 0.723 | 0.039 |
| boots | 0.307 | 0.069 |

C0d, the layer-order audit, found less to change than the table above
assumed: `_belt` is already drawn after `_coat`, so the belt is over the coat;
it only reads as sitting between the panels because the shared coat's panels
are narrower than the belt there. `_collar` comes after `_coat` and `_arms` and
before `_head`, so a collar lies over the jacket and tucks under the chin with
no change. The one relationship the order does not give: `_arms` draws after
`_coat`, so a sleeve's top lies over the jacket's shoulder, where the reference
has the jacket over the sleeve. C4 decides it (start the traced sleeve below the
jacket's shoulder seam, or draw the jacket cut's shoulder after the arms), not a
global reorder.

- [ ] **C0a.** The body-space mapping above, as one function in
      `character.py` (`_garment_placement(sk, p)`-style, like
      `_staff_placement`), with a test that it is within 0.01 head radii of
      the identity on `tall_chibi` at every reference landmark.
- [ ] **C0b.** The cut registry pattern for garments: an optional cut-name
      field per garment, `None` byte-identical to today (checked by the
      `ref-out` snapshot test for all fourteen other presets), catalogue
      slots and labels asserted in sync with the registry the way
      `HAIRSTYLE_LABELS`/`BODY_LABELS` are.
- [ ] **C0c.** A reusable comparison harness in `harness/clothes/`: renders a
      character, isolates each garment by its own fill colour, and reports
      per-region overlap and mean contour distance against the reference's
      component for that region, in head radii. This is the number each
      milestone's acceptance reads, not a glance.
- [ ] **C0d.** Layer-order audit for the new relationships the reference
      needs (belt over jacket, sleeves out from under the jacket's shoulder,
      collar over the jacket's neckline), recorded before any shape is drawn,
      since a wrong z-order looks like a wrong shape.

### C1. Neck and collar

**Status: done, signed off with the neck deferred, 2026-09-17.** `COLLAR_CUTS["pointed"]`
(back band, left and right wings: components 181, 176, 175), chosen by
`Outfit.collar_cut`, catalogued with a Cut select; colour moved to the
reference's `#c4903c`. Cuts draw only where `_wears_cuts(sk)` (chibi-range
builds); the realistic build keeps the band collar
(`test_a_traced_cut_draws_at_chibi_builds_and_not_realistic`). Harness:

| region | before | after |
| --- | --- | --- |
| collar | 0.327 / 0.070 | 0.768 / 0.018 |
| neck | 0.000 / 0.160 | 0.153 / 0.093 |

The neck is left as it is, deliberately (C1b): what hides it is not the neck.
Our chin is rounder and wider than the reference's and covers more of the
throat, which is the head's shape, outside this campaign; and the shared
coat's neckline climbs to the jaw, which is C3's.

**Deferred by the owner, 2026-09-17, to pick up later:** the visible neck (a
narrower, more pointed jaw on `tall_chibi` first, a slightly longer neck as the
fallback) and two small dark ticks where the collar wings' tops show at the
jaw's edge. The collar reads as a collar without a neck until then.

- [ ] **C1a.** Trace the collar's two wings and V notch (175/176) and the
      visible neck (177). Collar colour from the reference's median (the
      accessories plan's table has `#c48f3d` against the preset's `#c9a13b`).
- [ ] **C1b.** Neck width and length on `tall_chibi` against the reference;
      if the shared `_neck` is only wrong in its numbers, fix the numbers on
      the body type rather than tracing a neck.
- [ ] **C1c.** Accept on the C0 harness numbers plus a 4x zoom on white and
      black: no gap between collar, neck, chin and hair.

### C2. The dress

**Status: done, 2026-09-17.** A narrower cut than planned, because the dress's
visible bodice is only the strip the jacket's fronts leave, which is C3's to
shape: `SKIRT_CUTS["a_line"]` (component 204, carried under the belt and the
jacket's lower panels, `harness/clothes/trace_skirt.py`), worn over a tucked
tunic of the same colour so the lighter band below the belt is gone and the two
read as one dress. Colour: the reference's `#251d35` lifted to `#29213b` to keep
the coat-visibility guard's luminance gap (see the preset's comment). Harness,
re-scored after a harness fix (the long sleeves share the tunic's key colour and
were counted as skirt; the skirt now scores its own colour, the bodice only
within |x| <= 0.45):

| region | before | after |
| --- | --- | --- |
| dress_bodice | 0.856 / 0.019 | 0.856 / 0.019 |
| skirt | 0.770 / 0.109 | 0.894 / 0.035 |

Looked at on `tall_chibi` and on the shared chibi through the mapping
(`out/clothes/c2_bodies.png`): a short A-line there, collar intact.

- [ ] **C2a.** Trace the bodice strip (182) and the skirt (204) as one dress
      cut: A-line from the belt, curved hem. It replaces tunic-plus-skirt on
      whoever wears it, so the lighter band below the belt goes.
- [ ] **C2b.** Decide what of the dress is hidden under the jacket and trace
      only a plausible continuation there (the dress layer export shows it;
      use it as a guide to shape, coordinates from the composite where the
      dress is visible).
- [ ] **C2c.** Accept on the harness plus looks, both on `tall_chibi` and on
      the shared chibi through the mapping.

### C3. Jacket body

**Status: done, 2026-09-17.** `COAT_CUTS["open_jacket"]` (`harness/clothes/trace_jacket.py`):
each side one piece, the navy upper panel split by hue from the purple sleeve it
shares a fill component with, carried across the hair as the convex hull of its
visible navy and under the belt edge to edge into its flaring lower panel; plus
the two vertical seams where the sleeve's back meets the body. `coat_length`
does not apply to a traced cut (C3c); Katherina's fitted 0.49 is gone with it.
The jacket keeps the preset's `#12152a` rather than the reference's `#191d30`:
the sampled navy against the dress would fail the coat-visibility guard (a gap of
7 against its 12), and the preset's is the same hue, darker. Harness:

| region | before C3 | after |
| --- | --- | --- |
| jacket_upper | 0.489 / 0.067 | 0.555 / 0.057 |
| dress_bodice | 0.856 / 0.019 | 0.871 / 0.016 |
| jacket_lower | 0.598 / 0.075 | 0.800 / 0.028 |
| skirt | 0.894 / 0.035 | 0.949 / 0.016 |

`jacket_upper` still counts the sleeves (they share its components), so it moves
with C4. Seen at 4x on white (`out/clothes/c3_shoulders.png`): the tunic's own
sleeve caps and the swung arm's joint cap show beside the jacket's shoulders where
our hair is narrower than the reference's; both are C4's.

- [ ] **C3a.** Trace the upper panels (179/180 minus the sleeves), the
      sloping shoulders and the front edges down to the belt. The hair hides
      the shoulders' outer line; the jacket layer export shows its shape, and
      anything taken from it is flagged as inferred in the cut's comment.
- [ ] **C3b.** Trace the lower panels (202/203) flaring from the belt to the
      3.30 hem, with the dress showing between them.
- [ ] **C3c.** Coat length on this cut is the traced hem; decide whether
      `coat_length` still applies to a traced coat (probably not; record it).
- [ ] **C3d.** Accept on the harness plus looks, with the staff and the hair
      in place, since both cross the jacket.

### C4. Sleeves and cuffs

**Status: not started.**

- [ ] **C4a.** Trace the hanging sleeve (the viewer's right, part of 179) and
      its cuff (208) along the arm line, sleeve colour from the reference
      (darker purple than the jacket's body).
- [ ] **C4b.** Apply the same traced sleeve to the swung arm, attached under
      the jacket's shoulder, and retire or rework `_arm_joint_cap` where the
      traced shoulder makes it unnecessary.
- [ ] **C4c.** Refit `right_arm_out` if the sleeve's pivot moves, and check
      the staff's grip again.

### C5. Belt

**Status: not started.**

- [ ] **C5a.** Draw the belt over the jacket (the C0d order), trace its
      band, the keeper loop and the buckle (192-198); colour `#31281e`.

### C6. Boots (deferred)

**Status: deferred by the owner, 2026-09-17.** The boots were not called mangled and
the body type already puts their shaft at the reference's height. Listed so
the campaign's scope is explicit, not so it grows.

### C7. Integration

**Status: not started.**

- [ ] **C7a.** Both builds rendered and looked at; realistic falls back to the
      shared garments per the decision above.
- [ ] **C7b.** One other preset wearing the cuts on `tall_chibi` and on the
      shared chibi, to prove they are cuts and not a costume that only fits
      Katherina.
- [ ] **C7c.** Web tool and catalogue exposure of the cut names.
- [ ] **C7d.** The book's cover and style anchors, then its reader artifact,
      only on the owner's go-ahead (held since the body type landed).

## Acceptance, every milestone

- The C0 harness: per-region overlap and mean contour distance against the
  reference, recorded in the milestone's status with the commit it was taken
  at. Predict the number before rendering.
- Looked at: side by side at one head scale on black, on white, and at 4x zoom
  on every junction the milestone touches.
- `ruff check`, `ruff format --check`, `pytest` green; `refresh-ref-out.sh`
  reports only the wearer's renders changed (plus `catalogue.json` when a cut
  is exposed).
- The owner's sign-off before the next milestone starts.

## Risks

- **The hair hides the shoulders and upper sleeves.** Shape there comes from
  the layer exports, which are regenerated variants, not crops: guide only,
  flagged as inferred.
- **The reference's held arm bends at the elbow; ours is straight.** A traced
  sleeve on a straight swung arm may read stiff. If it does, an elbow bend is
  pose machinery and a separate question, not something to fake in a sleeve.
- **Draw order is shared.** Moving the belt over the coat is correct for this
  cut and wrong for other characters' belted tunics under open coats; the
  order has to depend on the cut, not change globally.
- **Scope creep into a garment rewrite.** Parametric garments stay the
  default for the cast; this campaign adds cuts beside them.

## Owner's decisions (2026-09-17)

1. **Reusable named cuts**, not Katherina-only garments.
2. **Realistic build keeps the shared garments** for now.
3. **Boots (C6) deferred**, out of this campaign's scope.
4. **Colours move to the reference's samples**, one milestone at a time.

The questions as asked, kept for the record:

1. **Reusable named cuts or Katherina-only garments?** Recommended: named cuts
   (the hairstyle pattern), so `tall_chibi` becomes usable for anyone.
2. **Realistic build:** keep the shared garments there? Recommended: yes, for
   now, matching the body type's scope.
3. **Boots (C6):** in or out? Recommended: out unless they start to look wrong
   once the clothes above them change.
4. **Colours:** move the preset to the reference's sampled garment colours as
   each milestone lands (collar `#c48f3d`, belt `#31281e`, jacket `#171c2f`,
   skirt `#261e36`), or keep today's? Recommended: sampled, one milestone at a
   time.
