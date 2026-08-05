# Status

Snapshot of where the generator is and what comes next. Working notes,
not user documentation: see `README.md` for how to run it and
`CLAUDE.md` for the rules that govern changes.

Last updated: 2026-08-05, at commit `86c4e0e` "chibi / realistic mode".

## Where it stands

A front-facing character renders end-to-end as programmatic SVG. Every
shape is computed from the `Skeleton`, nothing is composited from
pre-made art, and no AI image generation is involved.

What is parametrized:

- **Build.** `BUILDS` names `chibi` (2.4 head-heights, the default) and
  `realistic` (7.0). `--heads N` reaches anything in between. Both
  widths and where the landmarks sit along the body interpolate, so a
  chibi comes out nearly neckless with high hips and an adult does not.
- **Colors.** Skin, hair, hair tips, eyes, outfit, boots.
- **Hair.** Two-tone with a waved fade boundary, and a body-relative
  `hair_length` (chin 0 to hip 1) so one haircut survives a change of
  build.
- **Face.** `FaceStyle` carries the eye aperture (size, width,
  openness, lower lid, tilt, corner sharpness, iris size), brow tilt
  and weight, mouth curve and width, blush, and a cheek scar. Every
  default is neutral, so a character states only what it differs on.
- **Characters.** `presets.py` holds named `CharacterParams`. `SATOKO`
  is the only one so far.

Every knob above has a CLI flag, and flags override a preset one value
at a time.

## What is weak right now

- **The outfit is one dress shape.** This is the single biggest
  problem. It runs shoulder to hem with no waist, which is tolerable on
  a chibi and dominates the frame on a realistic build (`out/satoko_real.png`).
  Everything else about the realistic mode is in reasonable shape; the
  garment is what makes it look wrong.
- **The head is a plain circle.** Fine at chibi scale, reads as a ball
  on a stick at 7 heads. Needs a jaw before the realistic build is
  presentable.
- **Arms are capsules with circles for hands.** Acceptable at chibi,
  crude at realistic.
- **Hair is symmetric.** No side-swept part, so the mirrored point data
  is doing all the work.
- **Only one hairstyle, one outfit, one pose.** Variety has been
  deliberately deferred until the base shapes are right; a template
  with wrong proportions is wrong for every character built from it.

## Satoko recognizability

The working goal is a simplified chibi that reads as Satoko
(`ref-local/satoko.png`, gitignored). Ranked by identity carried per
pixel:

| Feature | State |
| --- | --- |
| Blonde fading to white ends | done |
| Shoulder-length blunt hair | done |
| Guarded expression: narrow lidded eyes, level brows, no smile | done |
| Cheek scar | done |
| Muted green / leather palette | done |
| Outfit color banding: green tunic, brown belt and apron, green skirt, dark underskirt | **not started** |
| Tan long undersleeves under short green sleeves | **not started** |
| Side-swept parting | not started |

Deliberately out of scope at this size: belt buckle, pouch flaps, boot
laces, the keyhole neckline, sleeve wrinkles. They will not survive
chibification and attempting them adds noise.

## Next steps

1. **Layered outfit.** The next thing to build, and the one that
   unblocks the realistic mode. New parts in z-order: undersleeves,
   tunic, skirt, underskirt hem band, apron, belt. Needs
   `CharacterParams` to stop being colors-plus-face and gain garment
   selection, otherwise every new piece gets hardcoded into
   `render_character`. Use the existing `waist_y` / `hip_y` /
   `hip_half_w` anchors; they were added for this and are currently
   unused by any part.
2. **Head shape.** Replace the circle with a path that has a jaw,
   tapering more as the build gets taller. The hair's crown points are
   pinned to the head, so this touches `_hairline_shape` too.
3. **Asymmetry.** Side-swept parting. Lowest value, highest
   fiddliness, since it breaks the mirrored point data that
   `_mirror` / `_reverse` currently rely on.
4. **Then variety.** Alternate hairstyles and outfits, once the base
   shapes hold up at both builds.

## Conventions worth remembering

- Render and *look* at the PNG before calling a shape change done.
  Coordinates that are right in the math are routinely wrong visually;
  most of the fixes so far came from looking, not from reasoning.
- Check both builds after touching anything below the neck. Several
  rules that were correct at 4 heads broke the chibi (arm placement in
  particular), which is why `arm_x` is a skeleton anchor and not a
  formula in `character.py`.
- Check a palette far from the defaults after touching `shade()`
  derivations.
