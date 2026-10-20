# Franzi's emotions and gestures, for the companion

Written 2026-10-20, after the adult-body campaign (v0.5.0). State: steps 0 to 4 done and most of 5 (see Progress), the companion side planned. The record of the earlier campaign is
`adult-body-status.md`; her outfits are in `franzi-outfits-plan.md`.

The companion app (`../anime_ai_companion`) draws a character as a set of pictures it swaps between. Franzi was built without any of
what it asks for. This file says what it asks for, what she does now, what the AI-made reference pack shows, what has to be built and in
what order, and what the owner has to decide first.

Sources, so the claims can be checked: the companion's `docs/frame-packs.md`, `emotions.json`, `public/frames.js`, `public/avatar.js`,
`src/render-ops.ts`, `packs/franzi-dress/`; this repo's `ts/src/body-adult-parts.ts`, `body-adult-eyes.ts`, `presets.ts`.

## What the companion asks for (read from its code and docs)

- **Seven emotions**, the keys of its `emotions.json`: `neutral`, `happy`, `sad`, `angry`, `surprised`, `shy`, `thinking`. Each is a few
  `FaceStyle` values laid over the character's face: `mouth_curve`, `mouth_open`, `mouth_width`, `brow_tilt`, `blush`, `eye_openness`,
  `eye_size`, `iris_size`, `eye_tilt`, `gaze`.
- **Five frames per emotion**: the rest picture, a blink (`eyes_closed`) and three mouth openings (`mouth_open` of the rest value, then at
  least 0.3, 0.55 and 0.85). Seven emotions of five frames is 35.
- **Two gestures of two frames each**, drawn in the happy face with the mouth at rest: `wave` is `right_arm_out` 128 then 152, `cheer` is
  both `right_arm_out` and `left_arm_out` 125 then 150 (degrees from the body). A pose may override any top-level field of the character.
  The four frames bring the total to 39, the size of the AI pack.
- **Framing**: `public/avatar.js` hard-codes the view box, `55 0 290 330` for the close-up and `0 0 400 500` for the full body. Her canvas
  is 400 by 500, so the close-up is her head down to about the dirndl's hem (`hem_y` is 322; the crop ends at 330). Its shape, 290 by 330,
  has the same aspect as the AI pack's pictures (940 by 1070), so they were framed to match.
- **A way to see the format**: `python/make_sample_pack.py` draws a pack from a preset. It imports the removed Python package, so it cannot
  run any more (read from its source, not run).

## What she did before step 1 (rendered 2026-10-20)

Franzi in the dirndl, drawn with each field at several values, compared byte for byte with her default render:

| field | values tried | result |
|---|---|---|
| `mouth_curve` | -2, 0, 1.6, 3 | identical |
| `mouth_open` | 0.3, 0.65, 1 | identical |
| `blush` | 0, 1.5, 2, 3 | identical |
| `eye_openness` | 0, 0.3, 0.5, 1.5 | identical |
| `eye_lower_lid`, `brow_tilt`, `gaze` | both signs or both ends | identical |
| `eyes_closed` | true | identical (she cannot blink) |
| `right_arm_out` | -90, -30, 36, 60, 90, 128, 160 | identical |
| `left_arm_out` | 125 (with the right) | identical |
| the seven companion emotions, and the four gesture poses | as the companion sends them | all identical to neutral |

`mouth_curve` 3 with `finish` set to soft: identical too (the other fields were not tried under soft). This agrees with the 5d entry in `adult-body-status.md` ("the adult head replaces the shared
face"). Reading the code says why: `adultFace` draws a fixed traced nose and mouth and reads only the skin tone, `adultBrows` draws two
fixed polygons, `adultEyes` draws the traced eye and reads only the eye colour, and the arms are part of the body's one fused outline
(`body-adult-parts.ts`: "the arms are part of the one outline for now"), with the hands traced onto it.

**Resolved 2026-10-20:** `ts/test/ignored-fields.ts` (behind the catalogue's `BODY_IGNORES`) only tests the fields the web page has a control for. `mouth_curve`, `mouth_open`,
`blush`, `eye_openness`, `brow_tilt`, `gaze` and `eyes_closed` are not page controls, so they were never tested and appear in neither list. "Not on the ignored list" meant
"absent", not "live". The controls it does test (`eye_size`, `eye_tilt`, `iris_size`, `mouth_width`, `lash` and others) are correctly listed as ignored.

## What the AI pack shows (`../anime_ai_companion/packs/franzi-dress/`, looked at on contact sheets, not at full size)

Made with Grok Imagine from a dirndl base picture (apparently the one in `ref/franzi/00-base-dirndl.png`; not compared), one edit per picture, 940 by 1070. The blinks and
mouths are scripted over the emotion pictures. It is the reference for what each frame should read as, with the limit the repo's rule
sets: **nothing below the chin is traced off a picture whose body is not ours**, and these are other renders of the base, so the arms in
them give angles, lengths and the gesture's idea, not outlines.

| picture | what changes from neutral |
|---|---|
| happy | open smiling mouth |
| sad | brows raised at the inner ends, small downturned mouth |
| angry | brows drawn down and in, eyes narrowed, mouth flat |
| surprised | eyes wider, brows raised, small round open mouth |
| shy | strong blush on both cheeks, small mouth |
| thinking | mouth closed. **Also a pose:** one hand at the chin, the other arm across the waist (the companion's `thinking` is face-only, so this stays out of scope) |
| wave-1, wave-2 | her right arm (the viewer's left) raised with the elbow bent, forearm near vertical, open palm toward the viewer beside the head; the upper arm stays low. The two frames differ by a small tilt of forearm and hand |
| cheer-1 | both arms straight up in a V, fists closed, the puff sleeves stay on the upper arms |
| cheer-2 | the viewer's-left arm straight up with a fist, the other arm bent with the fist at the shoulder (a flex) |

The companion's own cheer is symmetric (both arms, 125 then 150), so cheer-2's flex is not something its contract can ask for.

## The bikini pack is the better reference for the arms

`../anime_ai_companion-packs/packs-src/franzi-bikini` (found 2026-10-20, the owner's suggestion) is the same 43-file layout as the dirndl pack with her in a white halter
bikini and briefs, so the arms, shoulders and torso are least covered. Same rule as above: it gives angles, lengths and the idea of each pose, not outlines to trace.
Seen on a contact sheet, its gestures differ from the dirndl pack's cheers:

| picture | what it shows |
|---|---|
| wave-1, wave-2 | her right arm (the viewer's left) raised, elbow bent, forearm near vertical, open palm toward the viewer at head level; the other arm hangs. The frames differ by a small tilt of forearm and hand |
| cheer-1 | both arms bent, both fists raised beside the head at shoulder height (a pump). **A straight swing of the arm cannot draw this**, which counts toward elbow fields (C, option 2) |
| cheer-2 | both arms straight up in a V with open hands; the head sits lower in the picture, so the fingertips fit inside it |

The companion's cheer (both arms 125 then 150 degrees) is the straight V of cheer-2; cheer-1's fists are not something its contract can ask for today. Whichever way C goes, the
arms are measured against this pack first, and the dirndl pack is used for how the sleeves behave.

## What has to exist

### A. A face that reads the fields (no arms needed)

All of it is traced geometry made parametric, not re-traced per emotion, and each emotion is then judged against the pack's picture with the
aligned head overlay (`harness/franzi/aligned.py`; the pack's heads need a mapping first, by eye line and pupil distance, as for the refs).

1. **Blink** (`eyes_closed`): a closed eye from the traced lid, the upper lid's curve as one thick tapering line with the lashes. The
   smallest piece that makes her feel alive.
2. **Mouth**: `mouth_curve` bends the traced line; `mouth_open` and `mouth_width` need a new shape, an open mouth (the chibi's flat dark red
   inside, no teeth or tongue, as in the house style) at three sizes for the talk frames, and a happy open smile. Flat colour, nothing anatomical.
3. **Brows**: `brow_tilt` as a turn and lift of each traced polygon about its inner end; `brow_weight` and `brow_length` if the angry brow
   needs them.
4. **Blush**: flat tint marks on the cheeks, a second tone on a small element (`finish` soft may use a gradient, as the chibi does).
5. **Lids and gaze**: `eye_openness` lowers the lid over the iris (it already covers the top of it), `gaze` shifts the iris and pupil,
   `eye_size` and `iris_size` scale the traced eye about its centre (surprised wants it), `eye_tilt` turns it (angry).

The catch on blush: its default is 1, which is what her neutral face carries today, so a face that starts reading it would put a blush on
her neutral picture. Either her preset sets `blush` to 0 (a change to the preset, so to her recorded metadata) or the adult blush is drawn
relative to the default. Decision 3.

### B. Arms that can be raised (the large piece)

Today the arms hang inside the body's one outline, the armpit creases and hands are drawn on it, the blouse's puff sleeve is one traced
piece with the blouse body mapped onto the hanging arm, and `adultArmsOver` redraws the arms over a skirt. Raising one needs:

1. **The arms split from the body outline**, as limbs placed along a posed line (shoulder, elbow, wrist) using the width profile in the
   `ARM_INNER` and `ARM_OUTER` tables, and the torso's side taken from `TORSO_SIDE` where the arm used to be. The hanging pose must stay
   byte-identical, so the split is proved on the hanging case first (the body gate, `ref-out/`).
2. **Hands**: the open palm for the wave and the fist for the cheer, traced from `ref/franzi/hands/open-palm.png` and `fist.png`, mapped as
   the relaxed hand was (`harness/franzi_hands/`). Only the relaxed hand exists. Which hand shows is driven by the pose, not by the chibi's
   `hand_style`, which the adult body ignores.
3. **Sleeves that follow the arm**: the blouse's sleeve and its frilled cuff rotate with the upper arm, so the traced sleeve has to be split
   from the blouse body along its seam (the seam line already exists). The cheer pictures keep the puff on the upper arm and show the bare
   forearm above the cuff.
4. **Which garments**: the dirndl, the blouse and bare arms first. The coat, the robe (hanging sleeves) and the hakama do not follow a
   raised arm, so when one is worn the adult body keeps the arms down, a gesture then does nothing, and the catalogue's ignore list says so.
   That is the companion's own rule for a gesture with no pictures. Decision 2.
5. **Draw order**: a raised arm is in front of the body and in front of the ponytail (hair is behind the shoulder).
6. **Room above the head**: see the next section.

### C. The arm contract

The companion sends one angle per arm, 128 to 152 degrees from the body. One angle gives a straight arm, which suits the cheer's V and makes
a stiff wave (the pack's wave is an elbow bend). The same angles serve both gestures, so the angle alone cannot ask for a bent arm.
Options:

1. **Straight swing only, on the existing fields.** No schema change, the companion works as it is. Judge the wave by eye and the AI pack.
2. **Add `right_elbow` and `left_elbow` (a bend, neutral 0)** to `CharacterParams`. The wave becomes honest, but a new field moves the
   recorded fixtures (the rules for that are in `harness/ts_port/golden-updates-stage7/README.md`, as for `bodice_color`) and needs the
   owner's say, and the companion's gesture table for her has to change.

Recommended: option 1 first, and look at it before deciding on 2. Decision 1.

### D. The frame (measured 2026-10-20)

Her canvas is 400 by 500, her head top is at y 25.5 and the companion's views start at y 0. Rendering the companion's four gesture frames (wave 128 and 152 on the right arm, cheer 125 and 150 on both,
fists in the cheer) and finding the topmost inked pixel of each: **wave 1 at y 12, wave 2 at y -22, cheer 1 at y 23, cheer 2 at y -15.** So the first frame of each gesture fits and the second is cut off
at the top, by 22 and 15 units, in both of the companion's views (`0 0 400 500` and the close-up `55 0 290 330`), and the hands go about 45 units above her head. (My first estimate from the reference's
proportions, -28 to -30, was too large for both, so the measurement replaces it.) The AI pack does not have the problem, being framed with the fists inside the picture. Options:
a view box that starts at about y -30 for these frames (a companion-side constant, or the frames request returning the posed figure's bounding box), or keeping the swing at or below about 135 degrees.
A test should assert that no pose frame's ink leaves the view box, whatever is chosen. Decision 6.

### E. On the companion's side (not this repo, but the plan depends on it)

- Replace `python/make_sample_pack.py` with a TypeScript script that draws the 39 frames of a preset (or put one in this repo's `ts/bin/`).
  Franzi drawn this way is the acceptance sample: the same 39 names as the AI pack.
- The frame crop (`CLOSE_UP`, `FULL_BODY`) and, if chosen, the bounding box (D).
- A new creator release for it to pin. The companion's `package.json` pins `v0.5.0`. The release is a minor one (0.6.0), on the owner's say.

## Order of work

Each step ends in something the companion can use, and in green gates: `npm run typecheck`, `npm test`, the three `refresh-*.sh --check`
(her default picture and every other character stay byte-identical, so `ref-out/` does not move), and the body gate (IoU at least 0.93).
Nothing is committed without the owner's say.

0. **Questions and baseline. Done 2026-10-20.** The owner's decisions below. Resolve the `ignoredFields` discrepancy. Write the byte-identity test: a
   default Franzi renders the same bytes as v0.5.0.
1. **Blink and mouth** (A1, A2). **Done 2026-10-20.** a talking, blinking Franzi in neutral and happy. Pack-maker script on the companion's side to see it.
2. **The rest of the face** (A3 to A5): the seven emotions. Owner checks each against the AI pack's picture. **Done 2026-10-20**: brows, lids, gaze, blush, and `eye_size`, `iris_size`, `eye_tilt`.
3. **Hands** (B2): the open palm and the fist. **Done 2026-10-20.**
4. **Arms** (B1, B3 to B5): split, prove the hanging case unchanged, then bare arms, the blouse, the dirndl. **Done 2026-10-20** as a straight swing: the arm is the hanging arm turned about the shoulder; the blouse's sleeve goes with it; a coat or a robe keeps the arms down.
5. **Wave and cheer** (C, D): wire the contract, settle the frame, the no-clipping test. **Wired 2026-10-20** (the companion's own angles draw the gestures; the cheer needs `grip_style` fist); the frame (D) and the no-clipping test wait on decision 6.
6. **Companion** (E) and a release, if the owner says release.

Rules that still bind: SFW (an open mouth is fine, nothing anatomical), flat colour with a second tone only on small elements, no new field
without the owner's say, the age floor, the adult parts replace the shared ones only on an adult body so no other character's output moves.

## Progress

**Steps 0 and 1 done 2026-10-20** (committed on `dev`):

- **Baseline** (`ts/test/adult-face-baseline.test.ts`): the SHA-256 of her default drawing in the dirndl, in her underwear and in the soft finish, taken from v0.5.0 before any
  change, and a check that her face carries the defaults of the fields being added. It passes with the new code, so her neutral picture is byte for byte what 0.5.0 drew.
- **Blink** (`eyes_closed`, `body-adult-eyes.ts`): one thick lid line along where the aperture's lower outline ran, from the inner corner to the wing's tip (the wing stays where the
  open eye's is), and the thick lash flick moved down to start from its inner end. No white, iris or crease. The two thin flicks and a hairline tail were tried and looked like a
  scribble at close-up scale, so they are not drawn when shut.
- **Mouth** (`adultMouthPoints` and the open mouth in `adultFace`, `body-adult-parts.ts`): `mouth_curve` scales each point's distance from the line between the corners (1 is the traced
  line, 0 straight, below 0 a frown); `mouth_width` scales it about its middle; `mouth_open` adds the chibi's flat dark red inside under the traced line as the upper lip, with a lower edge
  whose drop is 0.5 mouth widths at `mouth_open` 1 (the chibi's 1.0 read as a gape on this narrow mouth). At the defaults the traced points are returned untouched.
- **Tests**: 7 in the baseline file (blink, the four talk openings grow, curve and width, ids unique and references resolved in both finishes, the chibi unchanged). Full suite 922 pass, 7
  skipped, 0 fail; typecheck and the three `refresh-*.sh --check` green; the catalogue fixture did not move.
- **Looked at**: rest, blink and three talk frames in the companion's close-up crop (`55 0 290 330`) and zoomed on the face. They read as a blink and a mouth opening wider. Not compared
  with the AI pack's faces yet (that needs the head mapping, step 2).

Known gaps from step 1, for step 2: the surprised mouth (width 0.6, open 0.65) is a lopsided crescent, not the pack's round "o" (the traced line is uneven and the lower edge follows it);
the happy open smile has no cheeks or eye curve to go with it; no blush, brows, lids or gaze yet.

**Step 2 done 2026-10-20** (steps 0 and 1 are commit `44fbc97`, brows to blush `b6c9830`, the eye fields the next commit):

- **Brows** (`tiltBrow`, `body-adult-parts.ts`): `brow_tilt` turns each traced brow about its middle, 9 degrees per unit, positive dropping the inner end (the chibi's sign). 0 returns the traced points.
- **Lids** (`eye_openness`, `body-adult-eyes.ts`): the lid band, the thin line along the white's top, the aperture's top edge and the lash flicks move down together (the crease three quarters as far),
  by up to 40 eye-frame pixels at 0, less toward the inner end and none at the wing tip; the iris is cropped by the lowered aperture, so no white shows above the lid.
- **Gaze** (`gaze`): the iris, pupil and highlights shift sideways inside the aperture clip, 7 eye-frame pixels at the full look, both eyes the same way (+1 to the viewer's right, the chibi's sign).
- **Blush** (`blush`): **decision 3 taken: relative to the default.** Her neutral face carries 1 and draws none; above 1 two flat tint ellipses (the chibi's blush colour for her skin) appear on the
  cheeks, their opacity 2 x (blush - 1) x the chibi's, so 1.5 is the chibi's own, never past solid. This keeps her preset and every recorded fixture as they were, and matches the AI pack, where only
  the shy picture blushes. Flat in both finishes (no soft-finish gradient yet).
- **Tests** (13 in `adult-face-baseline.test.ts`): brow direction, the lid's drop growing as the value falls, gaze direction and symmetry, blush thresholds and opacity, ids unique in both finishes, and
  the seven companion emotions drawn as seven different faces (the test also checks its copy of the table against the companion's `emotions.json` when that checkout is next to this one).
  Full suite 928 pass, 7 skipped, 0 fail; typecheck and the three refresh checks green.
- **Looked at**: all seven emotions in the companion's close-up crop, beside the AI pack's pictures (`out/franzi-frames/step2-ours-vs-pack.png`, not tracked).

**Eye fields** (`eyeFrame` in `body-adult-eyes.ts`, built after that comparison): the traced eye is her neutral, so `eye_size` scales the whole eye about the iris by its ratio to the default 1 (the aperture, lid,
crease, lashes and the stroke widths follow), `iris_size` scales the iris and pupil by the ratio to the default 0.72 (highlights keep their size), and `eye_tilt` turns the eye about the iris by 25 degrees per unit
away from the default 0.1, positive raising the outer corner (the chibi's sign). A shut eye follows size and tilt too. At the defaults the traced mapping is returned untouched, so her default drawing keeps its bytes.
`mouth_width`, `eye_size`, `iris_size` and `eye_tilt` are now drawn but hidden in the web tool (`BODY_HIDDEN_EXTRA`) until the owner approves the catalogue fixture change that showing them makes. Four more tests
(17 in the baseline file); full suite 932 pass, 7 skipped, 0 fail; typecheck and the three refresh checks green. `surprised` now has the bigger eyes and iris it asks for, and `angry` its turned eyes.

What the comparison still shows, for the later polish: **our emotions are subtler than the pack's**, `surprised` still has a lopsided crescent where the pack has a round mouth, and `shy`'s eyes are not lowered as in the
pack, which no field of the companion's asks for.

**The close-up crop does not frame her like the pack.** The companion's `CLOSE_UP` (`55 0 290 330`) shows her from the head top (y 25) to just above the knees with wide margins, so she is small in the
frame, where the AI pack is framed from the head to about the apron with the head larger. A tighter crop for her (for example head to waist) is a companion-side constant, part of decision 6.

**`mouth_width` stays hidden in the web tool.** It now draws on her, but showing the control changes the catalogue's recorded fixture, so it sits in `BODY_HIDDEN_EXTRA`
(`catalogue-tables.ts`) until the owner says. The companion sets the field directly and does not need the control.

**Steps 3 to 5 done 2026-10-20** (committed after `a9f1451`). The bikini pack was the arm reference, as the owner suggested.

- **Hands, traced** (`harness/franzi_hands/poses.py`, `poses_lines.py`; data in `ts/src/body-adult-hand-poses-data.ts` and `body-adult-hand-poses-lines-data.ts`). The open palm and the fist from `ref/franzi/hands/`
  in the frame of the relaxed hand: the arm's knot coordinates, the viewer's-left hand hanging from the wrist at depth 2.0 with the fingers down and the thumb on the outer side (the anatomical position; the
  open palm needs a vertical flip and the fist a half turn to get there, the derivation is in the script's docstring). The open palm shares the relaxed hand's scale (their wrists are 328 and 331 px wide in
  the close-ups) and the fist is scaled to the same wrist width; the outline method is the relaxed hand's (silhouette, inset by the hand's half stroke, blended into the arm's knots over D_CUT to D_BLEND,
  fitted as an open quadratic B-spline). Interiors: the open palm's thenar arc, two palm creases and the thumb's web line (points read off a gridded contrast-stretched view and snapped onto the drawn ridge)
  and nine short finger creases (ridges inside Grok's finger cut-outs); the fist's four nails, four finger pieces (the ragged thumb piece left out) and the dark cavity, from Grok's cut-outs.
- **Arms** (`ts/src/body-adult-pose.ts`, `body-adult-pose-arm.ts`, and `without` in `adultBodyPath`). `right_arm_out` and `left_arm_out` are degrees from hanging, clamped to 0 to 180, an angle under 1 hangs.
  A raised arm is the hanging arm built from the same knot tables (the shoulder's outer edge, `ARM_OUTER`, `ARM_INNER`, the traced hand), turned about the shoulder's tip (depth 0.36) by a `rotate` on a group,
  so it is exactly the hanging arm, raised, with the same widths and stroke weights (the stroke tapers to the hand's weight in eight bands). The body outline leaves that arm out (the shoulder stops at the
  tip, the outline goes in to the armpit and down the ribs; the hanging side keeps its arm, and with no arm raised the path is the same as ever). The arm's fill is its outline path filled as it is, which
  closes it with a straight chord across the shoulder, not stroked (a half-disc cap was tried first and swung out of the torso at the armpit, leaving a nub of skin with no outline). Her default drawing is
  byte for byte v0.5.0's (the baseline test).
- **The hand a pose draws**: the open palm, or the fist when `grip_style` is "fist" (the chibi's word for a closed hand; `hand_style` is a free string and `grip_style` was ignored on her, so no field is added).
  The companion's cheer must therefore add `grip_style: "fist"` to its pose override (it already lets a pose override any top-level field); its wave needs nothing. A hanging arm is a fist too with that field (see the fixes below).
- **The blouse's sleeve** (`adultBlouse`): the blouse is one traced piece, so with an arm raised it is split along its seam (the line where the sleeve meets the bodice, carried up above the shoulder and
  down through the gap to depth 1.25, below the cuff and above the hem's flare) into a body piece and one sleeve piece per raised arm, each the whole blouse clipped to its region; the sleeve is turned by the
  arm's own transform, so the puff, the frilled cuff and the bare forearm come out as in the AI pack's dirndl. The dirndl's wave and cheer work. A blouse tucked into a skirt, or worn loose, splits the same
  way; with no arm raised the blouse is the one piece it was. **A coat or a robe still keeps the arms down** (decision 2 as recommended): their sleeves are not cut to follow.
- **Tests** (`ts/test/adult-pose.test.ts`, 10): hanging below a degree, the turn of each side and the clamp, only the raised side changes, the open palm against the fist, unique ids and resolved
  references (both finishes, the dirndl too), the SVG staying small, the traced chains, the blouse split and its turn matching the arm's, a coat or robe keeping the arms down. Full suite 942 pass, 7
  skipped, 0 fail; typecheck and the three refresh checks green. The raised-arm SVG was rendered by cairosvg and looked at; it was **not opened in a browser** (the in-app pane shows a local file as a
  snapshot it will not let me inspect), and it relies on `use`, clip paths and nested transforms, so that is worth doing.
- **Against the bikini pack**: the straight arm is the cheer-2 V and reads right at 125 and 150 degrees (with fists where the pack has open hands). It is **not** the pack's wave (an elbow bend, the forearm
  near vertical) or cheer-1 (both fists pumped at shoulder height). The straight swing is what decision 1 recommended; the pack's wave and cheer-1 are the case for reopening it (elbow fields, C option 2).
- **Fixes after the owner's report (2026-10-20)**: a raised fist showed a dark line across the wrist that made the hand look detached. **Cause:** the viewer's-right arm's path was wound backwards. The path runs down the
  outer edge, round the hand and up the inner edge on both sides, and the traced hand chain runs outer to inner, but for the mirrored side I had copied the body outline's walk, which goes the other way round
  (its right-hand path goes down the inner edge), so the path jumped across the wrist and drew the hand backwards. The viewer's-left arm was right, which is why renders of the left arm looked fine. Fixed
  (`armGeometry` walks the chain forward on both sides), and a test now pins the viewer's-right arm to the exact mirror of the left, point for point (it fails on the old code, checked by putting the old walk
  back). Checked after the fix: both sides, the open palm and the fist, raised and not, on a light background.
  **Hanging arms:** a hanging arm with `grip_style` "fist" used to keep the relaxed hand (the fist only showed when the arm was raised). It is now the traced fist: the fist's outline replaces the relaxed hand's in
  the body outline (`adultBodyPath`'s `handChain`, the same frame) and its cavity, finger separations and nails are drawn in `adultHandsDetail`. **An arm under six degrees now hangs** (`ARM_POSE_MIN`):
  drawn on its own at 1 to 5 degrees it left a sliver of page between the arm and the ribs, where the one outline has no gap above the gap's tip. Because `grip_style` now draws on her it is hidden in the web
  tool with the other fields that do (`BODY_HIDDEN_EXTRA`), so the catalogue fixture did not move.
  **Hands in front** (second report: with the arm down the fist was partly hidden behind the apron). The hand zone that redraws a hand over garments stops at an inner limit that follows the thigh, which the
  relaxed hand fits inside; the fist's curled fingers reach 0.60 to 0.62 H from the centre line at depths 2.2 to 2.35, past the limit (0.618 to 0.628), so the skirt and apron covered them and cut them off flat
  (on bare legs the thigh's outline ran across them). A hanging fist is now also drawn as its own overlay in `adultHandsDetail` (the traced outline filled with skin, closed across the wrist, edged at the
  hand's weight) after the garments, and a raised arm's hand, below the wrist, is drawn again in the detail layer (`adultPosedArmDetail`), so a hand held low over the skirt is in front of it too. The
  relaxed hand keeps the zone redraw it had.
  **Sleeve head** (third report: with the blouse the raised arms looked cut off, a cutout, with bare shoulder showing). Seen in a zoomed render: the sleeve piece ended in a flat cut where it met the bodice,
  and the cloth that covered the shoulder had turned away with the arm, leaving a patch of skin beside the strap. `adultPosedSleeveHead` (`body-adult-pose-arm.ts`, in the torso layer, so under the blouse's body
  piece, the bodice and the turned sleeve) lays the blouse's colour over the shoulder first: a disc of 0.15 H about the shoulder joint (a turn about the joint leaves it where it is, so it fits at every angle),
  clipped to the skin there (the body without its arm and the arm itself, so it cannot reach past the silhouette), with the shoulder's outline and the arm's drawn again over it at full weight. With the arms
  down nothing changes (the blouse is not split then, and her default drawing is still v0.5.0's byte for byte); with no blouse there is no head. Looked at at 40, 90 and 130 degrees on the left shoulder, and on
  the whole figure for the wave (135, 152), the cheer (125, 150) and 60 degrees.
  **Sleeve cap outline** (the owner circled the end of the sleeve by the shoulder in a screenshot: it read as a hard cut, not connected fabric). Cause, seen in a zoomed render: when the arm is raised the
  sleeve's cap (its top, at the shoulder) ends up as the end beside the bodice, and the outline along the cap's edge, which was the shoulder's edge, was still stroked there. The sleeve piece is now its fill, clipped
  to the sleeve's region, and its outline as a separate element clipped to the same region less the cap's corner (depth above 0.42 H, half-width inside 0.58 H; `CAP_D`, `CAP_V` in `body-adult-garments.ts`), so the
  outline stays along the outer edge, the cuff and the underside and the cloth runs into the bodice. The sleeve head's disc is 0.2 H (it was 0.15) to cover the last bare tick under the sleeve's end. Checked
  at 125, 90 and 60 degrees (zoomed) and on the whole figure; one tiny hook remains at the very end of the underside edge. 947 tests pass (15 in `adult-pose.test.ts`), typecheck and the three refresh checks green.
- **Elbow fields** (the owner's request after the wave and cheer comparison with the packs; decision 1's option 2, built). `CharacterParams` gained `right_elbow` and `left_elbow` (degrees, 0 neutral, clamped to 0 to
  150, named from the viewer's side like `right_arm_out`; the chibi ignores them). A bend of a degree or more draws the arm on its own, and a hanging arm that is bent is held out at least six degrees (the one
  outline cannot bend). **Geometry** (`armGeometry`, `body-adult-pose-arm.ts`): the arm is drawn in the forearm's own frame, where the forearm hangs straight and the hand is traced, under the transform
  `rotate(shoulder turn about the shoulder) rotate(bend about the elbow)`, so the forearm, the hand, its details, the stroke bands and the hand-in-front redraw needed nothing else. The upper arm is the hanging upper
  arm turned back by the bend about the elbow (at depth 1.3 H, a knot of both edge tables), and the two are one outline: on the outer edge, where the bend closes, the edges cross and are cut at the crossing;
  on the inner edge, where it opens, they are joined by a round elbow (an SVG arc, centred on the elbow with the arm's half width, sweeping the way the bend turns). The path is stroked in three pieces (the outer
  edge to the wrist, the hand with its taper bands, the inner edge back) because a bent upper arm lies in the hand's rows of the forearm's frame. The blouse's sleeve is carried by the upper arm's turn alone
  (`armTurn`), so the puff stays on the upper arm and the forearm is bare. Straight arms are drawn by the code they always were (a bend under a degree is no bend). **Values that match the packs** (read off the
  comparison sheet): the wave is `right_arm_out` 6 with `right_elbow` 148 then 155 (the upper arm hugging the body as the pack's does, the forearm tilted out, then vertical), the pack's cheer-1 is both arms 16 with elbows 148 and `grip_style` "fist", and its cheer-2
  is the straight V (150, open hands). The companion's `GESTURES` still send straight angles; it should send these (a pose may override any top-level field, and its field list comes from the creator's registry).
  **Recorded fixtures**: the two fields moved every recorded text that holds a character, so the goldens were updated by mechanical rules from their old content and checked against the new code, as for
  `bodice_color`: `harness/ts_port/golden-updates-elbow/README.md` (nineteen tests were red, all green after; one hard-coded field count, 29 to 31, changed by hand). `docs/api.md` documents the fields. 952 tests
  pass (20 in `adult-pose.test.ts`: the registry default, the clamp and the minimum angle, the composite transform and the sleeve's single turn, the mirror image command for command including the elbow's
  arc, unique ids and resolved references with and without the blouse), typecheck and the three refresh checks green. Looked at in the bikini and the dirndl beside both packs
  (`out/franzi-frames/elbow-poses-vs-packs.png`), and zoomed on the elbow at 90, 135 and 145 degrees.
  **Proper-arm pass** (the owner found the first bent arms creepy, a chicken wing with the upper arm out at 28 and 42 degrees): the values above are the pack's; `ARM_ELBOW_MAX` is 155 because the two outer edges cross inside the forearm only down to a 20 degree crease (the hanging tables lean the upper arm about 7 and the forearm about 12 degrees outward, so the crease is |175 - bend|), and tighter folds drew a chord, so the crossing search covers 48 dense points and a test checks `arm-a` has no chord; an arm held under 30 degrees strokes its inner edge only from the armpit (`D_ARMPIT`), so no seam runs up the shoulder; the skin is now the arm without its hand (`-fill`) plus the hand path (`-hand-edge`), each filled, so the hand's long outline is written once (a raised arm's SVG is about 20 KB larger than a hanging one, down from 54 KB). **Fold line** (the owner's sketch over the first render, to set the upper and lower arm apart as the pack does; first built on the wrong edge, the upper arm's, and corrected: it is the forearm's, the hand's side): the forearm's edge, which the crease cuts, goes on over the upper arm toward the elbow for 0.35 H (`FOLD_LEN`) in three bands (`adult-pose-l-fold-0..2`, weights 1, 1 and 0.7 of the outline's, round caps), only on a bent arm whose edges cross. **Shoulder and armpit** (owner's red marks on a close zoom: an unnatural bend at the shoulder's top and a gap at the armpit): `RAISED_SHOULDER_D` moved from 0.36 to 0.4, a knot of the shoulder table, because a tip between knots lay on the straight interpolation and made the curve wobble, which read as a step in the outline; the body's shoulder line and the arm's edge now both leave the tip in the direction of the hanging curve (`withoutLastSpan`, `withoutFirstSpan` drop a phantom span so the Catmull tangent comes from the real neighbouring knots); an arm held under 30 degrees turns about its outer tip (blending back to the chord's middle by 50), so the tip does not move off the body's line; its inner stroke starts where the body's armpit line comes out from under the arm's fill, found by crossing the two curves, so the gap closes in a clean apex; both arm strokes have round caps. A one pixel hairline remains at the shoulder join (the arm fill's corner), seen only at 8 times zoom. The 54 KB-to-20 KB size note above is unchanged. **Dirndl sleeve when raised** (the owner: it was traced from the lowered arm, so it read as cut off; options were references or mirroring, mirroring chosen after comparing the pack's `cheer-1`, `cheer-2` and `wave-1`, where the sleeve is a puffed bag round the whole upper arm with a ring cuff and no seam along its inner side): a raised sleeve's inner edge is now the traced outer edge reflected across the upper arm's centre line (`armAxis`), or the seam where that lies further out (cap and cuff), inked at the full outline weight; the seam line is no longer drawn along the sleeve (the bodice keeps it as its armhole); the gather and cuff are the traced ones. Only raised sleeves change, the hanging blouse is as it was. Looked at against the pack (`out/franzi-frames/sleeve-vs-pack.png`). Not done: the pack's puff is fuller, and at 150 degrees the sleeve's cap end is a soft flap with no outline (the cap outline stays omitted by the earlier fix). **Raised arms at 90 to 150 degrees, bikini** (the owner: the arms looked cut off rather than attached): both arm edges are now inked from where the body's own line (shoulder line, in to the armpit and down the ribs) comes out from under the arm's fill, found by crossing the two curves, for every angle (it was the small-angle inner edge only). The upper edge runs on from the shoulder line with no stub of ink left inside the body; a lower edge that misses the line (at 125 and 150 degrees it passes the armpit) is rounded into it with a short quadratic through its own top, which ends where the line leaves the fill (the chord crossing). The arm strokes have butt caps again. At 3 times zoom there is still a one pixel notch at the armpit join and a tick where an inner edge starts at 45 degrees; the dirndl's sleeve cap flap at 150 degrees is untouched (the owner takes the bikini first). **Rounded shoulder and armpit** (the owner: smooth the transition with a slight curve): where the shoulder line meets a raised arm's upper edge (at 90 to 150 degrees) the corner is rounded over `CORNER_R` = 0.14 H each way, a quadratic with the corner as its control point, drawn after the arm: the old ink either side of it is covered with skin (a stroke 0.3 px wider than the ink, so no fringe shows), the piece of page cut off is filled with skin, and the curve is inked; nothing is done when the lines are within 160 degrees of straight (arms held in). The armpit's ink starts 1.2 half-strokes past the crossing so a butt end does not stick a corner out. The body's hidden shoulder-to-armpit link is covered with skin from just past the tip to the point it leaves the arm, which removes most of the hairline it drew from the tip into the skin at small angles; a faint trace of it remains at 6 and 20 degrees at 3 times zoom. Tried and dropped: an ink-only variant of the body path without the link (it also removed the armpit line's upper part). At 45 degrees a small tick at the armpit and a step at the shoulder remain. **Dirndl sleeve ends against the body** (the owner's red marks at 125 degrees: the sleeve's inner end had no outline and a flap of cloth hung beyond the body at 125 and 150 degrees): the sleeve's cap (the cloth above the sleeve proper, over the shoulder, which swings with the arm) is its own fill, `adult-blouse-cap-l/r`, clipped to the body's silhouette in the turned frame (`armTurnBack` carries the body outline into it), so it shows only where it lies over the body and no longer hangs in the air; the sleeve proper (from `CAP_D`) is filled and inked as before. **Lower outline to the body** (the owner: extend it until it meets the body): the sleeve proper now begins higher, at `SLEEVE_TOP` = 0.3 H instead of 0.42, with its inner edge going up the seam to there, and the cut across the arm at that depth, which lies beside the body once the arm is raised 105 degrees (`RIM_FROM`) or more, is inked as a short curve bowed 0.05 H toward the shoulder (`RIM_BOW`), so the sleeve ends in a rim against the bodice and no unlined edge of cloth is left (found by colouring the sleeve and cap pieces: the unlined edge was this cut). Below 105 degrees the cut lies in the shoulder's cloth and is not inked. The cap's top still has no outline (kept from the earlier cap fix). Tried and dropped: inking the seam above the sleeve (it was clipped away or dangled in the air). **Breast side restored** (the owner: with the arms raised the bikini top's breast bulge was cut off where the hanging arms used to be): the top is clipped to the body's outline, and the rib line of a side without its arm ran inside the cup's outer edge (the cup bulges to 0.452 H at 0.78 H, the line was 0.42), so the cup's side was clipped away. `RIB_KNOTS` now follow the cup's outer edge a little outside it (0.462 at 0.74, 0.458 at 0.82, 0.432 at 0.9), so the side is skin with the cup over it; only sides with a raised arm use it, the hanging figure is as it was. **White strips beside the dirndl bodice** (the owner: white residuals on the dirndl with the arms raised): the blouse's body piece was cut along the seam, which lies outside the bodice's edge from the neckline to the waist (the edge is at 0.40 to 0.46 H, the seam 0.43 to 0.46 and 0.39 below), and the cloth between them, the blouse's armhole allowance, is hidden by the arm when it hangs but showed as a white strip down each side of the bodice when it is raised (found by colouring the body piece). The cut now follows the bodice's outer edge (chain points 23 to 34, `BODICE_SIDE_FROM` and `BODICE_SIDE_TO`) wherever that is further in than the seam, on raised sides only; skin shows there instead. **Bodice notches closed** (the owner, against the pack: the notches beside the bodice at the waist, with a red line for the fix): the traced bodice nips in at the waist and flares at its hem, which the hanging arm hides and a raised one shows as a notch. On a side whose arm is raised the bodice is now filled out in its own colour along `BODICE_FILL`: the traced edge from the bust's widest point (0.467 H at 0.81 H, a hair outside the trace so its outline is covered) down its nip at the waist, which is kept as in the hanging figure, then on to the sash at the traced waist's width (0.362 H at 1.36 H) without the step and flare the trace has between (the first version ran straight at 0.43 H and stuck out past the apron's waistband, the owner), with the new edge inked over the traced outline; `adultBodiceCloth` takes the sides to fill, `adultBodice` passes the raised ones, a hanging side is as it was. **Owner's decisions for the 0.5.1 release (2026-10-21)**: the clipped fingertips of the wave and cheer-2 frames (decision 6) are accepted as they are; the 45 degree armpit tick and shoulder step, the faint hairline at 6 and 20 degrees, the unoutlined top of the dirndl sleeve's cap and the packs' fuller puff are deferred; the version is 0.5.1 (a patch, not the 0.6.0 earlier notes suggested). Still open: the forearm is a little thicker than the pack's (about 0.21 H against 0.16 H), the elbow rounder, and a small hook where the inner stroke starts at the armpit.
- **Seen, not fixed**: the open hand is large against the arm in some poses (it keeps the relaxed hand's scale); the open palm's lines are faint at this size; there is no soft-finish shading on the hands.

## Later: polish the emotions again

Noted 2026-10-20 at the owner's request, after step 2. The seven emotions work and differ, but they are subtler than the AI pack's, and the owner wants a second polish pass later. Candidates, in the order
the comparison (`out/franzi-frames/step2-ours-vs-pack.png`) suggested (the eye fields are done): a round open mouth for surprised; stronger brows and narrower eyes
for angry; lowered eyes for shy; a soft-finish gradient for the blush; the brow's own height for surprised (the companion sends only a tilt); comparing each face against the pack's with the aligned head overlay
once the pack's head mapping is built; a tighter close-up crop on the companion's side. Do it after the arms and gestures work, so the emotions are judged as they will be seen, together.

## Decisions needed from the owner

On 2026-10-20 the owner said to use the recommendations. Taken as recommended: 1 (straight swing first, but see the bikini pack's cheer-1 above, which may reopen it), 2, 4 (done: the mouth and
eye fields draw, their web controls wait, see Progress), 5, 7. No recommendation was stated for 3 (blush), 6 (the frame) or 8 (the release). **3 is taken** (blush relative to the default, see Progress); 6 is still open and now has measured numbers (D) and includes the close-up crop; 8 at the end. **1 and 2 are built as recommended** (straight swing; the blouse follows, a coat or a robe keeps the arms down), and the bikini pack's wave and cheer-1 are the argument to reopen 1.

1. Arm contract: straight swing on the existing fields first (built), then elbow fields (built 2026-10-20 at the owner's request, see Progress): the pack's wave has a bent elbow and its cheer-1 pumps both fists, which a straight swing cannot draw.
2. Gesture scope: dirndl, blouse and bare arms, other garments keep the arms down (recommended, built), or support the coat and robe as well (B4).
3. Blush: set her preset to 0, or draw the adult blush relative to the default (A, the catch on blush).
4. Whether the adult face honours `eye_size`, `iris_size`, `eye_tilt` and `mouth_width` (the web tool then offers them for her), or stays with
   the other fields. Recommended: yes, modestly, so `surprised`, `angry` and `thinking` read as the companion intends.
5. `thinking`: face only, as the companion defines it (recommended), or also the hand at the chin later.
6. The frame for raised arms (D): the second frame of each gesture is cut off by 15 to 22 units at the top. A view box from about y -30 for these frames, the posed figure's bounding box returned by the frames request, or the swing kept at or below about 135 degrees.
7. The companion's cheer is symmetric; the AI pack's second cheer is a flex. Keep the companion's.
8. A release (0.6.0) after step 5, and who bumps the companion's pin.

## Not verified

The pack's pictures were looked at on contact sheets, not at full size, so the table of what changes is a reading of the overall look. The pack's head mapping is not built. The companion's tests were not
read, and nothing was tried on the companion's side (its pose override with `grip_style`, its view boxes, its pack maker). The raised arms were not opened in a browser. The body gate (IoU at least 0.93) was not
rerun: it measures the hanging figure, which is byte for byte unchanged.
