# Risa on the adult woman's body

Started 2026-10-20 at the owner's request. Risa is drawn today on the tall slender body (`docs/risa-plan.md`), which is to be deprecated. The references in
`ref/risa-adult/` show her on Franzi's adult body (a white bikini, then her school uniform), 1312 x 1504 px, with Grok segment layers for each. The job is to move
her onto `adult_female`.

## Owner's decisions (2026-10-20)

1. The new Risa **replaces** the `risa` preset. The old tall slender one is not kept beside it.
2. The blazer is the references' **navy**, not the grey she has now.
3. Order: her head and hair on the bikini body first, then the uniform, piece by piece.
4. The adult build's rules stand (SFW, age floor in the render code, no sensitive parts, every other render byte-identical).

## What the references say about the head

Overlaying Franzi's render on the bikini reference (`harness/risa_adult/compare_head.py`) shows the two share one head: the jaw, chin, neck, nose and mouth sit where
Franzi's do, on the same 1312 px grid, so Franzi's head calibration (origin 660, 270.5, 175.7 px per head radius, the chin at row 434) applies unchanged. What differs is
the hair (long, straight, a blunt fringe with two wedges of forehead showing, both ears under it, the whole mass hanging behind the shoulders and the arms), the eyes
(set about 10 px further right, her right eye 12 px higher: the head is turned and tilted a little), the brows (thin lines across the fringe) and the clip (a gold
bracket frame). Her body is not identical to Franzi's (a smaller bust, narrower hips and shoulders in the reference), which this stage leaves alone.

## Stage 1: the head and hair (done 2026-10-20, not committed)

How it is built, so that Franzi's drawing stays byte for byte what it was:

* **A head cut per adult hairstyle** (`ts/src/body-adult-cuts.ts`). The traced head data (the face's visible skin, the hair silhouette, the strand lines, the strips and
  ears, the soft finish's clumps) is a consequence of the hair, so it is chosen by `hairstyle`. `swept_ponytail` is Franzi's (her existing data, moved behind the
  table) and is the fallback; `long_straight_fringed` is Risa's. The adult head parts read the cut from the character instead of module constants.
* **Risa's data** (`ts/src/body-adult-risa-data.ts`, generated, do not edit): the face's skin (108 segments), the hair silhouette (481), 95 strand lines and two brows.
* **Per-cut settings**: the strand lines' tone and weight (darker than the hair for red hair, lighter for Franzi's black), the weight of the stroke round the face (0.45
  for Risa, whose reference draws the hairline thin), brows as tapering lines with their own widths, where the clip sits, where the irises sit, the white of the eye and the
  weight of the soft line under it.
* **A `bracket` hair clip** (`ts/src/hair.ts`, `clipBracket`), and `hairClip` takes an optional placement so a cut can say where the clip sits instead of the shared
  placement beside the hair's edge. The adult body's `_hair_clip` passes the cut's.
* **The hairstyle on a chibi body** falls back (`ADULT_CUTS_ON_CHIBI` in `core-head.ts`): `long_straight_fringed` to the chibi `long_fringed`.

How the data was made (`harness/risa_adult/`, run through `./harness/run.sh`, `PYTHONPATH=.claude/skills/trace-reference` for the overlay):

| script | what |
|---|---|
| `outline_masks.py` | the face skin and the hair as masks from the bikini image (hair told from skin by the green to red ratio, its segment layer, the body in front of the hair filled so the silhouette runs under it) |
| `strands_auto.py` | a Hessian ridge detector for the dark lines inside the hair, walked into polylines (her hair has dozens, too many to read off a grid by hand as Franzi's dozen were) |
| `brows.py` | the two brows, read off gridded zooms and snapped onto the drawn line |
| `outline_trace.py` | fits the masks and writes `ts/src/body-adult-risa-data.ts` (run `outline_masks.py`, `strands_auto.py`, `brows.py`, then this) |
| `compare_head.py`, `overlay_chains.py`, `eye_metrics.py` | the reference beside our render and a 50% blend; the fitted chains over the reference; iris centres, widths and heights measured in both |
| `risa.ts` | Risa on the adult body in her underwear, the harness's base (`SVG=out/risa_adult/risa.svg` for `compare_head.py`) |

Measured: the two irises now sit at (617.0, 320.5) and (727.1, 308.3) against the reference's (617.3, 319.9) and (727.1, 307.8). Widths 32 against 31 and 30; heights 36 to 38
against 34 and 32 (the reference's lid covers more of the iris).

Gates after stage 1: typecheck, 964 TypeScript tests pass (7 skipped, 0 fail), `refresh-ref-out.sh --check`, `refresh-bases.sh --check` and `refresh-catalogue.sh --check` green.
The one fixture that moved is the catalogue (`harness/ts_port/golden-updates-risa/README.md`): a hairstyle and a clip entry added, nothing else.

## Not done in stage 1

* The preset is not switched yet. `RISA` in `ts/src/presets.ts` still draws the tall slender body with the old uniform, so the cast and `ref-out/risa.png` are unchanged. The
  new head is reachable through the harness base `harness/risa_adult/risa.ts` and the `long_straight_fringed` hairstyle on an `adult_female` figure. Switching the preset
  moves her goldens (`ref-out/`, the recorded calls, `ts/fixtures/presets.json` and the links), which is one deliberate change to make when the uniform is on.
* The eye is Franzi's traced model with Risa's iris centres and a few settings (`eye_openness` 0.85, a warm white, a faint lower line). Her lid is a little thicker and her
  eye a little rounder than the reference's. A retrace of the eye would move more of the model's constants.
* The soft breast arcs over the cups and the armpit creases are still Franzi's positions, so with a smaller bust the creases sit a little off the cups' sides.
* The hair has no highlight bands (flat finish) and the soft finish has no clumps for this cut.

## The bust (done 2026-10-20, not committed)

The adult woman's bust is now a control: the existing `bust` field, read by the adult code through the skeleton (which already carries it). Not a new field: that would have moved
every recorded character (the ten updaters of `harness/ts_port/golden-updates-elbow/`). Its meaning on the adult woman differs from the chibi's (0 flat, up to 1): it is an offset from her
traced bust, so 0 is Franzi's and her drawing is byte-identical, below 0 smaller and above 0 larger (`adultBustScale`: 1 + 0.5 * bust, so -0.5 is 0.75 of it).

* `bustWarp` (`ts/src/body-adult-parts.ts`) moves the bust's traced shapes: x scales about the centre line (the cleavage's V stays put), depth about the top of the breasts (0.45
  head heights), with a ramp over the neck and straps that keeps them where they are. It is applied to the breast contour (`adultBreastPoints`, hence every garment's soft
  breast line) and the top's cup outline (`adultBandPath`).
* The body outline does not move: at bust height it is the shoulder and arm, not the breast.
* The garments traced on Franzi (the dirndl's blouse and bodice) keep their cut, so on a smaller bust they are not refitted. Risa's own uniform will be traced on her bust.
* Fitted to Risa's reference with `harness/risa_adult/bust_metrics.py`: her bikini-top layer is 277 wide and its lower edge is at row 762; ours at `bust` 0 is 313 wide with the edge at 778,
  at -0.15 it is 288 and 764, at -0.18 283 and 761. Risa is -0.18 (`harness/risa_adult/risa.ts`).
* The web tool does not offer it: `bust` is in `BODY_HIDDEN_EXTRA` for the adult woman, since its range there (0 to 1) cannot say "smaller than traced".

## The fringe as locks (2026-10-21, not committed)

The first trace smoothed the fringe into one mass whose lower edge read as a bell with drips (the face edge was fitted with a heavy smoothing and grown by 2 px, which widened the
slits between locks). It is now built the way the reference is drawn:

* The skin runs up under the fringe (`face_ext` in `outline_masks.py`), so the gaps between the locks show skin.
* The fringe's hair is a closed shape of its own drawn over the skin (`RISA_FRINGE_HAIR`) with the real blade tips and slits. The hair there is found by colour, because the face rule
  counted the thin dark lock tips as skin. Its domain stops above the eyes (`harness/risa_adult/zones.py`, `DOM_BOX`) so it never covers the cheeks' outline.
* One thin line (1.8 px, the reference's) runs along the whole edge where it meets skin (`RISA_FRINGE_LINES`), instead of the face's heavy stroke.
* The lock lines (`RISA_HAIR_EDGE_STRANDS`, found by the ridge detector on a local-contrast view, looking a few px past the hair onto the skin) run to the edge and end blunt; the inner
  ones are drawn again over the fringe's fill, clipped to it, because the fill covers the ones drawn behind the face.

Checked against the reference by `harness/risa_adult/fringe_length_check.py`: the lowest hair row in 25 columns across the fringe, ours minus the reference's, is -2.4 px on average
(ours a little shorter) and 3.2 px mean absolute, the worst column -11 px. `compare3.py` draws the reference, a saved earlier render and the current one side by side.

## Registration of the uniform (2026-10-21)

`ref/risa-adult/README.md` says the images share a pixel grid. They share a size, not a scale: the uniform figure is drawn at 0.786 of the bikini figure's (it has to fit the knees and
the loafers in the frame), with the head higher. The first skirt was traced at the uniform's pixels as if they were the bikini's and hung under the breasts. Two steps now, both in
`harness/risa_adult/registration.py`:

1. **Register on the head.** The irises' centres fix the scale (1.273: 110.5 px apart in the bikini image, 86.8 in the uniform one) and the offset; there is no rotation (the eye line
   slopes -0.110 and -0.109). The hair clip then lands within a pixel of the bikini's. Blended, the head, the hair and the shoulders line up.
2. **Map landmark to landmark onto our body** (`to_body`). Our body is Franzi's, and against Risa's reference its briefs sit lower (top at row 1041 against 1019, the crotch at 1226 against
   1189) and are 5% wider (355 px against 339), measured by `body_landmarks.py`. A cut traced at the reference's pixels would hang too high (the briefs showed under the first skirt's
   hem), so every cut goes through the row mapping the plan's decision 3 asks for, with widths scaled the same way.

## The clothing references 02 to 07 (PR 4, 2026-10-21)

The owner prepared single-piece references because tracing from the clothed image (01) hides parts behind the blazer: `07` is the skirt over the bikini top, `06` the blouse over the
briefs, `05` the blazer laid flat, `02` to `04` the uniform without the blazer, the ribbon, the socks and shoes. `06` and `07` are framed closer (head to thighs, Risa drawn at about the
same scale as the bikini: irises 110.8 and 111.2 px apart against 110.5), the rest are the uniform's smaller scale. `registration.py` now registers any of them to the bikini grid
(`Registration(path)`): the irises give the scale and the offset, checked by the hair clip, which lands within 2 px of the bikini's on all seven.

## The pleated skirt (2026-10-21, not committed)

Traced again from `07` (the first trace, from 01, saw only a band under the blazer): the silhouette is the whole layer, waistband included, the pleats are the dark valley lines (7 paths,
the band's lower edge among them). The darker strip beside each fold, which 07 shows on every fold, is not yet drawn: the detector finds it for two. First trace notes follow.

`skirt_cut` `"pleated"` on the adult body draws a traced skirt (`ts/src/body-adult-skirt-pleated-data.ts`, generated by `harness/risa_adult/skirt_trace.py`): the silhouette (sides and top
the hull of the visible layer, the hem the layer's own lower edge so the panels step), and nine fold lines found as luminance valleys. One flat colour (`#697897`, the layer's
median); the darker strip beside each fold in the reference is left out (it was detected for three folds of ten, and a partial set would read as inconsistent). Franzi's dirndl skirt is
unchanged (`skirt_cut` null). The control is hidden in the web tool on the adult body (`BODY_HIDDEN_EXTRA`).

## The shirt (2026-10-21, not committed)

From `06` (the blouse over the briefs, the single-piece reference), registered by the irises. The torso and the sleeves are **not traced**: the plan's lesson is to trace nothing below the chin off
a reference whose body is not ours, and a long sleeve that has to cover our arm exactly is that case. They are built in `ts/src/body-adult-shirt.ts` from this body's own tables (the shoulder, the
arm's two edges, the torso's side) with an ease, as one outline so there are no seams. What the reference gives, because the body cannot, is traced by `harness/risa_adult/shirt_trace.py`
(`ts/src/body-adult-shirt-data.ts`):

* the **collar** (the wings' sharp tips, read off an 8x gridded zoom) and its inner edge, which is the shirt's neckline, so the skin shows through the opening as in the reference and not through a
  straight cut;
* the **hem**, the layer's lowest row column by column, with the V of the shirttails' opening in it; its two ends are the torso's side (the reference's torso is narrower than ours, so the traced ends
  left a ledge);
* the **button band's two lines**, a quadratic fitted to each (the detector's wobble made them look hand-drawn) and the **five buttons** centred between them, plus the stand's button;
* the cuffs are a line across each sleeve at the top of a 0.19 H band.

The details are a darker tone of the cloth at half weight, not ink: the reference's are thin pale lines.

Owner's first feedback (2026-10-21), done: (1) **one centre line**: the reference's drifts (the collar's V at x 679, the buttons from 675 to 666), so the collar, its stand and button are moved onto the body's centre line,
the buttons and the band's two lines (11 px either side) are put on it, and the hem's V is made symmetric about it, apex at the last button's end: neck, stand button, five buttons and the opening are one vertical line;
(2) the **breasts as a soft outline** over the cloth (the contour the skin and the top draw, a tone darker than the cloth at 0.55 weight), masked where the button band crosses it; (3) an **armhole line**, the arm's
inner edge carried up past the armpit along the body's own underarm crease (`RIB_KNOTS`) to the shoulder, in the outline's ink, so the sleeve reads as an arm.

Selected by `collar_cut` `"shirt"` on a tunic (no new field; hidden in the web tool on the adult body like `skirt_cut`). Tucked, it is drawn in the legs' layer under the skirt, and its sleeves are drawn again over the skirt,
from just below the armpit down (`ARM_OVER_HOOKS` in body-adult-parts.ts: the skin the arms were drawn again with over a skirt would show through a long sleeve otherwise).

## The ribbon (2026-10-21, not committed)

The bow at the collar, `adultRibbon` in `ts/src/body-adult-shirt.ts`, drawn from `ribbon_color` (no new field). Traced from `06`'s `blue-ribbon`: points read off a 12x gridded zoom of the right half, the left its
mirror about the collar's centre (the same rule as the collar, which the owner approved), emitted by `shirt_trace.py` into `body-adult-shirt-data.ts`. Seven flat pieces, back to front: a band each side that
tucks up behind the collar, the two tails over the button band, the two loops with a slit each (the cloth shows through, filled in the shirt's colour) and the knot. A thin edge in a dark tone of the ribbon's
own blue (`shade`, 0.4 of the ink), not the ink: the reference edges the bow lightly, and ink made the tails look thin.

It is drawn between the shirt's body and its collar so the collar's wings lie over the bands, as in the reference. On a figure with no shirt the same bow is drawn on its own (`_ribbon` on the adult body),
since the chibi's traced bow would sit wrong on this body.

Colour: the layer in `06` is a dark blue (median `#2d4c7c`), but the uniform's ribbon is light blue in `01`, `02`, `04` and `05` (medians `#5482aa` to `#5b86b3`), so `06` looks like a drift of Grok's and the
preset will take `#5784ae`, the median of `02`'s (the shirt without a blazer, nothing over it). The shape is `06`'s, a wider bow than `02`'s, whose loops stand more upright.

Not yet: raised arms (the shirt ignores them), the soft shading of the cloth, and the shirt's colour on the preset (the layer's median is `#f5eaea`).

## The blazer (2026-10-21, not committed)

`coat_cut` `"blazer"` on a coat draws `adultBlazer` (`ts/src/body-adult-blazer.ts`, replacing the adult open coat for that cut; hidden in the web tool like `collar_cut`). Navy `#212940` (the median of `01`'s
blazer, `(33, 41, 63)`), buttons `coat_button_color` (gold).

Same method as the shirt: the torso and the sleeves are **not** traced but built from our body's tables with a roomier ease (shoulder 0.035, sleeve 0.05 out and 0.03 in, torso 0.035 H, flaring 0.03 toward the hem),
as two front panels, each one closed outline: the V's top, over the shoulder, down the sleeve to just above the shirt's cuffs (1.86 H, so the cuff shows), up its inner edge, down the torso's side (eased out of the
armpit so there is no hook), along the hem, up the front edge and the V's edge. The left panel is the right's mirror. What the flat reference gives is traced by hand from 3x gridded zooms
(`harness/risa_adult/blazer_trace.py`, `ts/src/body-adult-blazer-data.ts`): the V of the opening, the collar's edge, its notch, the lapel's top and fold, the front edge with its flare and the hem, the flap and welt
pockets, the dart lines and the buttons with their buttonhole slits.

`05` shows the garment laid flat, so it is fitted to the body by its own landmarks, not by the irises. Vertical: the collar's top 0.0, the neck 0.12, the first button 1.00, the last 1.48, the hem 1.95 H below the chin
(cross-checked on `01`, registered, where the buttons are at 0.93, 1.20, 1.42 and the hem at 1.87: the two agree to 0.1 H). Horizontal: the flat blazer's torso is 237 px a side at the bust, which is our blazer's half-width
there at 460 px per H; things near the front are in head heights at that scale, things across the width (pockets, darts, hem) are a fraction of the half-width at their row, so they follow the body.

The two panels' straight front edges lie on the centre line (their strokes merge); only the flare leaves it. The sleeves are drawn again over the skirt (`ARM_OVER_HOOKS`, as the shirt's), the shirt's first from the
blazer's sleeve end down so its cuffs show, then the blazer's, as fill plus two edge lines so no seam shows where the redraw starts.

Owner's first feedback (2026-10-21), done: (1) the breasts as a soft outline on the cloth (the contour the skin and the top draw, a lighter navy since a darker one does not show on it, clipped to the panels and
hidden under the lapels by a patch of cloth), and the sleeve's seam is now a smooth curve instead of the body's own wavy underarm crease, which was what read as bubbles; (2) the V's top and the collar start level with
the shirt's collar (0.172 H across, 0.11 down) instead of the flat blazer's corner (0.189, 0.057), which put the tips above and outside it; (3) the pockets and the dart lines are drawn before the lapel's lines, so the
fold runs over the welt where they meet, not under it.

Width check against the reference (2026-10-21, `harness/risa_adult/blazer_outline_check.py`: our blazer's outline in cyan over `01` registered, the reference blazer's boundary in yellow): at first ours was
467 px wide (sleeves included) at row 620 against the reference's 406, and 561 against 515 at the hem. Cutting the ease to the least that covers the body and the shirt (blazer 0.02 / 0.018 / 0.015 / 0.03 H, the shirt
0.008 under it, `EASE_UNDER`) took 11 px off (456, hem 537); that is the floor, because the blazer cannot be narrower than the arms it covers: tried at -0.04 H, the shirt's white sleeve and then the arm's skin
show outside it. Where the remaining difference comes from, measured: our bare body at row 620 is 435 px arm to arm and the bikini reference's own body is 432, so the body matches the bikini image, but the clothed
images are narrower than it: the blazer in `01` is 406 and the shirt in `06` is 409 at the same row (6% less). So no garment on a body that equals the bikini's can match the clothed references' width; making the
garments narrower than the body is not possible without narrowing the arms. If the width matters, the fix is a shoulder and arm width control on the body (the owner's fallback), not the garments.

Not yet: the preset (below), the lapel's and the sleeves' shading, raised arms, the breast pocket's welt is on the right only as in `05` (the worn blazer in `01` has it too).

## The blazer's breast contours, and the socks and loafers (2026-10-21, not committed)

The soft breast contours on the blazer were only for fixing its shape (the owner) and are removed, with the patch that hid them under the lapels. The blazer is approved.

**Socks and loafers.** `boot_cut` `"loafer"` with `knee_sock_color` draws the school pair in `adultKneeSocks` and `adultBoots` (`ts/src/body-adult-garments.ts`), the existing adult garments with a school variant: the sock's
top edge dips at the front in one curve (0.07 H, as in `02` and `03`), it has no band line, and its lower end is open, so only its sides and top are inked. The loafer is inked along its sides and toe only, with the
rim an arch across the instep (the sock shows inside it), the strap a lighter band with its slot, positioned as fractions of the foot's length (rim at 0.22, strap 0.44 to 0.59). Colours are the references' medians:
sock `#2a282b`, loafer `#4d332c`. Registration of 02, 03 and 04 on a taller canvas (`Registration.register(..., size=(1312, 2100))`) because the uniform figure's feet are below the bikini canvas.

**Retraced from `08` (2026-10-21, after PR 5).** The owner's new close-up shows the loafers whole (a bare leg-and-shoe image at its own scale, 1152 x 1728, so not registrable by the irises). The loafer is traced
in its own coordinates (`harness/risa_adult/loafer_trace.py`, `ts/src/body-adult-loafer-data.ts`): the viewer's-left shoe's silhouette from its `brown-loafers-1` layer, notch at the top included (where the sock
shows), symmetrised about its own centre line and mirrored for the other shoe, plus the strap's two edges, the slot, the seam round the oval below it and the dark sole band's upper edge read off a 5x gridded zoom.
It is then fitted to our foot (`loaferFit`): as wide as the foot's last, 1.6 widths long (the reference's aspect), its toe at the foot's toe. Because the shoe is shorter than our foot, the school sock
continues down the instep to a quarter of the way into the shoe (`shoeFoot`, shared with the boots), drawn inside the shoe's counters; the sock shows through the notch, as in `08`. Not drawn: the glossy highlight
stripes and the grey floor shadow (flat style).

Sock to shoe (owner's feedback): the school sock's lower sides used to follow the foot's outline, which stepped at the ankle where the leg's tables end and was wider than the shoe's counters (a hard cut with
spikes beside the shoe). Now they are the reference's profile: in `08` the sock narrows to about 0.62 of the shoe's width where it enters it and runs straight down inside the counters (measured on its layer, in
shoe widths from the shoe's axis: 0.31 a side at the shoe's top). From 4.0 H, where the leg's own edges are, down to the shoe's top the sock's edges ease (smoothstep) from the leg's to 0.33 shoe widths about the
shoe's centre, then run on to a third of the way into the shoe, hidden.

Sock width (owner's feedback): the sock's ink edge now lies on the leg's own, a fifth of a canvas pixel (about a pixel of the reference grid) proud of it. It stood 0.012 H off the leg's knots, so with its own
stroke it overhung by 4 to 5 px of the reference grid a side; measured by rendering with and without the sock and comparing each row's edges (now 1 to 2 px).

Known mismatch, measured: our legs are longer than the uniform references'. Registered by the head, `02`'s loafers are at row about 1910 and the sock top at 1507, while ours (the adult body's own legs, Franzi's) put the sock top at 1700 and the
feet at about 2300. The references' legs are about 20 to 25% shorter than the body's below the knee, so the socks cannot sit where the references' do without changing the body's legs. The shapes are the references'; the placement is the body's.

## Face revisit (2026-10-21, not committed)

Owner's two points. (1) The cheek contour had small notches and hooks where hair strands cross it in the mask. The face mask is now low-passed with a 6 px Gaussian in the band of the cheeks and upper
jaw (rows 318 to 430, and for the chain's own mask only at the cheeks' edges, columns under 602 and over 732, away from the fringe), done after the hair and the fringe are computed, so only the face edge changes: the
regenerated data differs in `RISA_SKIN_FACE` alone (the strand blocks the detector re-found slightly differently were put back, the fringe was approved). (2) The right cheek's blush: it was at Franzi's
position, but Risa's right eye is 12 px higher than her left (the head is tilted), so the cut now carries its own cheek positions (`cheeks` in `body-adult-cuts.ts`): left (608, 361) as before, right (728, 350), the
same distance from the centre line as the left and 11 px higher, following the eye.

**Eyelids, first pass (owner's question: can Risa's lids be closer to her reference's).** Franzi's eye model draws a heavy black lid band, a wing and thick lashes; Risa's reference has a thin dark-brown lid line,
fine lashes and a long pointed outer corner. Three per-cut settings (`eye` in `body-adult-cuts.ts`, defaults leave Franzi byte for byte): `lidThickness` (the band's lower edge moves toward its upper edge, so 0.5 is half
as thick; `lidBand(thickness)` in `body-adult-eyes.ts`), `lidColor` (the lid, the lashes, the aperture's lower line and the lid's tail; Risa's `#2e1a14`) and `lashWeight` (0.7). Not done, and what a retrace
would add: the reference's two eyes differ (the viewer's right is wider and more slanted than the left) where ours mirrors one, the outer wing is longer, the inner corner has a small flick, and the iris has a yellow
lower half. That would be per-eye lid, wing and lash shapes traced as the brows were (`harness/risa_adult/brows.py` is the template), and an iris gradient in two flat tones.

Lid joined to the eye (owner): thinning the band left a gap between the lid's new lower edge and the eye's white and outline, which still began at the circle the thick band used to cover. Under a thin lid
(`lidThickness` below 1) the aperture's top edge, and so the white, is now the thinned lid's own lower edge (`lidLower` in `body-adult-eyes.ts`, from the lid's inner tip to the outer corner), and the eye's lower
outline runs on from the inner corner to that tip and starts at the thinned outer corner, so lid and outline are one line. The lid's thin tail along the old circle is not drawn then.

Blush clip (owner): Risa's cheeks are now clipped to the face's traced skin (`adult-cheek-clip`), so the left blush no longer tints the hair past the contour; Franzi's blush is unclipped as before.

## The preset switch (2026-10-21, not committed)

`RISA` in `ts/src/presets.ts` is now on `adult_female`: `long_straight_fringed`, `bust` -0.18, skin `#fac4a8`, eyes `#78925a`, the hair `#6b1f2a` (the owner's colour; the reference's median is `#7b232d`), the bracket clip `#d2a368`
and the whole uniform with the colours the pieces were traced with (shirt `#f4ecec`, ribbon `#5784ae`, skirt `#697897`, blazer `#212940`, buttons `#ba975e`, socks `#2a292c`, loafers `#4b332c`), `eye_openness` 0.85 and `blush` 1.12.
Her old definition stays as `RISA_TALL_SLENDER` (deprecated, tests only). The recorded fixtures that held her were updated as `harness/ts_port/golden-updates-risa-adult/README.md` says.

Not done: removing `tall_slender` and the chibi cuts only she used. They are in the recorded Python calls (`harness/ts_port/fixtures/calls/` has them in `_registry.json`, `BodyProfile.applied.json`, the hair and arm calls...), which
would all need rewriting, and the tests of the traced cuts would go with them: a bigger change with its own risk, so it waits for the owner's decision. Until then the body type is still in the web tool's list of bodies.

## Poses in the uniform (2026-10-21, not committed)

The companion draws Risa as a character that waves, cheers and shows emotions (`public/frames.js` keys the gestures by `body === "adult_female"`, so no companion change is needed). Emotions, blinks and mouths
already worked. The arms did not: the blazer held `armsUnderSleeves` true (a coat's sleeve is cut for the hanging arm), and neither the shirt nor the blazer had a sleeve that follows a raised or bent arm.

- `armsUnderSleeves` (`body-adult-pose.ts`) now ignores a `blazer` coat cut. Any other coat or a robe still holds the arms down.
- `adultPosedSleeve` (`body-adult-pose-arm.ts`) draws a sleeve as the posed arm's own fill grown by stroking (ink `2*ease+ink`, cloth `2*ease`), in the arm's turned frame, clipped at `endD` and inked across.
  The cut below the end line takes out only the forearm's band, plus `cutMargin` outline widths beside it (a plain cut at the end line also sliced the upper arm of a folded arm). The shirt uses 3, the blazer
  1.2, so the shirt's cuff (the shirt ends at 2.0, the blazer at 1.86) shows between them without a wedge of shirt colour beside it.
- The shirt (`body-adult-shirt.ts`) and the blazer (`body-adult-blazer.ts`) cut their torso piece along the armhole on a raised side (`torsoWithoutRaisedSleeves`, a short slanted cap seam so there is no flat ledge)
  and draw the posed sleeve after; hanging sides are as before.
- The generic sleeve head disc (`adultPosedSleeveHead`) leaves the hand out of its clip for a shirt: a folded arm lays the hand beside the shoulder and the disc painted it in the shirt's colour.
- Franzi's and Risa's hanging drawings are byte-identical (`ref-out/` check), and `ts/test/adult-pose.test.ts` pins the sleeve counts, the cut's shape and the unchanged hanging drawing.

Checked by eye on both sides and mixed poses (hang, wave 1 and 2, cheer A and B, 90 degrees, one arm folded and the other up) and through the companion's own frame requests (7 emotions x 5 frames, wave 2, cheer 2).
Open: the shirt alone (no blazer) has a small ledge at the shoulder top on a folded arm; not Risa's outfit, not fixed. The companion sees this from 0.6.0 on (`creator-release-to-companion`).

## Her face made straight (2026-10-21, not committed)

The reference has her head tilted (the right eye 12 px above the left, about 6.3 degrees) and turned, so the companion's emotions read oddly: the nose and mouth are Franzi's, placed by her eyes, and sat left of Risa's.
`ts/src/body-adult-cut-level.ts` builds the straight face from the traced data, applied in `body-adult-cuts.ts` to the `long_straight_fringed` cut only:

- the eyes are level about one midline (`RISA_MID` 672.2, the traced eyes' midline, at y 313.5, 55.2 px either side); the eye shape was already one set mirrored, only the placement tilted;
- the left brow is the traced one moved up to the new eye height, the right brow its mirror;
- the jaw is made symmetric about the midline from the cheekbone line (y 315) down, blended in over 30 px, so the chin is on the midline; above it the contour is as traced, because the hair decides the hairline;
- the cheeks are mirrored about the midline;
- `featuresAt` (new on `AdultHeadCut`, `[0, 0]` for Franzi's) moves the nose and the mouth to the midline and up with the eyes.

Not done on purpose: the fringe and the hair stay as traced (turning the fringe upright by the same angle left ticks at the temples, tried and dropped); it is hair, so some asymmetry reads as natural. Franzi's
drawing is unchanged. `ref-out/risa.*` and the three `pages.json` cases that draw her were refreshed with `./refresh-ref-out.sh` and `harness/ts_port/golden-updates-risa-adult/upd_fixtures.ts` (the head only changed; no
field of her preset did). `ts/test/adult-body.test.ts` pins the levelling and the symmetry.

## Franzi's face made straight (2026-10-21, approved by the owner)

Her traced face was tilted a little as well (the right eye 3.5 px above the left, the right brow about 7 px above the left, the right mouth corner 3.5 px higher, the mouth 4 px right of her eyes' midline and the chin 7 px right of it).
Her neutral face reads fine, but every expression amplifies it (the shared happy lifts a mouth whose right corner is already higher, so it reads as a smirk). Tuning the emotions cannot remove an asymmetry of the base geometry
(`mouth_curve` and `brow_tilt` scale around the existing slope), so the geometry was straightened instead, with the same pieces as Risa's: in `body-adult-cuts.ts`, `irisAt` level at the traced pair's midline (662.25, 323.25),
`featuresAt` and `symmetricMouth` for the nose and mouth, `symmetricJaw` for the jaw from y 330 down; in `body-adult-parts.ts` the left brow kept and the right its mirror (`STRAIGHT_BROW_L`/`R`) and the cheeks mirrored;
in `body-adult-eyes.ts` the default `IRIS_AT`. Her hair, ears and the eye shapes are as traced.

Her default drawing therefore moved, and the recorded pins with it, with the owner's say: `ref-out/franzi.*`, the three hashes of `adult-face-baseline.test.ts` (and the dirndl hash in `adult-pose.test.ts`), the `eye_size` test's tolerance
(1% to 1.5%: it reads extents off one-decimal coordinates), and the cut assertion of the Risa test. Nothing else of the recorded fixtures held her face.

The companion's happy for the two adult cuts is an open smile, `CUT_FACES` in its `public/frames.js` (`mouth_width` 1.5, `mouth_curve` 1.5, `mouth_open` 0.6, `blush` 1.3, `eye_openness` 0.8, `brow_tilt` 0), the owner's pick of six variations.

## Stage 2: the uniform (next), then the clean-up

Back to front, as `docs/franzi-outfits-plan.md` does for the dirndl, each piece traced from `ref/risa-adult/segments/01-school-uniform/` onto the adult body, flat colour, checked
against the reference at 50%: the skirt (a pleated one on the adult hips), the shirt with its collar, the ribbon bow, the blazer in navy with its gold buttons and pockets,
the knee socks and the loafers (the reference crops the loafers at its bottom edge). Then the preset switch, the goldens, and the removal of `tall_slender` and the traced
pieces only it used.
