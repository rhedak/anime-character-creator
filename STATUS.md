# Status

Snapshot of where the generator is and what comes next. Working notes,
not user documentation: see `README.md` for how to run it and
`CLAUDE.md` for the rules that govern changes.

Last updated: 2026-08-05, uncommitted, on top of `b7ec2b5` "satoko and
satoshi ref".

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
- **Garments.** `Outfit` carries one field per piece: tunic,
  undersleeve, belt, apron, skirt, underskirt, trousers, boots, plus a
  `skirt_length`. A garment is worn when its color is set, so a
  character states only the layers it has. Satoko wears all but the
  trousers, Satoshi swaps skirt and apron for trousers.
- **Hair.** `HAIRSTYLES` names `long_blunt` and `short_layered`, each a
  set of four outlines that agree with each other. Two-tone with a waved
  fade boundary. `hair_length` spans whatever range the cut defines: the
  long one measures the body, chin to hip, so it survives a change of
  build; the short one measures the head, ear to chin, because the
  body-relative range cannot express hair ending above the chin at all.
- **Head.** Eight quadratics tracing a circle at the chibi end and
  narrowing to a jaw and chin as the build gets taller.
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

- **Arms are capsules with circles for hands.** Now the most crude thing
  left. Acceptable at chibi, and at `realistic` the straight tube and
  ball hand are what stop the figure reading as a body. The tunic's
  short sleeve is drawn in `_arms` rather than `_tunic`, so a rework has
  to keep the sleeve lapping over the arm and the hands over every
  garment.
- **The chibi face has not been calibrated against `ref/girl-chibi.png`.**
  The forehead is taller than the reference's and the hair mass flares
  wider, so the head reads wider than tall. The width profile matches
  from the chest down; it is the head that has not been checked.
- **Hair is symmetric except for the short cut's fringe.** No
  side-swept part on the long style, so the mirrored point data is
  doing all the work there.
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
| Dark trousers instead of skirt and apron | done |
| Green tunic, tan undersleeves, brown belt, brown boots (shared with Satoko) | done |
| Level brows, no smile | done |
| Slimmer frame: broader shoulder over narrower hip | done, realistic only |
| Faint cheek mark | not started |

The frame row is realistic-only on purpose. At 2.4 heads a shoulder to
hip ratio is invisible, so a chibi Satoshi has to read as a boy on hair
and trousers alone. If that turns out not to be enough, the answer is
more contrast in those two, not skeleton work.

## Next steps

1. **Arms.** The last crude shape. Taper them from shoulder to wrist and
   give the hand a shape instead of a circle, the way
   `_legs_and_boots` already tapers off `sk.build`. Two constraints the
   current layering imposes: the short sleeve is drawn in `_arms` so it
   laps over the top of the arm, and `_arms` is drawn last below the neck
   so nothing clips the hands. The apron's edge sits about 3px inside the
   hand at chibi, which is why that ordering exists.
2. **Chibi face pass.** Calibrate the head against `ref/girl-chibi.png`:
   the fringe peak sits higher than the reference's so the forehead is
   too tall, and the hair mass flares wider so the head reads wide.
   Satoko's expression itself is right and should not move.
3. **Asymmetry.** Side-swept parting on the long style. Lowest value,
   highest fiddliness, since it breaks the mirrored point data that
   `_mirror` / `_reverse` rely on. The short cut's fringe is already
   asymmetric without touching the silhouette, which is the cheaper trick
   and may be enough.
4. **Then variety.** More hairstyles and a second outfit family. The
   hairstyle registry and `Outfit` are both built to take them now.

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
