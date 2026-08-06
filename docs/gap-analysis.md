# Gap analysis: current renders against the canon

A snapshot comparison of the four checked-in renders against the four
reference drawings, taken 2026-08-06 at `c4dc619`. The target style is
`ref/satoko-chibi.jpg` and `ref/satoko-real.jpg`, applied to both
characters, so where the two references disagree Satoko's win (see
"Where the references disagree" below).

The references are guides, not targets. What follows is measurement used
to find what is wrong, not a list of numbers to converge on; the final
call on any of it is by eye.

## Method and units

Each reference was paired with its render, both cropped to the painted
figure and scaled to the same height, then measured and looked at. The
`gap-analysis` skill in `.claude/skills/gap-analysis/` carries the
procedure and the tooling, so a re-run after a shape pass reproduces
these numbers the same way rather than measuring afresh. Strips
regenerate into `out/56/`:

| File | What it shows |
| --- | --- |
| `cmp_all.png`, `cmp_satoko.png`, `cmp_satoshi.png` | full figures, ref beside ours, with guide lines every 0.1 H |
| `heads_satoko.png`, `heads_satoshi.png` | the top 42% at 2x |
| `torso_chibi.png`, `torso_real.png` | the garment construction |
| `legs.png` | hem, legs and boots |

**H** is the figure height, ink top to sole. Every position and width
below is a fraction of it, because that is the one normaliser that
measures reliably on a JPEG reference and on our PNG alike. Our own
figures are computed from `build_skeleton` and the hair point data rather
than measured, so those numbers carry no measurement error. Reference
numbers are only quoted where they reproduced independently (identical on
the left and right of a symmetric figure, and physically sensible);
everything else is stated as what the strips show.

## What already matches, and should not be disturbed

- **The vertical landmark stack.** Chin, shoulder, garment hems and ankle
  all land within a few percent at both builds. Satoko's chin sits at
  about 0.46 H in the canon chibi against our 0.445, and at about 0.18 in
  the canon adult against our 0.184. The chibi figure was read off
  `out/56/chin_probe.png` rather than inferred from a colour scan, which
  is worth doing for any landmark in this zone: the mouth line at 0.38 H
  and the jaw stroke spanning 0.45 to 0.47 are easy to mistake for each
  other in a column of colour runs. The tunic's lower edge is at 0.99 H
  in both. Nothing about the skeleton's proportions along the body needs
  moving.
- **Hair length.** Satoko's chibi hair ends at about 0.58 H in the canon
  and 0.571 in ours. The long cut is the right length; what is wrong with
  it is its width and its edge (gap 2).
- **The fade height**, from task 55. The gold-to-pale boundary sits at
  0.176 H in the canon adult and 0.171 in ours.
- **The palette.** Sampled as the modal exact colour inside a flat patch
  of each surface, not from a quantised histogram, since a bucket centre
  is only good to eight points a channel and that is the size of the
  whole question here:

  | Surface | Canon | Ours | Delta per channel |
  | --- | --- | --- | --- |
  | tunic, chibi | `#4c6547` | `#4a6845` | +2, -3, +2 |
  | tunic, adult | `#4d6649` | `#4a6845` | +3, -2, +4 |
  | skin, chibi | `#f3d9c2` | `#f6dbc2` | -3, -2, 0 |
  | apron leather | `#6c594b` | `#6f5c4e` | -3, -3, -3 |
  | hair gold | `#e3b448` | `#e6b53c` | -3, -1, +12 |

  Every surface but one is inside four points a channel, which is not
  visible. The exception is the gold: the canon's is a touch less
  saturated, and ours reads marginally more orange. That is the only
  part of a palette resample with anything in it, and it is a one-line
  change to `HAIR` in `presets.py` if wanted.
- **The garment inventory.** Every layer the canon wears exists as a
  part. What is missing is construction detail inside those layers
  (gap 8), not garments.
- **Total line quantity.** Outline covers 20.5% of the canon chibi figure
  and 22.4% of ours. The amount of line is right; its colour and its
  hierarchy are not (gap 5).

## Where the references disagree

The two chibi references are not the same chibi. Measured at hip level
(0.50 H), the canon Satoko chibi's silhouette is 0.560 H across and the
canon Satoshi chibi's is 0.252 H: his reference is drawn with a
distinctly smaller body under a similar head. Our two chibis are much
closer to each other, which is what a shared skeleton produces and what
the Satoko-anchored style asks for. **So the large width deltas against
the Satoshi chibi reference, up to +70% through his torso, are not gaps.**
Reading them as gaps would mean giving him a separate set of proportions,
which is exactly the thing `CLAUDE.md` forbids.

The same holds for colour: the Satoshi references use tanner skin
(`#d8b8a8`) and a browner gold (`#c8a858`) than the Satoko ones.
`presets.py` deliberately unifies the palette so the two read as related.
That decision stands; the Satoshi references are still the only source
for his hair shape and his trousers, and should be used there only.

## The gaps, in priority order

Priority is by how much of the "not the canon style" impression each one
carries, which is not the same as how hard it is to fix. Gaps 1, 2, 3
and 4 are most of it.

### 1. Satoshi's crown is a dome with radial strand lines

The canon draws a tousled crop: a cowlick peak just off centre, spikes
flicking out at the temples, a fringe of separate pointed locks, and
sideburn locks running past the ear to jaw level. Every lock is gold at
the root and pale at the tip, so the two tones follow the direction each
lock lies in.

Ours is a plain part-circle with a scalloped fringe row and a ring of
pale teeth around its lower edge, and its strand lines all radiate from a
single point at the crown. At 2x (`out/56/heads_satoshi.png`) it reads as
an umbrella, and the radial lines are what make it read that way.

Measured: the canon crop is widest at 0.422 H at y 0.171, at the temples,
and narrows below that, ending at 0.756 H with the sideburn locks. Ours
is widest at 0.505 H at y 0.301, which is the bottom of the mass, because
the mass is a circle, and it ends at 0.434 H. So the silhouette's widest
point is in the wrong place, not merely the wrong size.

The crown tousle was tried and reverted on the owner's call, and is
parked with "potentially we will revisit this later" and a bar of beating
the plain circle by eye. Nothing here re-opens it; it is listed first
because it is the largest visual gap, and the rest of this entry is what
re-opening it would have to deal with.

The obstacle is structural rather than a matter of coordinates. The hair
contract gives a cut one `tip_edge`, a single region clipped across the
whole mass, which can express a band at a height but cannot express
"pale from here to the tip of each lock". A tousled cut needs the tone
boundary to follow the locks. That is a change to the contract in
`docs/architecture.md`, most likely a per-lock tip region rather than one
band, and it would want `_short_mass_shape`, `_short_tip_edge` and
`_short_strands` reworked together.

Cheaper partial move, if the contract change is not wanted: drop or
shorten the radial strand lines in `_short_strands`. They are carrying a
large part of the umbrella impression on their own, and removing a
feature is a legitimate column in a side-by-side.

### 2. Satoko's falls pinch at the jaw and hook inward

The canon's long hair is one curtain: two slabs of near-constant width
hanging straight down past the shoulders, tips flicking slightly outward,
the whole thing sitting behind the arms and forming the widest part of
the figure.

Ours reads as two ribbons pinned behind the ears, with a waist at jaw
level and a bulge lower down, hooking inward at the tips.

Measured, the width of one fall:

| y / H | canon | ours |
| --- | --- | --- |
| 0.28 | 0.057 | 0.049 |
| 0.32 | 0.054 | 0.030 |
| 0.36 | 0.056 | 0.029 |
| 0.45 | 0.043 | 0.091 |

The canon holds one width for the whole drop. Ours halves at 0.32 and
then more than triples by 0.45, which is the hourglass the strips show.
Consistent with that, our whole silhouette is 9% to 14% narrower than the
canon's through the head and hair zone (0.11 H to 0.40 H).

Fix in the fall rows of `_hair_mass_shape` and in `_fall_edge`, which has
to keep retracing the mass exactly.

### 3. The fringe sits too high, so the forehead is bare

In every canon drawing the fringe comes down to just above the brow, and
the brows sit partly under hair. It is built as two large swept locks
meeting at an off-centre parting, their edges long smooth curves ending
in points near the temples.

Ours forms an M with a sharp central peak far above the brows, leaving a
tall bare forehead with the brows drawn on open skin. Our strand lines
are long and nearly straight and cross the parting instead of following
the sweep.

This affects both characters at both builds and is the second thing the
eye catches after the hair silhouette. Fix in `_hairline_shape` and
`_short_hairline_shape` (lower the lock tips toward the brow line, which
`_face` puts at `eye_y - eye_r * 1.30`), and shorten the strand chains in
`_long_strands` and `_short_strands`.

### 4. Interior shadow *shapes* read as geometric wedges

The canon does use a second tone, but only on small elements: pouch
flaps, boot cuffs, the sleeve roll. What it never does is put a large
shading plane across a garment. On the tunic, the skirt and the apron
there is no second tone at all, and the form is carried by line work.

Ours paints five shadow shapes per figure, together about 2.7% of the
figure's ink area (Satoko chibi: tunic `#405c3c` 0.72%, undersleeve
`#897e69` 0.81%, skirt `#4b5b43` 0.38%, apron `#635245` 0.35%,
underskirt `#484744` 0.42%). The tunic one is a diagonal running from the
shoulder down across the chest to the hip, and it is the single most
artificial-looking mark on the figure.

So the finding is about the shapes, not about having a shadow tone.
There are two ways to act on it and the second is the owner's call, not
a mechanical fix:

- **Reshape.** Cut the wedges back to narrow turns along an edge, the way
  `_arms` already justifies its own ("wide enough and it stops reading as
  a rounded limb and starts reading as a two-tone plank"). Same reasoning,
  applied to the torso and the skirt. This stays inside the flat plus one
  shadow tone rule.
- **Remove the garment tones entirely**, which is what the canon shows.
  That is a change to a rule `CLAUDE.md` states as a hard constraint,
  "flat color + one shadow tone per surface, hard-edged", so it needs
  confirming rather than assuming. Worth previewing first: `shaded=False`
  already renders a figure with every shadow dropped.

One thing to notice while doing either: the shadows are painted as
`shade(colour)` at `opacity` 0.45 to 0.8, so the tone that lands is a
composite of the shadow and whatever is under it. `CLAUDE.md` asks for
one shadow tone per surface and `docs/architecture.md` says `shade()` is
the one place a shadow tone is decided; in practice the tone depends on
the stacking, and a shadow crossing two surfaces comes out two colours.
The shapes live in `_tunic`, `_skirt`, `_apron`, `_underskirt` and
`_arms`.

### 5. Line colour and hierarchy

The canon outline is effectively black: mean ink value 9 on the Satoko
chibi and 19 on the Satoshi chibi, sampled at `#080808`. Ours is
`#2b2b2b`, mean 47. Alongside that, the canon draws a stronger contrast
between a heavy silhouette and thin interior detail than we do, which is
part of why the canon reads crisper at the same line quantity.

`OUTLINE` is one constant in `character.py` and `_stroke_w` already
scales with the figure, so this is a small change with a whole-figure
effect. Worth testing at 2x before committing: a pure black outline can
tip a flat palette toward harsh.

### 6. The chibi eye is too round

Measured on Satoko's chibi, where the aperture detector agreed on both
eyes:

| | canon | ours |
| --- | --- | --- |
| aperture aspect (w/h) | 1.51 | 1.12 |
| aperture width / H | 0.111 | 0.090 |
| gap between apertures / H | 0.0781 | 0.0935 |

The canon eye is a wide almond and ours is nearly circular. In the canon
the iris touches both lids and leaves sclera only at the inner and outer
corners; ours leaves white above and below, which is what reads as
startled rather than guarded.

The knob is the aperture, not the iris. `presets.py` records that
`iris_size` was raised to 0.72 by eye precisely because a smaller iris in
an open aperture read startled, so shrinking the iris would undo a
decision already taken. Flattening the aperture (`eye_width`, and the lid
geometry in `_eye_shape`) lets the existing iris fill it.

**Spacing is a consequence here, not a separate gap.** The gap between
apertures is 20% wider than the canon's in absolute terms, and most of
that follows from the apertures themselves being 19% narrower while their
centres sit almost right. `eye_dx = r * 0.46` in `_face` is a canon
measurement someone already took deliberately, with its own note about
the eyes having previously crowded the middle, so it deserves the same
treatment as `iris_size`: widen the aperture first, re-measure, and only
then decide whether the spacing needs anything at all.

### 7. The head keeps its chibi shape at the realistic build

The canon adult head is an inverted egg: widest at the temples, cheeks
tapering to a narrow chin with a visible jaw angle. Ours is the same
rounded oval at both builds, nearly as wide at the jaw as at the temples.
Combined with gap 6 this is why the realistic build reads as a chibi head
on an adult body.

Measured: our silhouette is 8% to 18% wider than the canon's through the
head zone (0.02 H to 0.24 H) at the realistic build, for both
characters, while matching well at chibi.

`_head_shape(build)` already takes the build, so this is a shape edit in
one function rather than an architectural change.

### 8. Garment construction detail the canon draws and we do not

Individually small, collectively a lot of the "finished drawing" quality.
From `out/56/torso_chibi.png`, `torso_real.png` and `legs.png`:

- **Sleeve over limb.** The canon's short sleeve ends in a curved hem and
  the undersleeve below it is visibly *narrower*, so a garment hangs over
  a thinner arm. `_arms` deliberately makes the arm the sleeve's own
  width (`out_top = _sleeve_half_w(sk) * 0.99`) to avoid a step at the
  hem, and the result reads as one continuous plank from shoulder to
  wrist. The canon wants that step; it is what says "sleeve".
- **Cuffs.** Satoshi's canon undersleeves are rolled at the forearm with
  a thicker cuff and two roll lines, leaving bare forearm below. Satoko's
  end in a wrist cuff. Ours run to the wrist with no cuff at either build.
- **Shoulder slope.** The canon shoulder runs down and out from the neck.
  Ours is a nearly horizontal cap with a square outer corner, most
  visible on Satoshi at the realistic build.
- **Apron.** The canon apron hangs *below* a belt, and the pouches hang
  at the hips off the belt. Ours is a rectangle with a hard top edge and
  the pouches sit on its upper corners, so at chibi the whole assembly
  reads as a satchel across the hips rather than an apron. The canon
  adult also has a knotted belt tie hanging down the apron's front, which
  we have nothing for.
- **Belt.** The canon buckle is a frame with a pin, with a keeper and
  stitching along the strap. Ours is a hollow square.
- **Underskirt.** The canon adult's is a pleated skirt with vertical fold
  lines and a scalloped hem. Ours is a flat band, and at chibi its heavy
  dark rim under a wide hem reads as a tray.
- **Trousers.** The canon has pocket seams, a fly seam, hip shaping and a
  taper to the ankle. Ours are two rectangles with background visible
  between them up to the hip.
- **Boots.** The canon boot has a cuff, a tongue, eyelets, a heel and a
  sole. Ours is a rounded blob with lace crosses. At the realistic build
  ours is also 17% to 27% narrower than the canon's through the foot.
- **Hands.** The canon indicates fingers with short strokes. Ours are
  teardrop blobs, and at chibi they sit at the same height as the pouches
  so they merge with them.

### 9. Chibi hem too wide, adult hem band too wide

Our chibi silhouette runs 13% to 17% wider than the canon's at 0.80 H to
0.85 H, and the adult 8% to 20% wider at the same rows. In both cases it
is the skirt hem plus the underskirt band. `hem_half_w` lerps to
`head_r * 1.11` at chibi; the canon's flare is gentler and its underskirt
does not extend past the skirt.

## Suggested order

1. Gap 4 (reshape the shadow wedges, or ask about dropping the garment
   tones). Smallest change, immediate effect, and it makes everything
   else easier to judge.
2. Gap 3 (fringe down to the brow). Affects all four renders.
3. Gap 2 (Satoko's fall width).
4. Gap 6 (flatten the chibi eye, then re-measure the spacing).
5. Gap 5 (outline toward black), which is worth doing after 4 so the two
   are judged separately.
6. Gap 7 (adult head taper) and gap 8's sleeve step, which together are
   most of what makes the realistic build read as an adult.
7. Gap 8's remaining detail and gap 9.
8. Gap 1 only if the owner re-opens the crown, since it needs a change to
   the hair contract to do properly.

Gap 8's items are independent of each other and can be picked off in any
order, which makes them good filler work between the larger passes.
