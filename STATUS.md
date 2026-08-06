# Status

Snapshot of where the generator is and what comes next. Working notes,
not user documentation: see `README.md` for how to run it and
`CLAUDE.md` for the rules that govern changes.

Last updated: 2026-08-06, at `21850a5` "add new references", plus the
uncommitted canon pass (stroke scaling, canon eyes, long-cut locks,
pouches and buckle, boot toes and laces, mitten hands, realistic
polish, off-centre parting). Per-task snapshots of that pass are in
`out/35` through `out/43`.

## Where it stands

All four PoC targets render: Satoko and Satoshi, each at `chibi` and
`realistic`. Every shape is computed from the `Skeleton`, nothing is
composited from pre-made art, and no AI image generation is involved.

`ref-out/` holds those four as checked-in `.png` and `.svg`, and the
README displays them. It is the only generated output in version control,
and it is the current state of the named characters rather than a
snapshot of some past one, so **refresh it in the same change that alters
a shape.** Miss it and the README shows art the code no longer produces:

```bash
./refresh-ref-out.sh          # re-render, report which characters moved
./refresh-ref-out.sh --check  # compare only, write nothing, exit 1 if stale
```

Anything else goes to `out/`, which is ignored.

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
  undersleeve, belt, apron, skirt, underskirt, trousers, pouches,
  boots, plus a `skirt_length`. A garment is worn when its color is
  set, so a character states only the layers it has. Satoko wears all
  but the trousers, Satoshi swaps skirt, apron and pouches for
  trousers. A belt without an apron over it shows a buckle; pouches
  hang from the belt band, tucked inboard at chibi where the arms
  would otherwise hide them.
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

## Style canon

`ref/satoko-chibi.jpg` and `ref/satoko-real.jpg` are the style canon:
the target drawing language at each end of the build range, chosen
2026-08-06. They were made by feeding the original references and our
renders to an image model and tuning toward the owner's vision, so they
are guides in spirit as much as letter; visual appeal still beats exact
match.

The satoshi pair (`ref/satoshi-chibi.jpg`, `ref/satoshi-real.jpg`) is
identity-only. It fixes his haircut, trousers and the lower-body garment
detail the satoko refs barely show (belt buckle, simple trouser lines),
but its drawing style is explicitly not the target: the per-lock
highlight sweeps, ears, articulated fingers and skin shading there do
not carry over. Render his features in the satoko language. The older
`ref/satoko.png` and `ref/satoshi.png` stay identity sources, and the
`ref/girl-chibi.png` that used to set the chibi detail bar is gone from
`ref/`; the canon supersedes it and sets a higher bar.

What the canon language is, concretely:

- Bold uniform outline that scales with the figure: measured about
  0.017 of head width at chibi and 0.023 at real. Thick silhouette over
  thinner interior lines.
- Big open rounded eyes at chibi: heavy top lash line, iris rim tone,
  pupil, two highlights. Expression lives in brows and mouth, not in
  lowered lids. Smaller and slightly lidded at real.
- Hair as wedge locks with pointed tips and interior strands, falls
  sitting in front of the shoulders, the tip fade following the locks
  rather than waving smoothly across them.
- Flat fills, hard shadow edges, no interior shading beyond the one
  shadow tone. Ears hidden under hair. Mitten-grade hands with a thumb
  notch at chibi.
- Garment accents survive chibification: pouches with flap and button,
  a buckled belt band, boot cross-laces. (Rolled sleeve cuffs appear only
  in the satoshi pair, whose style is not the target, so they are out.)

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
  between them is narrower than in the refs. `ref/satoko-chibi.jpg`
  keeps the same tan sleeves but hangs the arms clear of the tunic's
  sides, so its green stays wide.
- **The waist is wider than the reference's, relative to the shoulder.**
  *Measurement gap only, does not read as wrong.* The forearm-to-waist gap
  is about 4px where `ref/satoshi.png` has 21px, but the arms hanging close
  to the body looks fine, and narrowing `waist_half_w` is a skeleton change
  touching both characters and both builds. Not worth doing on the
  measurement alone.
- **Hair silhouettes are still mirrored point data.** Both cuts now
  part off-centre in the fringe, divide into locks through strands and
  end in points, which carries the asymmetry the canon shows; by eye
  that is enough, so silhouette-level asymmetry stays deliberately
  unattempted. Worth revisiting only if a future cut needs it.
- **The realistic leg length is settled: it matches the canon.** The old
  short-legged judgment was made against `ref/satoshi.png` and does not
  survive the canon: measured, the canon's leg split sits at 0.565 of
  figure height against our 0.528, so ours are if anything the longer,
  and side by side at equal height the two figures agree. `hip_y` and
  `knee_y` stay where they are.
- **No pose variety, one outfit family.** Deliberately deferred.
- **Satoshi at chibi reads as a boy only through hair and trousers.**
  That is by design, since a shoulder-to-hip ratio is invisible at 2.4
  heads, but it does mean the two chibis are closer to each other than
  the two realistic builds are.

## Acceptance criteria

Four targets: Satoko and Satoshi, each at `chibi` and `realistic`. The
tables below are the definition of done. Style comes from the canon
(`ref/satoko-chibi.jpg`, `ref/satoko-real.jpg`); identity comes from
`ref/satoko.png` and `ref/satoshi.png`, plus the satoshi pair for his
haircut and lower body.

### How much detail each build carries

The canon sets the chibi bar, and it is higher than the old
`ref/girl-chibi.png` one: pouches with a flap and button, a buckled
belt band and boot cross-laces all survive chibification there, each
drawn as a few flat shapes. A chibi still reads through silhouette and
color banding first; these are accents on top of that, not texture.

Still out of scope at chibi: articulated fingers (a mitten with a thumb
notch is the bar), ears, skirt pleats, sleeve wrinkles, the apron's
hanging strap. At realistic the canon adds pleats on the underskirt, a
nose line, a visible neck and collar, and hinted fingers; the fingers
are optional, hand detail is explicitly deprioritized.

### Satoko

Ranked by identity carried per pixel.

| Feature | State |
| --- | --- |
| Blonde fading to white ends | done |
| Shoulder-length blunt hair | done |
| Guarded expression: level brows, no smile (carried by brows and mouth) | done |
| Canon eye: open rounded aperture, heavy top lash, iris rim and pupil | done |
| Cheek scar | done |
| Muted green / leather palette | done |
| Outfit color banding: green tunic, brown belt and apron, green skirt, dark underskirt | done |
| Tan long undersleeves under short green sleeves | done |
| Waist that reads: belt at the waist anchor, tunic taking in above it | done |
| Hair that reads as locks: pointed tips, strands, per-lock fade | done |
| Pouches with flap and button on the belt band | done |
| Ankle boots with a shaft rather than a brown block | done |
| Boot toe and cross-laces | done |
| Side-swept parting | done, fringe and crown strands part right of centre |

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
| Canon eye construction (same geometry as Satoko's, his own knobs) | done |
| Belt buckle | done |
| Boot toe and cross-laces | done |
| Slimmer frame: broader shoulder over narrower hip | done, realistic only |
| Faint cheek mark | not started, and the canon satoshi pair shows none, so decide first whether it survives |
| Off-centre parting in the silhouette, not only in the fringe | settled: fringe and strands carry it, silhouette stays mirrored |

The frame row is realistic-only on purpose. At 2.4 heads a shoulder to
hip ratio is invisible, so a chibi Satoshi has to read as a boy on hair
and trousers alone. If that turns out not to be enough, the answer is
more contrast in those two, not skeleton work.

## Next steps

The canon pass of 2026-08-06 cleared the previous list: stroke scaling,
canon eyes, long-cut locks, pouches and buckle, boot toes and laces,
mitten hands, nose and collar and elbow bend, off-centre parting. Leg
length closed as already matching the canon. What remains, ranked:

1. **Chibi arms hanging clear of the tunic.** The one canon gap left on
   the weak list: the tan arms cover about a third of the green where
   `ref/satoko-chibi.jpg` hangs them clear of the tunic's sides. That is
   `arm_x` and sleeve width at the chibi end only, so it wants the
   side-by-side lab treatment before anything ships.
2. **Satoshi's faint cheek mark, or its removal.** The old identity refs
   suggest one; the canon satoshi pair shows none. Decide first, then it
   is one `FaceStyle` value either way.
3. **Then variety.** More hairstyles and a second outfit family. The
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
- Re-render `ref-out/` in the same change as any shape edit. It is
  committed and the README shows it, so it is the one piece of output that
  goes stale visibly and silently. `./refresh-ref-out.sh` does it, and
  `--check` detects a stale state without writing anything.
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
