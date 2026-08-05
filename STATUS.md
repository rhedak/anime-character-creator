# Status

Snapshot of where the generator is and what comes next. Working notes,
not user documentation: see `README.md` for how to run it and
`CLAUDE.md` for the rules that govern changes.

Last updated: 2026-08-06, at `159fc01` "iterate satoshi".

## Where it stands

All four PoC targets render: Satoko and Satoshi, each at `chibi` and
`realistic`. Every shape is computed from the `Skeleton`, nothing is
composited from pre-made art, and no AI image generation is involved.

```bash
./render.sh --out out/satoko  --preset satoko
./render.sh --out out/satoko_real  --preset satoko  --build realistic
./render.sh --out out/satoshi --preset satoshi
./render.sh --out out/satoshi_real --preset satoshi --build realistic
```

What is parametrized:

- **Build.** `BUILDS` names `chibi` (2.4 head-heights, the default) and
  `realistic` (6.0). `--heads N` reaches anything in between. Both
  widths and where the landmarks sit along the body interpolate, so a
  chibi comes out nearly neckless with high hips and an adult does not.
  `Skeleton.build` exposes where along that range a figure sits, so
  parts that deform with the build read it instead of recomputing it.
- **Frame.** `frame` scales shoulder against hip, -1 narrow-shouldered
  and wide-hipped through +1 the other way. It rides on the build, so it
  bites at `realistic` and all but vanishes at `chibi`, where the head
  swamps the torso anyway.
- **Where the legs hang.** At the taller builds the outer edge of the
  thigh lands on `hip_half_w`, which is what the tunic's hem is drawn to,
  so the body's side carries straight on down into the leg rather than the
  trousers overhanging it. That falls out of the frame for free: a
  narrow-hipped figure's legs come in, a wider-hipped one's go out. It
  also happens to land the crotch gap where `ref/satoshi.png` has it, each
  inner edge about 0.09 head radii off centre. A chibi keeps its legs
  tucked in close instead, since its hips are nearly as wide as an adult's
  in head radii while its legs are less than half as thick.
- **Garments.** `Outfit` carries one field per piece: tunic,
  undersleeve, belt, apron, skirt, underskirt, trousers, boots, plus a
  `skirt_length`. A garment is worn when its color is set, so a
  character states only the layers it has. Satoko wears all but the
  trousers, Satoshi swaps skirt and apron for trousers.
- **Hair.** `HAIRSTYLES` names `long_blunt` and `short_layered`, each a
  set of four outlines that agree with each other, plus an optional fifth
  giving the strands that divide the mass into locks. Two-tone with a
  waved fade boundary. `hair_length` spans whatever range the cut
  defines: the long one measures the body, chin to hip, so it survives a
  change of build; the short one measures the head, ear to chin, because
  the body-relative range cannot express hair ending above the chin at
  all.
- **Headroom.** `hair_margin` is the space above the skull, measured in
  head radii rather than as a fraction of the canvas, because that is
  what it measures. As a canvas fraction it was generous at a tall build
  and too small at a chibi, where the head is a third of the figure, so
  both chibis used to come out with the top of their hair sliced flat
  against the canvas edge.
- **Head.** Eight quadratics tracing a circle at the chibi end and
  narrowing to a jaw and chin as the build gets taller. The short cut's
  crown is a circular arc off the same construction, a shell 0.28 head radii
  thick over it.
- **Colors.** Skin, hair, hair tips, eyes, and every garment above.
- **Face.** `FaceStyle` carries the eye aperture (size, width,
  openness, lower lid, tilt, corner sharpness, iris size), brow tilt
  and weight, mouth curve and width, blush, and a cheek scar. Every
  default is neutral, so a character states only what it differs on.
- **Characters.** `presets.py` holds `SATOKO` and `SATOSHI`, sharing a
  palette through module constants because the two are meant to read as
  related.

Every knob above has a CLI flag, and flags override a preset one value
at a time.

## What is weak right now

The bar is how it looks, not how closely it matches `ref/`. Those images are
guides: they are drawn on a different figure, in `ref/satoshi.png`'s case on a
wider hip and in a slightly turned pose, so numbers lifted off them come out
heavy or splayed even when the arithmetic is right. Measure to find *what* is
wrong, then choose by eye, and note in a comment where a shipped number departs
from a measured one. A difference from a reference is not a defect on its own,
so each entry below says whether it actually looks wrong or is only a
measurement gap.

- **The chibi's tan arms cover about a third of the tunic.** They are
  thick at that build and sit where they sit, so the visible green
  between them is narrower than in `ref/satoko.png`.
  `ref/girl-chibi.png` hides the same overlap by making the arms the
  dress colour, which Satoko's tan undersleeves cannot do.
- **The waist is wider than the reference's, relative to the shoulder.**
  *Measurement gap only, does not read as wrong.* The forearm-to-waist gap
  is about 4px where `ref/satoshi.png` has 21px, but the arms hanging close
  to the body looks fine, and narrowing `waist_half_w` is a skeleton change
  touching both characters and both builds. Not worth doing on the
  measurement alone.
- **Eye placement has not been calibrated against `ref/girl-chibi.png`.**
  *Unjudged, needs a look before anything is moved.* They sit lower and
  closer together than the reference's and smaller relative to the head,
  but that is a measurement, and whether it reads wrong has not been
  decided. The forehead half is fixed on both cuts: the fringe now stops
  just above the brows rather than on top of the skull.
- **Hair is symmetric except for the short cut's fringe.** No
  side-swept part on the long style, so the mirrored point data is
  doing all the work there. The long cut has no strands either, so it is
  still one flat field of colour with a single hairline across it, which
  is what the short cut looked like before this round.
- **The boot still reads as a block at the taller builds.** The shaft and
  the flare to the sole are both there and the foot is now wider than the
  ankle it hangs off, which it briefly was not, but there is no toe: the
  reference's boot projects forward and this one is a rounded rectangle.
  It survives chibification precisely because it is that simple, so any
  fix has to ride on the build.
- **The realistic figure is shorter-legged than the reference.** *Reads as
  wrong, worth doing.* At 6 heads the trousers are right in width but the
  figure comes out stubby: the leg is a smaller fraction of the body than
  `ref/satoshi.png`, where the inseam runs to about half the total height.
  That is `hip_y` and `knee_y`, so it moves both characters, and the skirt
  hem and boot shaft ride on it.
- **No pose variety, one outfit family.** Deliberately deferred.
- **Satoshi at chibi reads as a boy only through hair and trousers.**
  That is by design, since a shoulder-to-hip ratio is invisible at 2.4
  heads, but it does mean the two chibis are closer to each other than
  the two realistic builds are.

## Acceptance criteria

Four targets: Satoko and Satoshi, each at `chibi` and `realistic`. The
tables below are the definition of done. References are `ref/satoko.png`
and `ref/satoshi.png` for identity, `ref/girl-chibi.png` for how much
detail a chibi carries.

### How much detail each build carries

`ref/girl-chibi.png` sets the chibi bar, and it is much lower than the
two character refs. It has no belt, no apron, no visible undersleeve and
no underskirt: arms are plain tubes ending in circle hands, and the only
hint of a second garment is a sliver of tan collar inside the green V
neck. So a chibi reads through silhouette and color banding, nothing
finer.

Out of scope at chibi, in rough order of how tempting they are: belt
buckle, pouch flaps, boot laces, the keyhole neckline's split, sleeve
wrinkles, the apron's hanging strap. They do not survive chibification
and attempting them adds noise. At realistic they become optional rather
than wanted; the garment layering matters far more than any of them.

### Satoko

Ranked by identity carried per pixel.

| Feature | State |
| --- | --- |
| Blonde fading to white ends | done |
| Shoulder-length blunt hair | done |
| Guarded expression: narrow lidded eyes, level brows, no smile | done |
| Cheek scar | done |
| Muted green / leather palette | done |
| Outfit color banding: green tunic, brown belt and apron, green skirt, dark underskirt | done |
| Tan long undersleeves under short green sleeves | done |
| Waist that reads: belt at the waist anchor, tunic taking in above it | done |
| Ankle boots with a shaft rather than a brown block | done |
| Side-swept parting | not started |

### Satoshi

Same palette and same tunic as Satoko, by design: they are meant to read
as related, so what carries his identity is hair and lower body.

| Feature | State |
| --- | --- |
| Short layered cut, same blonde fading to white | done |
| Hair that reads as locks rather than as one mass | done |
| Dark trousers instead of skirt and apron | done |
| Trouser leg that fills out at the thigh then runs near straight | done |
| Legs hanging under the hip, not overhanging the body's side | done |
| Green tunic, tan undersleeves, brown belt, brown boots (shared with Satoko) | done |
| Level brows, no smile | done |
| Slimmer frame: broader shoulder over narrower hip | done, realistic only |
| Faint cheek mark | not started |
| Off-centre parting in the silhouette, not only in the fringe | not started |

The frame row is realistic-only on purpose. At 2.4 heads a shoulder to
hip ratio is invisible, so a chibi Satoshi has to read as a boy on hair
and trousers alone. If that turns out not to be enough, the answer is
more contrast in those two, not skeleton work.

## Next steps

1. **Eye placement.** Against `ref/girl-chibi.png` the eyes sit lower and
   closer together than the reference's, and smaller relative to the
   head. Only the geometry the two share should move: Satoko's aperture
   shape carries her expression and is right.
2. **Strands on the long cut.** The short cut's are what took it from a
   pot to a haircut, and the long one is now the undivided-mass style. It
   wants a different set: falling with the hair rather than radiating from
   a crown whorl.
3. **Leg length at the taller builds.** The trousers are the right width
   now but the leg is short against `ref/satoshi.png`. This is `hip_y` and
   `knee_y` in the skeleton, so it moves both characters, and the skirt
   hem and boot shaft ride on it.
4. **Asymmetry.** Side-swept parting on the long style. Lowest value,
   highest fiddliness, since it breaks the mirrored point data that
   `_mirror` / `_reverse` rely on. The short cut's fringe is already
   asymmetric without touching the silhouette, which is the cheaper trick
   and may be enough.
5. **Then variety.** More hairstyles and a second outfit family. The
   hairstyle registry and `Outfit` are both built to take them now.

## Conventions worth remembering

- Render and *look* at the PNG before calling a shape change done.
  Coordinates that are right in the math are routinely wrong visually;
  most of the fixes so far came from looking, not from reasoning.
- Render candidates side by side rather than one at a time. Monkeypatch
  the shape functions from a throwaway script so several profiles can be
  compared in one image without editing the source per guess, then write
  the winner in. Suppressing a feature entirely is part of the set: a
  render with the hair strands turned off is what proved they were
  carrying the difference, and the untapered leg is what proved the old
  taper was worse than no taper at all.
- When a comparison shows no difference, check that the variant was
  actually applied before concluding the knob does not matter. One
  strand-weight comparison here was five copies of the same image,
  because the substitution it relied on never matched.
- Anything meant to read as a smooth curve should be generated, not
  hand-placed. `_arc` traces a circle about the head centre by putting each
  control point on the bisector at `r / cos(half the segment angle)`, the
  same construction `_head_shape` uses. Hand-placed anchors and controls
  scallop instead: the crown peaked between its anchors and dipped at them,
  and that wobble reads as a defect rather than as texture. The hair reads
  as locks through the strands and the fringe, which is where the
  irregularity belongs.
- Check both builds after touching anything below the neck. Several
  rules that were correct at 4 heads broke the chibi (arm placement in
  particular), which is why `arm_x` is a skeleton anchor and not a
  formula in `character.py`.
- Check a palette far from the defaults after touching `shade()`
  derivations.
