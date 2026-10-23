# Risa polish: closing the gap to her reference

Started 2026-10-24 at the owner's request. Risa is on the adult woman's body in her school uniform (`docs/risa-adult-plan.md`, released in 0.6.0). She reads close to
`ref/risa-adult/`, but there are gaps: a body that is too broad, and a polish the flat style and the soft finish do not reach. This plan is the campaign to close them, one
stage at a time, each measured against the reference before the owner judges it by eye. The references are guides: a number that differs is a lead, and the pick is by eye.

## Owner's decisions (2026-10-24)

1. **The bikini image (`00`) is canon for her body's proportions.** The uniform images (`01` to `07`) draw her about 6% narrower and with legs 20 to 25% shorter below the knee
   when registered by the irises. That is Grok's drift between edits, not her body, and is not a target.
2. **A new field for the body's proportions is acceptable**, though it moves the recorded fixtures of every character: only Risa's drawing may change, every other character's
   (Franzi is the only other adult woman) stays byte-identical.
3. **Below mid-thigh, where `00` shows nothing,** Risa gets Franzi's knees, calves and lengths, her own thighs tapering into them.
4. **Line work** may go in the flat finish or the soft one: an experiment, both are acceptable.
5. **Shading stays after the base.** The soft finish may grow to shading and more polish, but only once the body, the uniform, the hair's drape, the lines and the eyes are
   right (stages 1 to 7); stage 8 is an option then, not a commitment now.

## The gap analysis (2026-10-24)

Our render and the reference on the bikini's grid (head height 352 px, the chin and the centre line matched, `compare_head.py`'s mapping), made by
`harness/risa_adult/gap_strips.py` (strips in `out/gap/`) and `harness/risa_adult/gap_widths.py` (the numbers).

**Measured, against `00`** (the body is the skin and bikini pixels, the hair left out; rows in head heights H below the chin):

| where | rows | ours against the reference |
|---|---|---|
| outer extent, arm to arm | 0.4 to 2.4 | 6 to 9% wider |
| the torso just under the bust | 1.0 to 1.2 | 13 to 15% wider (269 against 234 px at 1.0) |
| the waist | 1.4 to 1.6 | the same (255 to 319 against 258 to 318) |
| each arm | 1.0 to 1.6 | the same or a little thinner (63 to 70 against 65 to 75 px) |
| each thigh | 2.5 to 3.0 | 15 to 21% wider (175 against 149 px at 2.6) |
| the briefs' top, the crotch | | 0.06 H and 0.10 H lower (`body_landmarks.py`: rows 1041 and 1226 against 1019 and 1189) |

So the body is not uniformly broad: the thighs, the ribcage under the bust and the torso's length are off. The bikini image ends at mid-thigh, so below about 3.1 H there is no
canon.

**Corrected by stage 1's gate (2026-10-24):** this first pass counted skin and bikini pixels by colour, which left out our heavy black outline (about 6 px a run on this
grid) and kept the reference's thin one, so it under-measured ours. The arms are not the right size: the gate, which measures both silhouettes to the ink's outer edge, finds
the forearms 17 to 27% thick and the thighs 24 to 30% wide. Its numbers (stage 1, below) replace the table above.

**Seen, not measured:**

- **The hair's drape.** In the uniform images, locks fall in front of both shoulders and down onto the blazer; ours all hang behind the body, so the blazer's shoulders show as
  one square block. This is probably a large part of why she reads broad in the uniform (an inference, to be checked by stage 4's render).
- **Line work.** Our outline is a heavy black stroke, about three times the reference's, and the hair's strand lines are ink black. The reference draws thin lines in a dark
  tone of what they bound (dark red in the hair, brown on the skin).
- **The hair.** The reference has a sheen band across the crown, lit strands and a brighter crimson (its median `#7b232d`; the preset's `#6b1f2a` is the owner's pick, a prior
  decision). Her cut has no soft-finish clumps (`locks: []`, `ts/src/body-adult-cuts.ts`), so the soft finish adds nothing to her hair.
- **The eyes.** The reference's iris has several tones (a yellow lower half), large catchlights and a heavier upper lash; the two eyes differ (already listed as not done in
  `docs/risa-adult-plan.md`, "Eyelids, first pass").
- **Shading.** The reference has cel shadows on the skin (under the chin, under the bust, the knees, the inner thighs) and on the cloth (the blazer's folds and lapels, a strip
  beside each pleat). We draw none: flat is the house style, and the soft finish covers only the iris, the blush, the fringe's shadow and the hair clumps.
- **Hands and knees.** The reference's fingers are separate and relaxed and its knees and calves are shaped; ours are simpler.

## Invariants

- **Franzi and every other character stay byte-identical** at every stage. A new control defaults to Franzi's drawing; a new piece defaults to nothing.
- **Risa's own goldens move on purpose**, stage by stage, with the owner's say: `ref-out/risa.*` through `./refresh-ref-out.sh`, the recorded fixtures that hold her through a
  `harness/ts_port/golden-updates-*/` updater with a README, as `golden-updates-risa-adult/` did.
- **Flat stays the house style.** Shading planes are only ever inside `finish = "soft"`, and widening the soft finish to skin and cloth is the owner's decision (stage 8), judged by
  blind pairs as `docs/soft-hair-plan.md` describes.
- **The companion keeps working.** Her poses (`body-adult-pose-arm.ts`) read the same body tables, so every body stage is checked in the hanging pose and the companion's
  gestures (wave, cheer, folded arm), as the poses in the uniform were.
- **Gates after every stage** (G1): `npm run typecheck`, `npm test`, `./refresh-ref-out.sh --check`, `./refresh-catalogue.sh --check`, `./refresh-bases.sh --check`.

## Stages

The body comes first, because everything else sits on it: the garments are built from its tables and the hair's drape lies over its shoulders.

### Stage 1: Risa's target and gate

A silhouette target from `00` (`segments/00-bikini/anime-girl.png` less the hair layer, neck down to mid-thigh) and a gate in the manner of `harness/franzi/gate.py`: IoU,
widths at the landmark rows (shoulder, under-bust, waist, hip, thigh) within 5%, the landmark heights (waist, the briefs' top, the crotch) within 0.05 H. Unlike Franzi's gate
it registers by the head, not chin to sole, because the image ends at mid-thigh. Run on today's Risa first and record the numbers: the prediction is a fail at the under-bust
and the thighs and on the crotch's height, a pass at the waist. No shape changes in this stage.

**Done 2026-10-24.** Three harness scripts, nothing in `ts/src/` changed:

| script | what |
|---|---|
| `harness/risa_adult/target.py` | the target: `00`'s cutout less the hair layer, from the neck's top (0.12 H) down, strand gaps filled (only holes up to 1500 px, so the arm gaps stay open), and an **unknown zone** where the hair layer cannot say whether a strand is in front of the body: above the bikini band, hair inside the body's span (the locks lying in front of both shoulders, from beside the neck down the bust's sides), and below it only the narrow bites a strand makes in an edge. `target-check.png` shows both over the reference |
| `harness/risa_adult/body_outline.ts` | our body alone: `adultBodyPath` filled and inked black, with `risa.ts`'s parameters and overrides, so no hair or detail lies over it (checked: its leg runs at 2.6 to 3.0 H are the full render's to the pixel) |
| `harness/risa_adult/gate.py` | the gate: head-registered (`compare_head.py`'s mapping), ours shifted sideways onto the target's body centre (the reference's body is centred 8 px right of the head's centre line: her head is turned, ours was made straight), the unknown zone counted neither way. IoU at least 0.93; the outer extent and the centre run (the torso, or each leg) within 5% every 0.1 H from 0.3 to 3.0 H; the waist, hip and crotch heights within 0.05 H. Franzi's thresholds. The arms are printed, not gated. `--self` passes (IoU 1.000), `--self --stretch 1.08` fails (IoU 0.834, worst width +8.6%) |

**Today's Risa** (`./harness/run.sh harness/risa_adult/gate.py --verbose`): **FAIL**, IoU **0.821**.

| where | rows (H below the chin) | ours against the target |
|---|---|---|
| outer extent, shoulders to hips | 0.3 to 2.4 | +6 to +11% |
| outer extent, the thighs | 2.5 to 3.0 | +19 to +20% |
| the torso under the bust | 1.0 to 1.2 | +18 to +20% (281 against 236 px at 1.0) |
| the torso at 1.4 | 1.4 | +3% |
| the hips | 1.7 to 2.1 | +5 to +10% |
| the upper arm | 1.2 to 1.5 | +3 to +8% |
| the forearm | 1.6 to 2.0 | +17 to +27% |
| each leg | 2.3 to 3.0 | +12% at the top, growing to +30% at 2.9 |
| the waist's height (target 1.18) | | +0.077 H (lower) |
| the hip's height (target 2.06) | | +0.094 H |
| the crotch's height (target 2.14) | | +0.065 H |

Against the prediction: the under-bust, the thighs and the crotch fail as predicted. The waist's width passes where the two waists meet in width (1.4 H, +3%), but its
height does not: ours narrows lowest at about 1.26 H against the target's 1.18, so the whole torso from the waist down sits 0.07 to 0.09 H low, and the 1.0 to 1.2 H rows
compare our ribcage with her waist. That makes stage 2's work, in order of size: the thighs and the forearms (about a quarter too wide), the ribcage under the bust (a fifth),
the torso's length (the waist, hips and crotch 0.07 to 0.09 H higher), then the outer extent, which should mostly follow from the arms and the ribcage.

### Stage 2: a body that can take Risa's proportions

The adult body's outline is half-width tables by depth (`SHOULDER_OUTER`, `ARM_OUTER`, `ARM_INNER`, `TORSO_SIDE`, `LEG_OUTER`, `LEG_INNER` in `ts/src/body-adult-data.ts`,
and `RIB_KNOTS`), imported as module constants by five modules (`body-adult-parts.ts`, `-shirt.ts`, `-blazer.ts`, `-garments.ts`, `-pose-arm.ts`). The work:

1. The tables come from the character, not the module: one function (`adultTables(sk)`) that returns Franzi's tables unchanged by default, used by all five. A refactor
   with no change of output, proved by the byte-identical checks before anything else moves.
2. A body profile that warps them, separately per region rather than one scale (a single scale would also thin the arms, which are already right): the ribcage under the bust,
   the hips and thighs, how far the arms hang from the torso, and the torso's length (the rows of the briefs and the crotch). The traced chains that sit on the body (the
   briefs `ADULT_BOTTOM`, the top `ADULT_TOP`, the bust, the hands' placement) go through the same map, as `bustWarp` does for the bust.
3. Fit Risa's profile to the target until the gate of stage 1 passes, then judge by eye.

The profile is a new field (decision 2), neutral by default so Franzi draws as before; the recorded fixtures of every character take the field's default through an updater
in `harness/ts_port/golden-updates-*/`, as the elbow fields did. Below mid-thigh the legs are Franzi's (decision 3).

### Stage 3: refit the uniform on the new body

The shirt's torso and sleeves and the blazer are built from the tables and should follow; what is traced is placed by landmarks and needs a check: the pleated skirt's
silhouette and hem (`body-adult-skirt-pleated-data.ts`, through `registration.py`'s `to_body`), the shirt's hem and collar, the blazer's pockets and darts (fractions of the
half-width, so they follow), the socks and the loafers. `blazer_outline_check.py` against `01`; the width the blazer should reach is the new body's plus its ease, not the
drifted `01`'s. Then the poses.

### Stage 4: the hair in front of the shoulders

Front locks over the shoulders and the chest, traced from `01`'s `red-hair` layer where it covers the blazer (registered, `registration.py`), drawn as a part over the garments,
behind the arms where they cross. Checked on the raised and folded arms, where a lock over a moving arm would read wrong (the likely answer: the locks stay on the chest and the
arm passes in front). The bikini drawing gets the same locks where `00` shows them.

### Stage 5: line work

Thinner lines in a dark tone of what they bound, for Risa: the outline, the hair's silhouette and strands. Her cut already carries its own face stroke (0.45), so per-cut line
settings are the pattern. Flat or soft is an experiment (decision 4): try both and pick by eye.

### Stage 6: the hair under the soft finish

Clumps for `long_straight_fringed` (its `locks` list is empty), and a sheen band across the crown, inside the hair's silhouette, scaled by `highlight_strength`. Blind pairs.

### Stage 7: the eyes

Per-eye lids, wings and lashes traced as the brows were (`harness/risa_adult/brows.py`), the inner corner's flick, and the iris's lower half in a second tone (flat) or graded
(soft). The two eyes may differ in shape while their placement stays the levelled one (`body-adult-cut-level.ts`).

### Stage 8: cel shading, after the base is right

Hard-edged shadow shapes, one tone each, under `finish = "soft"` only: on the skin (under the chin, under the bust, the knees, the inner thighs) and on the cloth (the blazer's
folds and lapels, the strip beside each pleat, of which the skirt's trace found three of ten). The owner allows the soft finish to grow this way (decision 5), once stages 1 to 7
are done; it is judged by blind pairs, and `CLAUDE.md`'s rule for the soft finish is updated with it.

### Stage 9 (optional): hands and knees

Relaxed fingers and a shaped knee and calf. Lower priority than the rest; the hands are traced data shared with Franzi, so a Risa-only change is a second hand set.

## Open questions for the owner

None at present: the four the first draft listed are decisions 2 to 5 above.
