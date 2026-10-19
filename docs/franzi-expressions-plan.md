# Franzi's emotions and gestures, for the companion

Written 2026-10-20, after the adult-body campaign (v0.5.0). State: steps 0 and 1 done (see Progress), the rest planned. The record of the earlier campaign is
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

### D. The frame (a risk, estimated, not yet measured)

Her head top is at about y 25 of 500 (`head_cy` 61.4, `head_r` 35.9) and her shoulders at y 117. The reference measurements put the hands
about 2.6 head heights below the chin when hanging, which makes the arm about 167 units long from the shoulder (an estimate from
`ref/franzi/README.md`, not read off our render). At 125 degrees a fingertip would then be near y 21, inside the canvas; at 150 degrees
near y -28, and at 152 near y -30, outside it. If that holds, the second frame of both gestures is cut off at the top of both the full-body
and the close-up view box, and the companion's AI pack (framed with the fists inside the picture) does not have the problem. Options: raise the
companion's constants for her, or let the frames request return the posed figure's bounding box, or keep the swing at or below about 135
degrees. A test should assert that no pose frame's ink leaves the view box, whatever is chosen. Decision 6.

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
2. **The rest of the face** (A3 to A5): the seven emotions. Owner checks each against the AI pack's picture.
3. **Hands** (B2): the open palm and the fist.
4. **Arms** (B1, B3 to B5): split, prove the hanging case unchanged, then bare arms, the blouse, the dirndl.
5. **Wave and cheer** (C, D): wire the contract, settle the frame, the no-clipping test.
6. **Companion** (E) and a release, if the owner says release.

Rules that still bind: SFW (an open mouth is fine, nothing anatomical), flat colour with a second tone only on small elements, no new field
without the owner's say, the age floor, the adult parts replace the shared ones only on an adult body so no other character's output moves.

## Progress

**Steps 0 and 1 done 2026-10-20** (uncommitted, in the `dev` worktree):

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

**`mouth_width` stays hidden in the web tool.** It now draws on her, but showing the control changes the catalogue's recorded fixture, so it sits in `BODY_HIDDEN_EXTRA`
(`catalogue-tables.ts`) until the owner says. The companion sets the field directly and does not need the control.

## Decisions needed from the owner

On 2026-10-20 the owner said to use the recommendations. Taken as recommended: 1 (straight swing first, but see the bikini pack's cheer-1 above, which may reopen it), 2, 4 (done for
the mouth; the web control waits, see above), 5, 7. No recommendation was stated for 3 (blush), 6 (the frame) or 8 (the release), so they stay open until step 2, step 5 and the
end respectively.

1. Arm contract: straight swing on the existing fields first (recommended), or add elbow fields now (C).
2. Gesture scope: dirndl, blouse and bare arms, other garments keep the arms down (recommended), or support the coat and robe as well (B4).
3. Blush: set her preset to 0, or draw the adult blush relative to the default (A, the catch on blush).
4. Whether the adult face honours `eye_size`, `iris_size`, `eye_tilt` and `mouth_width` (the web tool then offers them for her), or stays with
   the other fields. Recommended: yes, modestly, so `surprised`, `angry` and `thinking` read as the companion intends.
5. `thinking`: face only, as the companion defines it (recommended), or also the hand at the chin later.
6. The frame for raised arms (D): which of the three options.
7. The companion's cheer is symmetric; the AI pack's second cheer is a flex. Keep the companion's.
8. A release (0.6.0) after step 5, and who bumps the companion's pin.

## Not verified

The pack's pictures were looked at on contact sheets, not at full size, so the table of what changes is a reading of the overall look. The
arm length, and so the clipping in D, is an estimate. The pack's head mapping is not built. The companion's tests were not read.
