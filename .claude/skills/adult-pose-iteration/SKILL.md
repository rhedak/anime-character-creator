---
name: adult-pose-iteration
description: Change or extend how the adult woman (Franzi, the adult_female body) is drawn when posed, such as raised or bent arms, sleeves and bodice that follow an arm, expressions, or any new parameter that moves her drawing. Use for any fix to a posed figure the owner reports by screenshot ("cut off", "creepy", "notch", "residual", "gap"). Gives the render-compare-fix loop, the byte-identity rules, the arm geometry's moving parts and the mistakes of the 0.5.1 campaign. Not for the chibi build or for tracing a new part from a reference (that is trace-reference).
---

# Adult pose iteration

The method that took Franzi from "ignores every arm and expression field" to blink, mouths, wave and cheer
(creator 0.5.0 to 0.5.1, 2026-10-20 and 21). The record is `docs/franzi-expressions-plan.md`; this file is the
distilled how, so the next posed-figure change does not re-learn it.

## The loop, one defect per round

1. **Render the defect and its neighbours before touching code.** `posefig.sh`, beside this file, renders named
   override sets side by side (see its header; `DRESS=1` puts her in the dirndl, otherwise she is in her
   underwear alone, which is where an arm's own shape shows). Always include the angles that bracket the problem:
   hanging (0), 6 (the least that is drawn on its own), 20, 45, 90, 125, 150, plus the elbow values the companion
   sends (wave: arm 6 with elbow 148 and 155; cheer: arm 16 with elbow 148 and a fist, then arm 150 straight). The
   default view reaches above the 400x500 canvas on purpose, so a hand that leaves the frame shows against black.
   Zoom to the region with a tight viewBox (third argument) and enlarge it; a defect of a few units is invisible
   in the full figure.
2. **Read the owner's marks literally, and say back what you see.** They draw red lines on a screenshot. One
   misreading cost a whole pass: "extend the outline of the upper arm" meant the part with the hand attached
   (the forearm), not the part attached to the shoulder. Before building, name the two or three candidate
   readings in a line and pick one, or ask when the cost of the wrong one is a rebuild.
3. **One fix per round, then show it.** Render the same pose set before and after, look at it yourself (zoom in,
   check the hanging and the other side are unchanged), and only then show the owner. They approve each round
   and ask for the commit in words ("commit to dev as one line, no trailer"); never commit unasked.
4. **Each defect gets a test in the same change** (`ts/test/adult-pose.test.ts`): a count of ids or strokes, a
   geometric relation (the ink starts where the body line crosses the edge, the cap stays inside the body
   silhouette), never a hash of the new drawing. A test that pins a number you just tuned only repeats the tuning.
5. **Keep a deferred list.** Owner decisions of the form "fine as is" or "defer" go into the plan doc and the
   memory the same day, so a later pass does not reopen them.

## Rules that decide what you may change

- **Her hanging drawing must stay byte-identical.** The baseline test hashes it; a raised arm touches only sides
  with a raised arm (`raisedSides`), and below 6 degrees with no elbow the arm hangs in the body's one outline.
  New geometry goes behind the pose, never into the default path.
- **Recorded fixtures change only by mechanical rules** the owner has seen
  (`harness/ts_port/golden-updates-*/README.md`). A field that is new to the registry needs the same treatment
  (the elbow fields did). Never edit a fixture to turn a failure green.
- **References are guides, not targets, and none below the chin unless it is our body.** The companion's AI packs
  (`anime_ai_companion/packs/franzi-dress`, `anime_ai_companion-packs/packs-src/franzi-bikini`) give the idea of
  a raised arm; the bikini pack decides the arm's shape, and the dirndl follows the arm, so fix the bikini first.
- **A shape traced from the hanging pose does not hold in another pose.** The dirndl sleeve traced from lowered
  arms looked cut off when raised. Compare against a reference in the target pose, or mirror the visible side
  (the sleeve's inner edge is the outer contour reflected across the arm's axis, capped by the seam).
- **When filling a gap, follow the curves already traced, not a straight line.** The first bodice fill ran straight
  and stuck out past the apron; the owner's correction was "match the apron's width and keep the body curves".
  Take the knots from the traced outline (`BODICE_FILL`, `RIB_KNOTS`).

## How the arm is built (`ts/src/body-adult-pose-arm.ts`, `body-adult-pose.ts`)

- A raised arm is the hanging arm drawn separately and turned by SVG `rotate` about a pivot: the outer tip under
  30 degrees, blending to the middle of the chord by 50 (`toTip`, `PIVOT_BLEND`). A bent arm is drawn in the
  forearm's frame with `rotate(upperTurn) rotate(elbow)`; the outer crease is cut where the two edges' polylines
  cross (K=48 dense points). `ARM_ELBOW_MAX` is 155 because past it the crease no longer lies inside the forearm.
- The body outline is one fused path. The raised side's shoulder stops at knot d=0.4 (`RAISED_SHOULDER_D`),
  a knot of the shoulder table, because a point between knots made the curve wobble. Phantom neighbour knots keep
  the body's side smooth where the arm leaves it (`adultBodyPath`).
- Skin is the `-fill` path plus the `-hand-edge` path, each filled; strokes are drawn in bands (`strokeBands`)
  with butt caps. `startOf` finds where the body line crosses each arm edge, and ink begins there, so the
  outline of the arm continues the outline of the body instead of restarting.
- The bikini top's breast bulge past the arm's cut is `RIB_KNOTS` following the cup's outer edge: if the breast
  side turns to a straight cut with a raised arm, look there first.
- Dirndl: blouse split into body piece, sleeve proper (from `SLEEVE_TOP`) and a cap cloth clipped to the body
  silhouette in the turned frame (`armTurnBack`); the sleeve rim is inked from `RIM_FROM` (105 degrees); the body
  piece is cut along the bodice's outer edge (`BODICE_SIDE_FROM` to `TO`); on raised sides the bodice is filled
  out along `BODICE_FILL` and inked. The white residuals and notches the owner saw beside the bodice were
  closed by that cut and fill, so look there first for the next one.

## Mistakes made once, so they are not made twice

- **Round stroke caps at a crossing leave ticks.** Use butt caps and start the armpit ink a little past the
  crossing (`advance`, 1.2 times the half stroke).
- **Removing ink to hide a hairline also removed the armpit's ink.** Cover the hidden link with skin (the `link`
  patch) instead of skipping its stroke.
- **A faint hairline at 6 and 20 degrees is still open** (deferred by the owner; the cause was not found). Do not
  assume its cause when you reopen it: render the pose, then bisect which layer draws it.
- **Corner problems at the shoulder** want a rounded corner built from a skin patch, a cover stroke slightly
  wider than the line (width + 0.3) and an inked quadratic (`shoulderCorner`), not a bigger arc radius.
- **Frames that leave the canvas** are the companion's to fix with a wider view (`gestureView`), not the
  creator's to squeeze; the owner accepted the fingertip clipping of wave 152 and cheer-2 150 as is.

## Done means

`cd ts && npm run typecheck && npm test`, then at the root `./refresh-ref-out.sh --check`,
`./refresh-catalogue.sh --check` and `./refresh-bases.sh --check`, with the hanging baseline test unchanged.
Releasing and the companion's side are in `creator-release-to-companion`.
