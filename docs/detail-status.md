# Detail status

The record for `detail-plan.md`. Procedure: `detail-strategy.md`.

## RESUME

D0 to D5 done. Next is **D6, garment line work**. **D5, the hair**, for the
record: after the study on `long_traced` and two traces of realistic
references (2026-09-29, below), an audit (2026-10-03, below) found why the
traces did not work: both references draw the hair on a
realistic body, and below the chin that hair's shape is mostly the body's, so
no mapping puts it on ours (three were tried). The owner's call: get the
hairstyle drawn again on the tall-chibi body (`katherina_grok` with only the
hair changed, the prompt is in the plan below), check it with
`harness/hair_audit/gate.py` before tracing anything, then trace it the way
`long_traced` was and build it as a new hairstyle on the `Hairstyle` contract,
which is what carries a cut to the other presets. The reference
(`ref-local/katherina_grok_nohat/`) passed, was traced and built as
`long_parted`, its tips reworked (findings), and Katherina (no side tail) and
Reika wear it; everyone else keeps their cut. The step list is **D5 plan
(2026-10-03)** below; the 2026-09-29 todo it replaced is kept after it as a
record. Open, all the owner's to decide later: a hair clip for Katherina where
the tail's band was (deferred, the owner, 2026-10-03); which presets take which `hand_style` (all "mitten", the owner's
call on 2026-09-27 until the traced hands get another pass); a relaxed hand pose of its own; the chin and the
lid crease (deferred); `../valley_of_mist` not regenerated since the detail
pass began (the owner: not for now; the Everglow and Katherina covers were,
before Katherina's new hair, so they show her old cut and tail).
Tools: the baseline `harness/detail/baseline.py`, the byte guard
`harness/tall_chibi/snapshot.py` (take the before from the committed tree with
`git stash`), and restage the web tool (`./web-stage.sh`) after any preset or
catalogue change; the local server may still be running on port 8000.

## Scoreboard

| step | state |
|---|---|
| D0 inventory and baseline | done |
| D1 line weights | done |
| D2 eyes | done |
| D3 face maturity | done |
| D4 body at height | done (the hands good enough for now; another pass deferred) |
| D5 hair | done: `long_parted`, traced off a tall-chibi reference, worn by Katherina and Reika (2026-10-03) |
| D6 garment line work | not started |

## D5 plan (2026-10-03)

The audit's recommendation (findings, below), the owner's call. The reference
is drawn on our body so that nothing below the chin has to be mapped, and the
`Hairstyle` contract, not the trace, is what makes the cut work on the other
presets: `long_traced` serves seven of them at `hair_length` 0.16 to 0.95 that
way.

- [x] 0. The target, pinned: a centre parting; the fringe parted into pointed
  locks sweeping off it toward the temples; a curtain each side over the face
  down to the jaw; one lock each side forward over the shoulder, about 0.36
  head radii wide, ending in a point above the belt; the rest behind the
  shoulders and arms, ending in pointed tips; the underside behind the neck a
  darker tone (the owner's call, 2026-09-29). The fall narrow and straight, as
  on `katherina_grok_real`: on a chibi body the hair falls free, so the
  hair-only reference's flare was its arms; a flare can be a knob later.
- [x] 1. The owner generates the reference: `katherina_grok.jpg` edited with
  the prompt below, a few candidates, one picked by eye for the style. Then the
  hair cut out with the tool that made `katherina_grok_real/segments/`
  (`harness/trace_hair/locate.py` found those exact pixel cuts; check the new
  one the same way). Saved under `ref-local/katherina_hair_chibi/`.
  **First image** (2026-10-03, `ref-local/katherina_grok_real_nohat/`): made
  from `katherina_grok_real`, not `katherina_grok`, so the realistic body with
  the hat and bat removed. Fails the check: soles 14.88 against 5.94, hem 8.98
  against 4.23, the head scales 12% apart. Not traced below the jaw; kept as
  the head's source for the fallback, since its crown and right side are no
  longer hidden. **Second image** (2026-10-03, `ref-local/katherina_grok_nohat/`,
  made from `katherina_grok`): the one taken forward. Grok also dropped the
  staff and drew small ears, neither of which touches the hair. Its
  `segments/` are exact cuts (`harness/hair_audit/segments.py`: the hair's mean
  colour difference 0.31, none over 20; jacket, dress and collar likewise).
- [x] 2. The check, before any tracing:
  `./harness/run.sh harness/hair_audit/gate.py PATH`. The two head scales
  within 5%, the skirt hem, soles and skirt width within 0.1 head radii of
  `katherina_grok`'s, by the same code. A failure means regenerate, not map.
  **`katherina_grok_nohat` passes:** soles +0.062, hem +0.039, skirt
  half-width +0.007, the head scales 1.0% apart; its eye band lies on
  `katherina_grok`'s 2 px off (0.012 head radii, correlation 0.945). The first
  run read the scales 18% apart, which was the check, not the head: the face
  is at full width for some fifty rows, so "the widest row" moved 49 rows on a
  one-pixel difference. The vertical scale is now the jaw's run, from the
  lowest row at 90% of the face's width to the chin, and both controls still
  hold. Placed on our figures by that calibration alone
  (`harness/hair_audit/preview_ref.py`), the hair sits on Katherina at 0.8, 1.0
  and 1.3 and on Satoko and Linnea with no cape and no pinch, ending near the
  belt at 1.0, below it at 0.8 and above it at 1.3, which is `_hair_fall`'s to
  even out. **What it shows against the target:** the parting, the fringe locks
  and their V of forehead, the curtains, a narrow straight fall and pointed
  tips, flat colour. A second tone at 0.6 of the main one (the owner's 0.65)
  marks what lies behind: the wedges behind the neck and the back hair seen
  between the front locks and the arm. The front layer is lighter locks over
  each shoulder and down the jacket to about the belt. Read by eye as 0.5 to
  0.7 head radii wide; measured row by row in step 3 it is about 0.27 at the
  shoulder, narrowing to its point, near `katherina_grok_real`'s 0.36. The
  owner took it as the style.
- [x] 3. Trace with the trace-reference skill: the mass, the hairline (the face
  opening, the curtains and each front lock's inner edge) and the tip edge;
  0.012 to 0.018 head radii; no edge under two stroke widths (the crop's rule);
  no holes or islands; the constants emitted by a script.
  **Done** (`harness/hair_parted/`). `regions.py` splits the exact hair segment
  by tone (line under 18, dark 18 to 32, light above) into the mass (each row
  filled between the innermost hair either side, holes filled), the front and
  the outer falls. The line between each front lock and its outer fall starts
  inside the hair beside the temple, at (-1.113, -0.198) and (1.113, -0.221),
  so a seam straight out from there to the silhouette cuts the front from the
  outer fall above it. `trace.py` walks each region, cuts it at the named
  points and fits at 0.012, then drops marks until no segment is under 0.0854
  (two strokes; `_stroke_w` is 0.0427 head radii at every height): the mass 46
  segments, the hairline 30, the lock edges 10 and 6, the outer falls' inner
  edges 4 and 3. Each inner edge starts where the dark strip is 0.08 across
  (at 1.11 and 0.94); above that it is a sliver about 0.04 wide, and two lines
  that close draw as one heavy one. Overlaid on the reference
  (`overlay*.png`) every chain rides its line. Two corrections on the way: the
  segment's alpha takes in only about a pixel of the outline, so the mass is
  moved a pixel out, not half a line in; and the reference's ear, a hole
  beside the left lock edge at 0.14 to 0.43, first passed for the strip's top.
  `emit.py --write` puts the block between markers in `character.py`.
- [x] 4. A new `Hairstyle` (say `long_parted`), `long_traced` untouched so every
  other preset stays byte-identical: above `_HAIR_CHEEK_Y` pinned to the skull,
  below it y a fraction of `_hair_fall` and x as traced (`_long_scaled`'s
  rule); the front locks through the hairline and `_hair_front`; the underside
  a `shade()` patch behind the neck; pale tips through `tip_edge`; no strand
  lines. **Done:** `long_parted`, labelled "Long, front locks". Its mass
  closes behind the body as `long_traced`'s does; the hairline's closing edge
  runs up the right lock's edge, out along the seam, over the crown on the
  mass's own segments and back down the left, so the front cannot paint past
  the mass; `fall_edge` strokes the lock edges and the silhouette above the
  seams. `Hairstyle` has a new optional `underside`: a region of the mass
  painted `shade(hair, 0.65)` (`_HAIR_UNDERSIDE_VALUE`), its tip tone likewise,
  and the lines bounding it where it shows, each outer fall's inner edge, led
  in from one anchor up the lock's edge so it splits off that line. The region
  runs up the lock edges and along the seams lifted 0.03 into the front, so
  where it is not a drawn line it is under the front, the head or the body.
  `_long_traced_tip_edge`'s construction moved into `_lifted_tip_edge`,
  unchanged, for both cuts. Every existing render byte-identical
  (`./refresh-ref-out.sh --check`); `ref-out/catalogue.json` refreshed for the
  new option and the web tool restaged.
- [x] 5. Verify, each prediction written first: the outer edge within 0.2 head
  radii of the reference's at matched heights (`proportions.py`); every
  `long_traced` preset switched over in a harness at its own `hair_length`, at
  heights 0.8, 1.0 and 1.3, with and without hats (Katherina's, Chiyo's
  scarf), Satoko's pale tips, a blonde and a near-black palette, the insert
  size; `ruff check`, `ruff format`, `pytest`, `./refresh-ref-out.sh --check`.
  **Done** (`harness/hair_parted/compare.py`, groups `katherina`, `cast`,
  `heights`, `palettes`, `small`). The outer edge, rendered through
  `_hair_mass` at the trace's own length, lies a median 0.02 outside the
  segment's (most 0.036): the stroke's outer half and the pixel the mass was
  moved out, against the 0.2 predicted. On Katherina it reads as the
  reference: the taller crown, the parted fringe and its V, the curtains, a
  lock each side over the shoulder to points above the belt, the outer falls
  behind the arms, the darker hair by the neck and in the strip; at 4x the
  seam does not show and the inner edges leave the lock lines cleanly. Heights
  0.8 to 1.3 hold, the locks ending above the belt at each. Every `long_traced`
  wearer at its own `hair_length` takes it; at Chiyo's 0.16 the fall squeezes
  into a short fan of points under her scarf. Blonde and near black work (on
  near black the underside and lines barely show, as every line on dark hair
  does). Satoko's tips turn at about eye height, level across the curtains,
  higher than on `long_traced` because the tone turns at half the hair's height
  and this crown is taller. The insert size reads at 1x; on the cast sheet
  every crown is whole. The tightest headroom, Katherina hat-less at 1.3, is
  5.9 px. Two things the cut does not do but show with it: Katherina's
  `hair_tail` still hangs on the right, and her raised staff arm uncovers more
  of the dark hair behind than the reference's lowered arms. 552 tests pass.
- [x] 6. The owner picks which presets wear it; then the docs (this file, the
  plan's D5, `CLAUDE.md`'s note on the reference exceptions). **Katherina and
  Reika** (the owner, 2026-10-03), Katherina without her side tail; the rest
  keep theirs. `./refresh-ref-out.sh` moved exactly four renders: the two of
  them and the two cast sheets they are on. A clip in place of the tail's band
  is deferred.

**Fallback**, if two or three generations fail the check or lose the style:
D5's traced head part (it fits within 0.1 to 0.2 head radii), the chibi fall
below it, and the front lock designed on body landmarks (the old todo's steps
8 to 10).

**The prompt**, for grok's image edit with `katherina_grok.jpg` as the input:

> Edit this image. Keep everything exactly the same except the hair and the
> hat: the same character, the same chibi proportions, face, pose, outfit,
> hands and staff, the same thick black outlines and flat colours, the same
> framing and the same plain black background.
>
> Remove the witch hat completely, so the whole top of her head shows.
>
> Give her this hairstyle, in the same dark purple, drawn flat with no shine
> highlights:
> - a centre parting at the top of the head;
> - the fringe split at the parting into several pointed locks that sweep
>   outward toward the temples, their tips around eyebrow height, with a
>   narrow V of forehead showing under the parting;
> - one side lock on each side of the face, over the cheek, down to the jaw;
> - one long lock on each side that falls forward over the shoulder and down
>   the front of the jacket, ending in a point a little above the belt;
> - all the rest of the hair hangs straight down behind the shoulders and the
>   arms, close to the body and not flaring outward, to just below the belt,
>   ending in several pointed tips;
> - the underside of the hair, seen behind the neck between the side locks,
>   a slightly darker purple.
>
> No hair clip. Only a few dark lines between the locks, no strand texture.

Why no hat, clip or sheen: the last traces had to fill in hair the brim and
the bat hid, the clip's ring was traced as hair, and the sheen's zigzags made
false lines. Our renderer draws its own hat and clip.

## D5 todo (2026-09-29), superseded

Superseded on 2026-10-03 by the plan above (the audit, in the findings, says
why); kept as the record of what was tried. Steps 6 to 19 were not done.

Why: the front locks are a fixed-width pixel band (`shoulders.py`, `LOCK_W`)
that ends in a flat cut, not at the lock's tip. The hair-only reference is a
pear shape about twice the body's width, where `katherina_grok_real`'s hair
hangs narrow and straight, so on our body the flare reads as a spiky fan. Lines
and outline at the reference's weight add to it. Some claw-like tips sit over
the sleeve and hand (unverified: strands flagged front past the kept lock).

Setup
- [x] 1. Find what draws the claw tips over the sleeve and hand
  (`harness/hair_only/diagnose.py`, `out/hair_only/diagnose.png`). **Found:**
  the guess was wrong. The front strands are clipped to the front piece, so
  none runs past the lock. The tips come from the cut itself: the front piece
  is one piece (no holes, x -1.62..1.68, y -1.90..2.49 head radii, the
  shoulder at 1.13) and where `shoulders.py` cuts it, the outline is stroked
  along the cut. That gives (a) a flat horizontal ledge with a spike above it
  at the left shoulder row, (b) each lock ending in a flat stroked bottom edge
  with a thin sliver of the same lock hooking on below it, over the sleeve,
  (c) a stair-stepped outer edge on the lock where the cut follows raster
  pixels, and (d) tips of back strands showing between the arm and the body
  below the sleeve. So step 4's designed lock also has to drop the stroke
  along the cut, and the back tips (d) belong to steps 6 and 9.
- [x] 2. Fix a test set: Katherina at 1.3 with and without the hat, Linnea,
  Satoko, Chiyo, and a hair colour far from purple; compare each against
  `katherina_grok_real` at one scale. `harness/hair_only/compare.py`, groups
  `katherina` (both references, hat, no hat, blonde), `others` (Linnea,
  Satoko, Chiyo, Reika, each at its own height), `full`, `small`.
- [x] 3. One preview command that renders variants side by side:
  `./harness/run.sh harness/hair_only/compare.py today current=out/hair_only/hair.json
  a=out/hair_only/hair_a.json,lw=0.02,min=0.3 [--only GROUP]`. A variant is a
  file in `hair.json`'s schema, so A and B only have to write theirs. Written
  to `out/hair_only/compare_<group>.png`. **Seen on the first run** (today
  against the current trace): the trace on the other presets is far off. The
  fixed flare is about twice their body's width and reaches the sleeves' hands,
  the crown sits above the frame, and under Chiyo's headscarf it shows above
  the cloth. Satoko's pale tips show as hard-edged rectangles: the tip clip is
  laid for today's mass, not the traced one. So the traced hair is fit for
  Katherina only, which is what step 16's separate hairstyle is for, and the
  other presets need B's parametric fall or nothing.

Front locks, both variants
- [x] 4. Replace the fixed band with a designed tapered lock a side
  (`harness/hair_only/locks.py`, writes `out/hair_only/hair_lock.json` and
  `locks.png`; view with `compare.py today current=... lock=out/hair_only/hair_lock.json`).
  The curtain is kept as traced down to our shoulder row (1.13 r). Below it
  each side is a funnel, 0.75 r long, from the curtain's whole cross-section
  (neck side to outermost hair, about 1.2 r wide) easing into one lock 0.38 r
  wide, then narrowing to a point at the belt (`waist_y`), the centre line
  drifting 0.08 r toward the body. The hair wider than the lock goes behind
  the shoulder, carried by the mass. Curtain, funnel and lock are one raster
  union, traced and fitted once: one outline, no stroke along a cut. **Seen**
  (`zoom_lock.png`, `compare_katherina.png`): the ledge, the flat lock
  bottoms, the hooks below them and the stepped edge are gone; each lock ends
  in its own tip at the belt; the traced lines of the curtain stop where the
  funnel ends and each lock has two lines of its own. **Left over**, for
  steps 6 to 12: one short thick tick on the left curtain's outer edge near
  the shoulder, and short stray back-strand lines between the lock and the
  jacket edge (step 12), and the back tips below the sleeves (steps 6, 9).
- [x] 4b. **Step 4 redone from the owner's trace** (2026-09-29). The owner, on
  the funnel: it is one large block, which looks odd; in the reference the
  lock starts near the top and goes down as a single unit (traced in red on a
  screenshot of `katherina_grok_real`), and the back hair is darker and not
  part of it (traced in cyan). `harness/hair_only/owner_trace.py` registers the
  screenshot to the reference (scale 2.83, correlation 0.91; the marks land on
  the reference's lines) and `owner_lock.py` builds `out/hair_only/hair_lock2.json`
  from it: the **front piece** is the traced crown and fringe cut to inside the
  lock's outer edge down to the cheek line, and below it only two strips, each
  between the owner's red lines (0.3 to 0.4 r wide, near the 0.36 measured),
  tip included; the hair outside a strip is the mass behind, so a strip's outer
  edge is drawn as a fine line (interior weight), its inner edge and tip at the
  outline weight. The **dark patch** is a second tone of the hair
  (`shade(hair, 0.65)`, the reference's underside measures about 0.63) on the
  mass, from the lock's inner edge to the centre line, so behind the head, neck
  and jacket, which cover what they cover; only the wedge beside the jaw shows.
  Two things of mine, not the owner's: the tip is drawn pointed, 0.3 r below
  where the owner's slanted end stops (the slant read as a cut-off ribbon), and
  the curtain's face-side edge is eased onto the lock's inner line over 0.35 r
  above the cheek line (a step showed there). **The dark patch is a second tone
  on hair, the owner's call under the flat-colour rule;** it is small and lies
  behind. **Left over:** thick short strokes on the outer hair's edge (slits
  between strands that the trace kept as holes of the mass), the many short
  traced lines on the outer hair (step 12), the back tips below the sleeves and
  the wide flare (steps 6, 9). View: `compare.py today current=... owner=out/hair_only/hair_lock2.json`.
- [x] 5. Check the lock meets the curtain with no seam or step, at several
  heights (`compare.py --only heights`, 0.8, 1.0, 1.15, 1.3). There is no seam
  at any height, since curtain and lock are one outline. **But the length is
  baked for 1.3:** the shoulder row is 1.13 r at every height, the belt is at
  2.16, 2.38, 2.55 and 2.71 r, and the tip is at 2.695, so the lock hangs 0.5,
  0.3, 0.15 and 0 r below the belt. **Katherina's preset has no `height`, so
  it is 1.0:** on her the lock, like the whole fixed-length mass, runs 0.3 r
  past the belt. Either she takes `height=1.3` in her preset (the trace's own
  choice, which the owner asked for), or the fall scales with height, which is
  variant B's parametric fall. With the owner.

Variant A, narrow like `grok_real`
- [ ] 6. An x-squeeze growing from 1.0 at the shoulder to about 0.6 to 0.7 at
  the tips, on mass, lines and lock together.
- [ ] 7. Render and compare; the tips should land near the arms' outer edge.

Variant B, the fuller flare, parametric fall
- [ ] 8. Keep the trace only to the jaw or shoulder (it fitted within 0.1 to
  0.2 head radii there).
- [ ] 9. Generate the fall below as tapered locks, tip lengths and spread from
  the reference's tip distribution, sized from the skeleton and `hair_length`.
- [ ] 10. Back hair behind body and arms by general rules, no per-body trace.

Line work, both variants
- [ ] 11. Line weight between 1.15 and 2.0 px (about 1.6).
- [ ] 12. Drop lines shorter than about 0.3 head radii; clip lines to the mass
  where the arms hide them.
- [ ] 13. Second tone (the darker underside): left out unless the owner asks.

Judge
- [ ] 14. A and B side by side against the reference, at full and insert size,
  with and without the hat; the owner picks.
- [ ] 15. Check the crown for clipping in the real viewBox and the sheet
  layouts, with and without hats.

Emit, the chosen variant only
- [ ] 16. A new hairstyle (say `long_traced_ref`), not a replacement for
  `long_traced`, so other presets stay byte-identical.
- [ ] 17. `hair_length`, the hat, holes (even-odd) and z-order with the locks.
- [ ] 18. `ruff check`, `ruff format`, `pytest`; `./refresh-ref-out.sh` only
  for a deliberate change.
- [ ] 19. Docs: this file's RESUME, the plan's D5 section, and CLAUDE.md's
  note on the reference exceptions. No commit unless asked.

## Findings, newest first

### D5: the parted cut's tips (2026-10-03)

The owner: switch Katherina's side tail off with this cut, and the tips still
look slightly off; then, "the reference has a hairline after the edge", which
makes it look more natural. `harness/hair_parted/tips.py` paints our drawn ink
over the reference in its own frame at each tip (Katherina at the trace's own
length, so nothing is stretched).

- **The shapes were right, the ends were not.** Our lines ride the
  reference's at every tip. But at each tip the reference's two side lines
  meet and run on as one line tapering to nothing, 0.09 to 0.16 head radii past
  where its colour stops (measured on the front locks over the jacket; over the
  black page line and page are one colour). The trace stops with the colour,
  since the segment's alpha takes in only about a pixel of line, and our
  outline closed each tip with its round join: a blunt end. Now
  `Hairstyle.tip_lines` draws that line, from each tip's apex along its
  bisector for `_HAIR_TIP_LINE` (0.12), as wide as the outline at the apex and
  thinning to a point, with the mass for tips behind the body and with the
  front for those over it. `tips_find.py` finds the tips, corners sharper than
  62 degrees pointing out of the hair: the four outer-fall points, each front
  lock's lowest point and the right one's second, and a fringe lock's point on
  the forehead. Over the reference each new line follows the reference's.
- **Short falls squashed the tips into hooks**, which the owner's sheets
  showed as well: the stretch below the cheek line was one linear squash,
  harmless for long straight sides, but a point at 0.56 of its height (Linnea)
  curls outward. Holding the last head radius rigid was tried and was worse:
  the run above it took the whole change, collapsed to a sixth on Linnea, and
  the silhouette stepped out as a shelf. `_parted_q` now ramps the scale from
  strongest at the cheek line to lightest at the tips (the square root of the
  overall scale there), which keeps Linnea's and Satoko's tips upright and
  pointed with no kink. Chiyo's 1.36, barely below the chin, still curls: the
  cut has nowhere to put its locks at that length.
- **Satoko's pale tips** left a sliver of gold down the outside of the left
  outer fall, which widens downward away from the lifted edge; the edge is
  pushed out (`_PARTED_TONE_WIDEN`, 1.15) before it is lifted. The level pale
  line at eye height remains, as noted.
- **The tail.** Katherina's oval on the right of her head was never a clip: it
  is `_hair_tie`, the tail's band, so it goes with the tail. With the owner
  whether to add a clip of its own.

Every existing render byte-identical; 552 tests pass.

### D5: `long_parted` built (2026-10-03)

The reference's hairstyle, drawn by grok on `katherina_grok` with only the hair
changed (`ref-local/katherina_grok_nohat/`), passed the body check and was
traced and built as `long_parted`. The detail is under the D5 plan's steps 1
to 5 above. In short: on our figures with no body mapping at all it reads as
the reference; its silhouette lands within 0.036 head radii of the reference's;
it holds from height 0.8 to 1.3 and on every `long_traced` wearer at its own
length, the shortest (Chiyo) the weakest; no preset wears it yet, so nothing
already drawn moved. With the owner: who wears it, Katherina's side tail with
it, and Satoko's tip line if she is one.

### D5: the hair-trace audit (2026-10-03)

The owner: why has the hair trace not worked, tested as hypotheses. Scripts in
`harness/hair_audit/`, sheets in `out/hair_audit/`; widths below are
half-widths in head radii, on each image's existing calibration.

- **H1, the hair is drawn on a different body: confirmed, the root cause.**
  At one head radius (`lineup.py`) the realistic reference runs 3.17 head
  radii from chin to belt, ours 1.38 at height 1.0 and 1.72 at 1.3; at the
  belt its body (arms included) is 2.18 wide, ours 1.17 (`proportions.py`).
  The hair-only reference's outer edge stays 0.26 to 0.53 outside
  `katherina_grok_real`'s body all the way down, so below the chin its shape
  is that body's. The deciding fact: there the body (1.75 to 2.18) is wider
  than the hair at the chin (1.51) and pushes the hair out; ours (0.88 to 1.17)
  is narrower than our hair at the chin (1.26 to 1.51), so on our body the hair
  falls free, which the reference never shows. **Control** (`chibi_control.py`):
  `katherina_grok`'s hair, drawn on a chibi body, placed by one uniform scale
  and no body mapping, fits Katherina at 0.8, 1.0 and 1.3 and Satoko and
  Linnea, with no cape and no pinch; only its length is off, which is
  `_hair_fall`'s job.
- **H2, the mapping makes the cape, and no remapping rescues it: confirmed.**
  `retarget.py` warps the hair-only reference onto our landmarks three ways.
  As traced (D5's: y squeezed onto our belt, x kept) gives the cape. Scaled
  with the body (`_garment_placement`'s rule; 0.52 at height 1.0, 0.62 at 1.3)
  hides the fall behind the body and reads as a bob. Body plus a kept
  thickness leaves a shelf at the shoulder. None looks like `katherina_grok`.
  Any map that gives a free fall has to bring the fall from somewhere else.
- **H3, too many segments: confirmed, secondary.** D5's shapes have 276 to 334
  segments, 18% to 51% of their edges under two stroke widths (0.085 head
  radii at 1.3), fitted at 0.008 against the skill's 0.012 to 0.018, with 60
  lines on top; `long_traced` has 28 segments, none that short. That is the
  stair-steps and the thick short strokes, not the cape.
- **H4, the front/back split came from an image that cannot carry it:
  confirmed.** `hair_with_human_shape.png` cuts out only the body that shows
  (0.73 wide), so all hair outside it counts as front, the falls over the
  shoulders and arms; `katherina_grok_real` and the owner's red trace have one
  lock a side in front, 0.36 wide, the jacket showing either side. The
  shoulder cut, the funnel and the owner's lock turned one layout into the
  other by cutting pixels, which is where the ledges and hooks came from.
- **H5, two references, two hairstyles: confirmed.** One a narrow straight
  fall, one a pear to 2.58; part of the pear is the realistic arms (H1).
- **Not a cause: the head.** The fringe, parting and curtains sit on our face
  in every variant, as D5 measured (0.1 to 0.2).
- **The process:** `detail-strategy.md`'s rule 1 has `katherina_grok_real`
  never traced, and D5's first finding already measured its body at about twice
  ours below the shoulders. That was a stop signal; the work went on patching
  below the jaw instead (now an anti-pattern there).

Limits: the warps are three families of width map, not every map; the control
used `katherina_grok`'s own hairstyle, so it shows a chibi-drawn reference
transfers, not that grok will draw the new style well at chibi proportions,
which is the plan's main risk; the chibi reference's hair was picked by colour
(checked by eye, `chibi_masks.png`) and its dark underside missed.

**The owner's call:** a new reference, the hairstyle drawn on the tall-chibi
body, checked by `gate.py`, then traced; the D5 plan above. The check's
controls: `katherina_grok` against itself passes, and off it the check reads
the soles at 5.941 and the hem at 4.231 against the 5.94 and 4.26
`tall_chibi` records; `katherina_grok_real` fails, its soles at 14.57.

### D5: the owner's hair-only reference traced (2026-09-29)

The owner, after the audit: interpolating what the old reference hides will
not get there; a new reference shows only the hair
(`ref-local/katherina_hair/`), to be split into the part in front of the body
and the part behind it. `hair_only.png` is the whole hair and
`hair_with_human_shape.png` the same with a human silhouette cut out (what
hangs in front); both carry alpha and share a frame (99.7% of the front lies
inside the whole). The three `segments_hair_only` cuts are each nearly the
whole hair, so are not used. `harness/hair_only/`:

- `register.py`: the new images have no face, so the front piece is
  registered to `katherina_grok_real`'s seen hair between brim and chin (one
  uniform scale and a translation, best intersection over union with the
  bat left out): scale 0.504, overlap 0.78, riding the old parting,
  opening and curtains. That puts it on D0's face-width calibration.
- `trace.py`: the mass is the whole hair, the front piece the human-shape
  cut, each with its holes, the outline moved in by half the measured 2 px;
  the line work by `lines.py`'s method on the whole hair, the luminance
  clamped at the fill's 70th percentile first so the sheen's zigzags do not
  make lines, lines along the front's edge dropped, each put on the piece it
  lies on (60, 44 in front; a median 2 px, 0.011 head radii); the as-is belt
  squeeze (0.567) after. Nothing is filled in.
- `preview.py --hair-only`: on Katherina at 1.3, beside the reference.

**Seen:** the traced outline and lines ride the reference (`overlay.png`);
on Katherina the hair reads as the reference's: the parted fringe, the
curtains, the locks and their pointed tips, the strands. The front piece is
the reference's width, so over our narrower body it hangs over the arms.

**One lock over each shoulder** (the owner: as on `katherina_grok_real`, one
strand a side comes over the shoulder, the rest goes behind it and the arm).
`harness/hair_only/shoulders.py` cuts the front piece at our shoulder line.
Above it the curtains stay in front. Below it each side keeps only the lock
against the body, 0.38 head radii wide (the original's front lock measures
0.36), followed down from the shoulder until the lock ends; a tip of another
lock that falls in that band is dropped. The mass is unchanged, so that hair
draws behind the arms. 22 of the 60 strands stay in front. On Katherina at
1.3 one lock hangs over each side of the jacket to about the belt and the
rest shows beside the arms. With the owner.

### D5: the reference's hair traced (2026-09-29)

The owner, on the study: the only thing that would work is tracing the
reference's hair (`ref-local/katherina_grok_real/`) and filling in its gaps;
a second exception to decision 4, after the hands. `harness/trace_hair/`:
`locate.py` finds `segments/`'s hair, hat and bat to be exact pixel cuts of
the composite (mean colour difference under 0.6, no pixel over 20);
`calib.py` puts the hair mask beside ours in head radii (D0's face-width
calibration, 88.7 px per head radius today); `trace_hair.py` fills the gaps
(the crown under the hat from a fitted circle, the right side under the bat
from the left mirrored, the back hair behind the body by each side's hull),
splits front from back at the row where the arm comes out, maps it onto our
body, and fits; `preview.py` stands it in for `_hair_mass` and `_hair_front`.

**Measured:** to the jaw the reference's hair agrees with ours within 0.1 to
0.2 head radii a side; below the shoulders its body is about twice ours in
both directions (0.483 from shoulder to waist), its neck 0.57 head radii
against our 0.12.

**Seen:** the traced fringe, parting and side curtains read as the
reference's. Below the jaw it does not transfer: the flare that sits on the
reference's broad shoulders lands under our big head as a hood (worst on
Linnea), in both mappings tried; the front locks come out as short hooks;
the reference's own interior lines read as scratches. With the owner.

**As-is, at height 1.3** (the owner: trace it unmapped first, put it on
Katherina at the tallest height, then discuss; `trace_hair.py --as-is`,
`preview.py --as-is`). The overlay rides the reference's lines. On our
figure the fringe, parting and curtains fit the head, and the front locks
hang over the jacket to about the belt, as on the reference. The back hair
does not: the reference's back sheets reach 2.3 head radii out, about one
head radius past our arms a side even at 1.3, and the fill behind the body
(each side's hull) shows as a wide cape with straight edges, since our arms
are too small to cover it. With the owner.

**The line work, traced faithfully** (the owner: invest in tracing the
segment with all its lines; the contrast is low). The hair's lines are only
a little darker than its fill, which carries sheen and shadow, so a darkness
threshold found 16. `contrast.py` brings them up with a black-hat (the grey
closing over a disk of radius 4 px, minus the picture): a thin dark line
comes out bright on sheen or in shadow alike, and flat fill of any shade near
zero. `lines.py` thresholds it with hysteresis (seeds over 18, grown over 8),
bridges one-pixel breaks, thins to a skeleton (Zhang and Suen, in numpy),
walks it, carries lines through junctions and across gaps of up to 8 px where
the two ends face each other within 35 degrees, drops paths that hug the
cut's edge (the outline), and fits: 28 lines, 196 segments, riding the
reference's lines (`out/trace_hair/lines_overlay.png`); the hair clip's ring
is traced too and dropped in the preview. On Katherina at 1.3 (as-is, the
silhouette now fitted at 0.012) the lines read as the reference's line work,
not as the scratches the 16 did. Still open: the back hair's cape, and the
filled-in edge under the bat is jagged.

**The gaps interpolated** (the owner: the segment has only what showed, so
the missing areas are interpolated or extrapolated). `locate.py` found the
dress, collar, staff and belt to be exact cuts too; `occlusion.py` maps what
hides the hair where. `fill.py` replaces the stand-ins, filling along the
hair's fall: each side's outer edge row by row (seen where the page beyond is
open for 22 px, a Hermite across hidden runs), the right side from the left
mirrored plus its own measured departure (the brim and the bat hide it for
about two head radii with no seen row), the back hair's bottom edge column by
column (a monotone cubic through the seen tips), the crown extrapolated from
each side's highest seen row into a top 0.25 head radii over the skull, and
the front piece taking fill only where the hat or the bat hid it (a first
version let the crown's chord cover the forehead). On Katherina at 1.3 the
face opening, fringe, curtains and front locks are the reference's. Open:
the lines stop where the seen hair does (at the brim row on a bare head); the
edge below the bat is ragged; the back hair is as wide as the reference's.

**Shortened by the belt, and audited** (the owner). As-is now keeps the head
as traced and squeezes y below the cheek line by 0.566, which puts the
reference's belt (4.40 head radii) on Katherina's at height 1.3 (2.75,
measured off her render) and its chin at 0.96 (ours 1.006); widths as traced.
`audit.py` draws the trace back in the composite's pixels, alone, over the
segment. It found two faults of the fill and two real differences:

- **The fill covered seen page** (the whole region between the outer edges
  down to the bottom edge), and the trace closed every hole. Now page (near
  black, outside every cut, connected to the picture's border; dark alone
  took the pupils) stays empty, and the trace keeps pieces and holes, drawn
  with an even-odd fill.
- **Faithful where it can be measured:** the traced outline a median 3 px
  (90th 4, max 6.4) from the segment's seen edges, the half outline the
  trace grows by; the lines' recall 97%, precision 100%.
- **Line weight:** the segment's lines are a median 2 px, 75th percentile
  4 px, about its outline's weight; ours are 1.15 px against our outline's
  2.84, under half. At the segment's weight (0.028 head radii) the lines
  carry the hair the way the reference's do.
- **Tones:** a fifth of the segment's hair is a darker purple (the underside,
  the hair behind the neck); ours is one flat tone. A second tone on hair
  is the owner's call under the flat-colour rule.

### D5: the `long_traced` study (2026-09-29)

`harness/detail/hair_study.py` stands candidates in for the cut's hairline
and strands: **A** today (two sweeps off the parting, one line down each
fall); **B** strands only (three lines of uneven length down each fall, a long
sweep off the crown over the temple into the fall, and a divider up from the
fringe's edge toward the parting per lock); **C** B with the fringe parted
into three locks a side, each tip hanging onto the forehead (0.12 head radii
at the parting, a fifth of that at the temple, where the brows are close) and
leaning toward the temple; **D** four longer locks (0.18). The fall strands
are given in the trace's frame and take the mass's own stretch, so they stay
in the fall at every `hair_length`. On Katherina with and without her hat,
Satoko (pale tips), Kyoko (near black), Linnea, Chiyo (the shortest fall,
under a hat) and silver hair on dark skin; heights 0.8 to 1.3; the insert
size.

**Seen:**

- A first C cut the edge up into the hair between points on today's line.
  Across this cut's slanted V hairline that read as bites out of the edge,
  not as locks; hanging the tips below the line fixed it.
- **B** makes the mass read as hair rather than a flat shape; on near-black
  hair the lines are faint, as every line on dark hair already is.
- **C and D** read as a parted fringe, closest to the reference's sweep off
  the parting; D's longer locks come nearest the brows at the temple.
- Under Katherina's hat the locks show below the brim; Chiyo's hat covers
  her fringe entirely, and her short fall takes the strands without crowding.
- At the insert size nothing turns to mud: the fall strands read as texture
  and the fringe as a jagged edge.

**Recommendation:** C. Its locks read without reaching the brows, and B's
strands come with it. D if the owner wants the fringe to carry more.

**The owner's call (2026-09-29): no strand lines.** The added lines make the
hair look worse, not more detailed: the flat mass reads as a choice, and
lines drawn into it read as weird. So B, C and D are out. **E** was added to
the study after: C's three locks with today's four lines, nothing else, so the
fringe's outline changes and the hair stays one flat shape. With the owner.

### D4d follow-up: the mitten fitted to a traced cuff (2026-09-27)

The owner: Katherina's hands did not meet her sleeves, the mitten's flat top
off to one side of the traced cuff's slanted edge. The cuff fit above only
reached the traced hands; the mitten still hung from the plain arm's wrist.
`_mitten_placement` now turns it onto the cuff's opening (`_cuff_opening`),
centred and facing out of it, its top edge on the cuff's edge rather than
tucked under (it is drawn over the coat), and `_hand_centre` follows, so the
staff still runs through the fist. Only Katherina wears a traced sleeve, so
only her `ref-out/` render changed. Compared mitten, grip and traced side by
side on her; the owner kept the mitten as the default for now, the traced
hands wanting more work before they are picked up again.

### D1 follow-up: the line under the chin (2026-09-27)

The owner: the chin reads as a different weight from the rest of the face.
`_head` draws the line under the chin thinner than the jaw on purpose (the
throat stands in front of it), at `_interior_w(sw, 0.6)`. Before D1 that was
0.60 of the silhouette's weight; D1's split took it to 0.44, a visible step at
the jaw's corners. Compared at 0.44, 0.60, 0.8 and 1.0 on Satoshi, Katherina,
Reinhard and Chiyo (`harness/detail/chin_weight.py`); at 1.0 the chin read
heavier than the sides, probably because the hair covers the side lines'
outer edge (not measured). The owner picked 0.60: now `_outline_w(sw, 0.6)`.
All 20 `ref-out/` renders and both bases changed; the catalogue did not.

### D4d: the hands locked in for now (2026-09-27)

The owner: keep the best recommendation, defer the rest (another pass on the
hands later), good enough for now. Built from the studies: `_traced_placement`
fits a traced hand to its cuff's opening (`_cuff_opening`: on a traced sleeve
the cuff band's far side, a fitted line; otherwise the wrist line), turned so
its traced wrist (`_HAND_*_INTO`, now emitted with the poses) lies along it,
tucked `_HAND_CUFF_TUCK` under the cuff; the open hand's wrist fills
`_HAND_WRIST_FILL` of the opening; size `_HAND_TRACED_LENGTH` 0.50. The staff
runs through a traced grip's channel (`_hand_centre`, `_grip_channel`).
`HAND_STYLES`: "mitten" (the default), **"grip"** (the recommendation: the
traced fist on a held staff, the mitten otherwise, since the traced open hand
reads thin on a chibi), "traced" (both). The web tool's Hands dropdown lists
all three. No preset changed (the owner has not picked which take which).

**Measured:** with the default, all 105 snapshot renders byte-identical to the
committed tree; tests for the styles, the open bare wrist and the staff in
the channel; 548 passed, 1 skipped. The superseded study scripts are marked
as records.

**Deferred:** a relaxed pose of its own (a half-closed hanging hand), the
grip's size against the cuff on a tube sleeve, which presets take which
style, and the elbow.

### D4d: the hands fitted to the cuff openings (2026-09-27)

The owner: match the hands to the cuff openings, their positions and angles.
`harness/trace_hands/cuff_fit.py` finds each opening in the arm's own frame:
on a traced sleeve, the cuff band's chain placed on the figure, its long axis
the band, the side further along the forearm the opening, a line fitted
through it (Katherina's: 8.7 degrees off level, 0.228 head radii half-width;
the earlier measure by its lowest points read it level); on a drawn sleeve or
a bare arm, the wrist line. Each hand is turned so its traced wrist lies
along the opening, facing out of it, its wrist's centre on the opening's,
tucked 0.04 head radii under the cuff; the open hand's wrist widens to 0.9 of
the opening, the grip keeps its shape and the staff runs through its channel;
size 0.50. Seen: on both of Katherina's arms the hand now comes out of the
cuff at its angle, the fist following the raised arm and the open hand the
jacket's sloping cuff; on Krista's sleeve and bare arm the join holds. With
the owner.

### D4d: the wrist's angle against the sleeve (2026-09-27)

The owner: zoom on Katherina's arms and turn the hands so the wrist's angle
matches the sleeve's. `harness/trace_hands/wrist_angle.py` turns each traced
hand about its wrist so the direction its reference forearm came in from lies
along our forearm (elbow to wrist), then lets it swing with the arm; rows
upright, half, matched. **The staff arm** needs -80 degrees in the arm's own
frame, and the arm's 36-degree swing undoes 36 of it, so "half" comes out
nearly upright; **matched** carries the sleeve's line on into the back of the
hand, but the fist then grips the staff at a slant and its fingers overhang
the staff's far side. **The other arm** needs only -3.5 degrees (the arm
hangs nearly straight), so matching changes nothing: the odd look there is
Katherina's traced jacket cuff, whose opening slopes and is wider than the
open hand's wrist, not the arm's axis. A first measure of the cuff opening
off its chain's lowest points read it level; it needs its edge found
properly. With the owner.

### D4d: the relaxed hand, both options (2026-09-27)

The owner: build both (the open hand smaller; a loose fist from the grip's
pieces) and compare before locking anything. `harness/trace_hands/relaxed_study.py`,
every column with the grip "wrist, smaller": mitten; open 0.65; open 0.50;
a fist from the grip's pieces with nothing held (the channel filled, a hull
outline), upright with the wrist from above; the same fist turned a quarter
so its traced wrist faces up the arm. On Katherina, Krista, and Krista in the
base layer. Seen: **open 0.50** is the right size but reads thin, the fingers
spindly on a chibi; **the fists** read as clenched, tense rather than
relaxed, and "from above" leaves the hull's top edge across a bare wrist;
"turned" is muddled (the rolls stand vertical). At whole-figure size the
mitten is still the cleanest relaxed hand. With the owner.

### D4d: the grip's position, a study (2026-09-27)

The owner: before locking the hands in, work on the positioning and the
transitions; it looks especially odd on Katherina holding her staff (the
chibi reference, `ref-local/katherina_grok/`, for comparison). Cause: her
staff arm is swung out 36 degrees, so it is not the hanging arm option (a)
was chosen for; the fist kept upright with its wrist taken from above left a
wedge between the diagonal cuff and its flat top, the fist hanging below the
sleeve. `harness/trace_hands/grip_study.py`: **wrist**, the fist anchored at
its own traced wrist (its side, where the reference's forearm met it) on the
arm's wrist, upright, the staff moved to run through the fist's channel;
**wrist, smaller**, the same at 0.50 head radii. Both connect to the cuff and
sit as the chibi reference's fist does, the forearm coming in from the upper
side; the smaller matches the chibi reference's fist (about 0.45 against its
head). The relaxed hand, long and open, still reads odd beside it: the chibi
reference's other hand is a small closed fist. With the owner.

### D4d H2, H3: the traced hands drawn (2026-09-27)

The owner's calls: option (a), the grip's fist kept as traced with the wrist
from above; an elbow later (the plan's deferred list). **H2**:
`harness/trace_hands/emit_hands.py` writes `_HAND_RELAXED` and `_HAND_GRIP`
(pieces in drawing order: outline, holes, interior lines) into
`character.py` between marker lines. **H3**: `CharacterParams.hand_style`
("mitten", the default, or "traced"; `HAND_STYLES`), a "Hands" dropdown in
the web tool. `_traced_hand` draws the pose at `_HAND_TRACED_LENGTH` (0.65
head radii, size B), mirrored per side: the grip when the hand holds the
staff, anchored at the top of the back of its fist over the staff's channel
(`_grip_anchor`) and kept upright against the arm's swing; relaxed
otherwise. **The transition** (the owner): the traced hand is drawn under its
arm, so a sleeve's cuff lies over the wrist; the relaxed hand's first stretch
(`_HAND_WRIST_STRETCH`, 0.30 of its length) widens from its traced wrist to
the arm's and tucks `_HAND_WRIST_TUCK` up under it; a bare arm leaves its
wrist unstroked under a traced hand.

**Measured:** with the default mitten all 105 snapshot renders byte-identical
to the committed tree; a test that traced hands draw and a bare arm's wrist is
open under them (and closed under the mitten). By eye
(`harness/trace_hands/look.py`, `checks.py`): the cuff over the wrist on
sleeves, a bare forearm running into the hand, the grip round the staff; at
heights 0.8 and 1.3, an arm swung out, a dark skin tone, and at the insert
size, where the hand reads as a hand. 548 passed, 1 skipped.

### D4d H1: the two hands traced (2026-09-27)

`harness/trace_hands/seg.py` mapped the fills (outline and page are one black
here): the grip is four skin pieces (the back of the hand with the thumb, the
index roll, the middle and ring together, the little finger) with the staff's
wood between them; the relaxed hand one piece and two curled fingertips.
`harness/trace_hands/trace_hands.py` traces **each piece as its own outlined
shape** (the skill's shape decomposition), in drawing order: first one union
silhouette with interior lines was tried, and the staff showing between the
grip's rolls and the back of its hand (5 to 7 px wide, too wide to close over)
cut a notch into it instead of drawing a line. Pieces are picked by colour
(every skin fill over 30 px, a mean red above 150): seeds read off a picture
landed two in one piece where a fingertip is a sliver. Lines inside one piece
(the middle and ring's split, the relaxed hand's outer finger line) are the
dark pixels inside it, centre-lined and fitted. Points are relative to the
wrist's centre, in the image's axes, in units of the hand's length (size B is
then 0.65 head radii), with the forearm's direction kept per hand
(`out/trace_hands/hands.json`). The overlay rides the reference's lines on
both hands (`out/trace_hands/trace_both.png`); of the relaxed hand's two
parallel outer lines only one is found.

**Open, for H3:** the grip's forearm comes in from the side in the reference
(the elbow bent, the staff across the fist); our arms have no elbow and hang,
so turning the grip to follow our forearm would lay its finger rolls along the
staff instead of round it.

### D4d H0, round two: size B without the mitten (2026-09-27)

The owner: B is the best size; the first mock pasted the hand over the mitten,
so redraw it without, and add a bare arm. `size_mock.py`'s `round_two`
(`out/trace_hands/size_mock_b.png`), Krista dressed and in the base layer at
1.0 and 1.3, the mitten not drawn. **The sleeve join works**: the hand reads
as coming out of the cuff, which hides that its wrist is narrower than the
arm. **The bare join does not yet**: the arm's path closes with a stroke
across the wrist, which the mitten used to cover; and the arm is wider than
the hand's wrist (about 0.37 head radii against the traced 0.24 at height 1.0,
less at 1.3, where the arm tapers), a step. For H3: a bare arm leaves its end
unstroked, and the hand's first stretch, its wrist, widens from the traced
width to the arm's, so the forearm runs into the hand.

### D4d H0: the reference's hands calibrated (2026-09-27)

`harness/trace_hands/calib.py`: each hand's wrist is where its skin meets the
cuff, fitted as a line in a box read off the gridded close-ups (the sleeve
and the dress are the same navy, so "skin touching navy" alone ran down the
relaxed hand's whole side), the hand closed over its own interior lines
before labelling (the trace skill's step 3; the grip's finger rolls had cut
it into pieces). Measured (the reference's head radius about 84 px):

| | wrist | length | length / wrist |
|---|---|---|---|
| relaxed | 36 px, 0.43 head radii | 98 px, 1.17 | 2.72 |
| grip | 26 px (foreshortened) | 68 px, 0.81 | 2.63 |
| our mitten | 0.39 head radii | 0.31 | 0.79 |

The wrists nearly agree against the head; the reference's hands are more
than three times as long as the mitten, an adult's hand about the face's
length. So a uniform scale cannot fit both the wrist and a chibi's hand.
`harness/trace_hands/size_mock.py` pastes the reference's relaxed hand onto
Krista (a harness preview, nothing ships) at three sizes: **A**, by the wrist,
about 1.06 head radii, reaches mid-thigh, too big; **B**, 0.65 head radii,
reads as a real hand on this body at 1.0 and 1.3; **C**, 0.45, reads spindly,
its wrist far narrower than the sleeve. At B the traced wrist is narrower than
our arm's: the cuff hides it on a sleeve, a bare arm needs the join handled
(the arm tapering into it, or the hand's top widened to the arm). With the
owner.

### D4c: the hands, research and a study (2026-09-27)

The owner asked for proper research first. A Sonnet delegate (59k tokens)
read drawing tutorials and style guides: `docs/detail-inventory/hands-research.md`
(sources listed there). What is sourced: chibi and distant figures keep the
thumb and drop creases and nails first; a hand is a finger mass plus a thumb;
a grip is stacked curves, one per finger, down the pole, the thumb the anchor;
knuckles are interior lines at the joints, not notches in the outline. The
delegate's level recommendations for our sizes are its own inference and were
treated as a hypothesis.

`harness/detail/hand_study.py` draws levels over today's mitten as interior
lines, for the relaxed hand and Katherina's hand on the staff (drawn over the
staff already), at 4x and at the smallest insert size. Seen: **level 1** (a
thumb crease) makes the thumb its own part on both hands, cleanly; the grip's
**stacked finger rolls** (levels 1 to 3) read as fingers round the staff;
level 2's two finger lines at the tips of the relaxed hand read as a paw, the
failure the research warned of; **level 3** (a fold where the fingers curl
under, one separation below it) reads as a loose fist. At the insert size
every level shows the same silhouette: nothing turns to mud, the lines just
fade. With the owner.

### D4: the bare leg's knee built (2026-09-27)

The owner's pick, "realistic, with height": `_knee_notch_d` draws the bare
leg with the knee in by `_KNEE_IN` (0.10), the calf's control `_CALF_CTRL`
(1.15) out from the narrowed knee and the bare ankle to `_BARE_ANKLE` (0.70)
of it, the bare foot taking that ankle (`_bare_ankle`); its strength follows
the limb taper (`_knee_strength`: none at 0.8, full from 1.3). The trousers and
the boots are untouched. Continuous: the leg's inside, one curve without a
knee, is split at the knee's height (`_quad_u_at`, a bisection;
`_quad_crossing`'s closed form hit a math domain error on one figure) into the
same curve in two halves, and its points blend toward the knee's.

**Measured:** at 1.3 pixel-identical to the study's realistic row; across
height 0.8 no element moves by more than 0.25 px (a test), the extra
anti-aliased pixels there being rounding in the arms, not a jump (the leg's
path changes structure only); trousered renders byte-identical, the bare-legged
ones changed (`ref-out/`: Satoko, Katherina, Keiko, Reika, Chiyo, the sheets
and the female base). 545 passed, 1 skipped.

### D4: a knee on the bare leg, the study (2026-09-27)

`harness/detail/knee_study.py` draws the bare leg (only: the trousers keep
their measured, nearly straight run) with a knee: in at the knee, the inside
split there into two curves, the crotch as it was. The owner asked whether
the ratios are realistic; measured off the render (knee = 1; a real leg front
on: upper thigh 1.4 to 1.6, calf about 1, ankle about 0.6):

| | upper thigh | mid-thigh | calf | ankle |
|---|---|---|---|---|
| today, no knee | 1.15 | 1.08 | 0.98 | 0.85 |
| firm (knee in 0.10, calf swell 0.08) | 1.35 | 1.15 | 1.12 | 1.00 |
| realistic (knee in 0.10, calf 1.03, ankle 0.70), full | 1.35 | 1.15 | 1.04 | 0.76 |

The firm knee only narrowed the knee, leaving the calf and ankle heavy. The
realistic row narrows the bare ankle too, and the bare foot with it (it is
sized off the ankle); the boots keep today's width. The ankle measures 0.76
against its 0.70 target because the outline adds a fixed width. With the
height (as the limb taper): none at 0.8, light at 1.0 (calf 1.01, ankle
0.87), full at 1.3. With the owner.

### The two other covers regenerated (2026-09-27)

At the owner's request, after the eye and spacing fixes:
`../short_stories` 3c496e7 (the Everglow cover, `scripts/build_cover_dual.py`)
and `../time_slider_katherina` 617b37d (the cover by `tools/generate_cover.py`,
the reference by `render.sh --preset katherina --no-metadata`, as it was made
before). Both covers byte-identical to the rebuilds the owner reviewed.
`../valley_of_mist` not regenerated (the owner: not for now).

### D3 follow-up: the eyes' spacing follows their size (2026-09-27)

The owner: on the rebuilt Everglow cover Gero's eyes still read much farther
apart than Linnea's. Measured: their centres were nearly as far apart (0.85
and 0.88 head radii, `eye_dx` held at 0.46 whatever the eye's size) but his
eyes are smaller, so the gap between them was 0.56 of an eye's width against
her 0.36 (Tenno 0.58, Krista 0.30). `harness/detail/eye_spacing_study.py`
(the gap following the eye's width at k 0, 0.5, 1; the target the cast's
median 0.44, not the default face's 0.58, which sat at Gero's end); at k 1
the eye's corner crossed the face's edge at the sliders' tops. The owner's
pick: k 1 with a limit. `_eye_placement` now puts the eye's centre at `w * (1
+ _EYE_GAP)` from the face's centre, `w` the eye's half-width, but never
nearer the face's edge than `_EYE_CORNER_CLEAR` (0.05) at its corner; the
lash's upper edge is kept inside too (`_eye_lash`).

**A bug, and a retraction.** The flick cap of the previous entry (e504eb0)
never worked: inside `_eye` the lower lash's sample count was also called
`reach` and shadowed the parameter, so every flick was cut to nothing (the
cap read 8 px against a real 28). The face-edge test passed, since it
computed its own reach. e504eb0's `ref-out/` and the two covers rebuilt to
scratch then had flickless eyes. Fixed (the local renamed `lower_n`); a new
test reads the lash off the rendered face (the flick past the corner, inside
the face) and fails on all three of its presets with the shadow put back.

**Measured:** `ref-out/` (all 20) and the bases refreshed, the cast's faces
checked by eye; 544 passed, 1 skipped. Both covers rebuilt to scratch again
(`out/review/covers_before_after.png`).

### D3 follow-up: the eye and the age, one story at a time (2026-09-27)

The owner, on a rebuilt Everglow cover: Gero (face age 1.55) and Linnea (0,
though she is fifteen) looked inconsistent; eye sizes should not differ this
dramatically within one story; scaling them is fine but as its own choice.
Measured: the eye's area fell to 0.87 at age 0.4, 0.70 at 1, 0.46 at 2.
`harness/detail/eye_age_study.py` (now, light, none); the owner's pick
**light**: `_MATURE_EYE_SHARE` 0.5 to 0.2, `aged_face`'s eye terms at a
third. The area is now 0.95 at 0.4, 0.87 at 1, 0.76 at 2; how big a
character's eyes are is `FaceStyle.eye_size`'s (the web tool's Eye size).
Ages set: Linnea 0.4 (fifteen), Katherina 0.35 (fourteen at the start of her
story, the owner).

**The eye inside the face.** On the study's "none" row the eyes reached and
ran over the face's edge, which read as creepy (the owner). Measured with
"light": the eye's outer corner stays 0.06 head radii inside the face even at
the top of the web tool's eye size and width, but the lash's flick crossed by
up to 0.036 there, and by 0.009 on Krista at her own settings. `_eye_lash`
now shortens the flick (never lengthens it) so its tip stays `_EYE_EDGE_CLEAR`
(0.03) inside the face's edge at the eye's height; a test holds the corner
0.04 inside and the lash inside, for every preset at face ages 0, 1 and 2, at
its own settings and the sliders' tops.

**Measured:** `ref-out/` (all 20) and the bases refreshed; 541 passed, 1
skipped. The Everglow and Time Slider Katherina covers rebuilt to scratch
(`out/review/covers_before_after.png`), not yet written to their repos.

### D4b: the limbs taper with the height (2026-09-27)

The owner's calls over three rounds: the hands follow the wrists; the taper
grows with the height instead of being one amount for all (the point of it,
explained to the owner: a straight tube of an arm is the chibi's, fine on a
short young figure and a pipe on a tall grown one); and, seeing the full
taper leave a tall figure's upper arm 1.5 times its wrist once D4a had
widened the arm, half of it at most. Now `Skeleton.limb_taper =
_limb_taper_at(height)`: 0 at 0.8, `_TAPER_MAX` 0.5 from 1.3, linear between,
0.2 at 1.0 where every preset stands (about 7% narrower at the wrist, the
hands with it). `_limb_build` reads it for `_arms` and `_legs_and_boots`.

**Measured:** all 20 `ref-out/` renders and both bases changed (every figure
stands at 1.0); at 4x the wrists, cuffs, sleeves and hands join cleanly on
six presets, Katherina's grip on the staff included. A test of the mapping.
The web tool restaged. 490 passed, 1 skipped. The three study scripts are
records now (the `_LIMB_TAPER` they patch is gone).

**Open:** the bare leg has no knee (the adult taper was measured on
trousers); a knee is a new shape, a separate study if the owner wants one.

### D4b: the limb taper, the study (2026-09-27)

The retired adult build's limb taper is still in `_arms` (the elbow 15% and
the wrist 34% in) and `_legs_and_boots` (the ankle to 0.85), riding the build.
`_LIMB_TAPER` (0, byte-identical: checked, 0 of 105 renders differ) sets how
far along it the limbs are drawn, through `_limb_build`.
`harness/detail/taper_study.py`: taper 0, 0.5 and 1, on Krista's base layer,
Satoshi, Keiko and Satoko at heights 1.0 and 1.3. Seen:

- **The arms** read better tapered: at 1 the forearm narrows to a wrist.
- **The hands** take the wrist's width (`_hand`: `w_wrist * 1.02`), so at 1
  they shrink with it and read small; kept at today's size they overhang the
  narrower wrist like a mitten stuck on; **half way** between reads as a
  hand a little wider than its wrist.
- **The legs barely change**: the adult taper was measured on trousers
  (`ref/satoshi.png`), nearly straight below the thigh, so a bare leg stays
  a tube with no knee.

**Recommendation:** taper 1 with the hands half way. The bare leg's knee is
a separate question for the owner.

### D4a: the widths follow the height (2026-09-27)

The owner's pick, k = 0.6: `stretched` scales the body's widths (shoulders,
waist, hips, hem, arms and where they hang, legs) by `1 + _WIDTH_FOLLOW *
(h - 1)`, the neck kept. **Predicted:** every preset byte-identical (all at
height 1.0, where the stretch is not applied). **Measured:** 0 of 105
snapshot renders differ from the committed tree's (taken with `git stash`;
an older snapshot, from before the ages, gave a false 60); the height test
restated (the widths grow by the rule, the neck does not); the web tool
restaged. 489 passed, 1 skipped.

### D4a: the widths at height, the study (2026-09-27)

`harness/detail/width_study.py` scales the body's widths after the height
stretch by `1 + k * (height - 1)` (shoulders, waist, hips, hem, arms and
where they hang, legs; not the neck), k 0, 0.3 and 0.6, on seven characters
and Krista's base layer at 0.8, 1.0 and 1.3. At 1.0 nothing moves (the
stretch is not applied there), and no preset uses another height, so this
changes the slider, not the cast. Seen: the traced coat and jacket, the long
coat, the robe and the skirts all follow; only Satoshi's hair reaches the
canvas edge, as before. At 1.3, k 0.3 is still a little lanky, k 0.6 reads
as an adult build, and it is the skirts and the hakama that grow widest.
With the owner.

### D3: the cast's ages applied (2026-09-27)

The owner approved the lineup ("mostly good", the nose and beard then
fixed). Applied: Katherina and Linnea 0 (unchanged); Kyoko and Tomohiro 0.6;
Satoko, Satoshi and Viktor 0.8; Krista, Elara, Keiko, Reika, Haruto and
Reinhard 1.0; Gero 1.55; Chiyo, Daizen and Tenno 2.0. The male and female
bases stay at 0.

**One correction to the proposal:** Kyoko is Satoko's earlier self
(`_before`), as Tomohiro is Satoshi's, and the proposal had her older (1.0)
than Satoko (0.5). Now the pair mirrors Satoshi and Tomohiro: `_before` takes
the earlier self's face age, 0.6 for both.

**The aged four** no longer bake `aged()` into their face: their plain face at
`face_age = 1 + years`. **Measured:** each renders SVG-identical to the old
baked face at age 1 (Gero's 1.55 included), so the web tool no longer ages
them twice. `presets.aged` stays as a helper with no preset caller.
`ref-out/` refreshed (18 changed: every preset but Katherina and Linnea, and
the sheets); two tests that assumed age 0 now read the mouth's real height
and set Satoko's baseline to 0. 489 passed, 1 skipped. `../valley_of_mist`
not regenerated (the owner's call: not for now).

### D3: one moustache rule at every face age (2026-09-27)

The owner: the chibi's beard has always sat a bit high; match it to the
grown face's. `harness/detail/beard_height.py` put the moustache's top at
today's 0.36 head radii, at 0.40, and at the grown face's rule applied at age
0 too (under the nose's line, about 0.43); the owner picked the one rule. Now
`tash_y = _nose_y(sk) + _BEARD_NOSE_GAP` at every face age, nose drawn or
not; `_BEARD_TASH_Y` and the settling blend (`_BEARD_NOSE_ONSET`) are gone.
The band of hair over the lip comes out the same on the chibi face and the
grown one (about 0.087 head radii, some 2.7 times the drawn outline), and
still reads at the smallest insert size.

**Predicted:** only the three bearded men change, in all four states each.
**Measured:** exactly those 12 of 105 snapshot renders; `ref-out/` refreshed
(5 changed: Gero, Daizen, Reinhard and the two sheets); the moustache test
restated against the rule and the drawn outline, at face ages 0 and 1. 489
passed, 1 skipped.

### D3: the moustache ends under the nose (2026-09-27)

The moustache's outer corner now drops with the mouth
(`_MOUTH_REALISTIC_DROP` times the face build's growth), and its top edge
moves to `_BEARD_NOSE_GAP` (0.05 head radii) under the nose's lowest point
(`_nose_y`, shared with `_nose`), settled by face maturity
`_BEARD_NOSE_ONSET` (0.25) while the nose is still faint, so it never
jumps. **Predicted:** byte-identical at face age 0 (both terms zero), the
nose clear of the moustache from 0.25 up. **Measured:** all 105 snapshot
renders identical; `harness/detail/beard_nose.py` (Gero at 0 to 1, and
Gero, Daizen and Reinhard at their proposed ages) shows the nose above the
moustache everywhere and no jump. The cost: on a grown face nose and mouth
are closer, so the moustache's band over the lip is thinner than the
chibi's; it still reads as a moustache. 487 passed, 1 skipped.

### D3: the nose inside the beard (2026-09-27)

The owner, on the whole-figure before/after: mostly good, but the nose
collides with the beard. A beard ends between the nose and the mouth, it does
not grow around the nose. Cause: `_BEARD_TASH_Y` holds the moustache's top at
0.36 head radii, which is `_NOSE_Y` itself, and the nose and mouth drop with
the face build (`_MOUTH_REALISTIC_DROP`, to about 0.54 for the nose at face
age 1) while the moustache does not. Added to the plan under D3.

### D3: one Age slider (2026-09-27)

The owner's calls on the prototypes: **as built**, no longer chin and no
crease; the chin deferred and not touched. And, from a user's side, child to
adult to old is one slider: `CharacterParams.face_age`, 0 to 2, replaces
`face_maturity`. 0 to 1 is maturity (`Skeleton.face_maturity = min(1,
face_age)`); 1 to 2 applies `aged_face` at render time (in
`_eye_placement`, the one place that reads the fields it scales).
`presets.aged` keeps its name and now calls `character.aged_face`, the
numbers in one place. Web tool: "Age (child, adult, old)", 0 to 2, beside
the height.

**Measured:** all 105 snapshot renders identical to before the rename; a
test that `face_age = 1 + years` renders the same as `aged(face, years)` at
1; checked in the browser (the slider there, the face older at 1.5, the link
carrying `face_age`). 487 passed, 1 skipped.

**Not yet:** Chiyo, Daizen, Tenno and Gero still bake `aged()` into their
face at age 0; moved onto `face_age` they would also take the grown face.
The web tool ages them twice if a visitor slides their age up. That is the
presets step, with the owner.

### D3: the face maturity mechanism (2026-09-27)

`CharacterParams.face_maturity` (0 to 1, default 0) is carried on the
skeleton (`Skeleton.face_maturity`), which exposes `face_build = build +
maturity * (1 - build)`. Everything welded to the skull reads it instead of
`build`: the head's outline (`_head_pt` through `_head_shape`), the hair's
inner edge, the ears, the beard, the glasses' arms, the mouth. That reaches
the retired adult build's face terms, which were still in the code, running
at the chibi's pinned build. Maturity's own terms: the eyes lower
(`_MATURE_EYE_DROP` 0.06) and a nose growing in (`_nose`: the retired adult
build's two marks, measured off `ref/satoko-real.jpg`, their length, weight
and spacing scaled by maturity, so it never pops; nothing drawn at 0). The
hair's volume and the familiar's size stay on the figure's own build.

**The study** (`harness/detail/maturity_study.py`): 0.5 read as a teen or a
young adult; with height 1.3 it is the first figure that reads grown rather
than a child's head on a long body. At 1 the adult build's eye change
(openness down 40%, width down 21%) left an adult squinting, where the
reference keeps a large, open eye. The sweep in steps of 0.1 moves without
a jump. **The owner's calls:** the eye takes half of that change
(`_MATURE_EYE_SHARE`, through `_eye_build`), the skull and mouth all of
theirs; `aged()` stays a separate mechanism, but a user sees one continuous
slider (child to adult to old), so the two become one "Age" slider, 0 to 1
maturity and 1 to 2 `aged()`; the chin and the crease as prototypes first.

**Ears under long hair.** From maturity 0.4 the ear showed under all three
long cuts: their side locks were fitted to the chibi skull and meet the face
at maturity 0; a narrower face opens a gap between lock and jaw (measured:
0 to 2 px of ear at 0, 94 to 225 px at 1). `Hairstyle.covers_ears` on the
three long cuts, and `_ears` draws nothing under them. At maturity 0 that
removes the hidden ear's six paths from every long-haired render (checked:
with the flag off every snapshot render is byte-identical to before, and
each changed render lost exactly six paths and gained none); the 2 px
sliver it leaked on `long_traced` is gone with it.

**Measured:** at maturity 0 the eye share leaves every render
byte-identical (the flag-off check above); `ref-out/` refreshed (10
changed: the eight long-haired presets and the two sheets); 485 passed, 1
skipped.

### D3: the chin and crease prototypes (2026-09-27)

`harness/detail/maturity_proto.py` patches `_head_pt` (the chin's drop
plus `extra * maturity`) and `_eye` (a crease over the outer half of the lid,
its weight growing with maturity). Seen: **+0.10** gives a longer, adult
lower face, and Gero's beard follows it; **+0.20** reaches the reference's
chin but the chin starts to cover the collar and the tunic's V, so the neck
reads short; **the crease** reads like the reference's lid line and is
light at 0.5. With the owner.

### D2: the men's lash (2026-09-27)

The owner's call: `FaceStyle.lash` (default 1.0) scales the lash's outer
thickness above the inner one and the flick's length; `presets.MAN_LASH =
0.4` on every man (Satoshi, Tomohiro through him, Daizen, Haruto, Reinhard,
Tenno, Viktor, Gero) and the male base. A web tool slider, "Lash (soft to
winged)", 0 to 1. **Predicted:** only the nine male figures change, in all
four snapshot states each. **Measured:** exactly those 36 of 105 snapshot
renders changed, the rest byte-identical; by eye, a firm upper line and no
wing on all of them. 482 passed, 1 skipped.

**For D3:** `presets.aged(face, years)` already reads a face older by
walking the eye's size, width and openness down and the brows' weight up
(Chiyo, Daizen, Tenno at the full amount). Face maturity overlaps it; D3's
study has to decide whether maturity replaces `aged`, builds on it, or is
kept apart from it (maturity as adult against child, `aged` as old against
adult).

### D2: the eye built (2026-09-27)

`_eye` draws variant D: the aperture filled white and unstroked; the
iris's top in a darker band (`_IRIS_BAND_CUT`, `_IRIS_BAND_SHADE`); a faint
lower edge (`_interior_w(sw, 0.8)`); a short lower lash over the outer half
of the lower lid's outer curve; the upper lash as a filled band
(`_eye_lash`: `_LASH_INNER` 0.05 to `_LASH_OUTER` 0.24 eye radii, the
flick `_LASH_FLICK` 0.40 at `_LASH_FLICK_ANGLE` 28 degrees). The aperture's
four quadratics now come from one place, `_eye_quads`, which `_eye_shape`
and the lash both read.

**Predicted:** pixel-identical to the study's D; every render changed only
inside the eyes. **Measured:** zero differing pixels against the study's
candidate on all five study cases; all 105 snapshot cases changed, none
outside a box of the eyes (`eye_y - 1.6 r` to `eye_y + 1.4 r`, eye radii).
One test read the iris band's arc radii as a point (`A 11.78 11.78`) and
now skips arc radii. `ref-out/` and the bases refreshed; 479 passed, 1
skipped.

**Seen:**

- The glasses sit cleanly over the lash; the closed eye is unchanged (a
  thinner line than the open lash: a blink would jump, which matters only
  for animation; noted for it).
- **On the men the flick reads as winged eyeliner**: Satoshi, Daizen and
  Tenno have narrow, sharp-cornered eyes and the wing dominates them.
  `harness/detail/lash_men.py` scales the lash's outer thickness and the
  flick: at 0.6 the wing is small, at 0.3 gone and the upper line still
  firm. **Owner question:** a `FaceStyle.lash` knob (default 1.0, the women
  as now), the men at about 0.4?

### D2: the eye study (2026-09-27, at 2736cb6)

`harness/detail/eye_study.py` stands candidates in for `_eye`, keeping the
aperture and the iris and changing the lining: A today; B a filled lash
along the lid (thin inner, thick outer, a flick past the corner), a short
lower lash at the outer corner, the lower edge unlined, the iris's top in a
darker flat band (`shade(eye_color, 0.68)`); C B plus a faint lower edge
(`_interior_w(sw, 0.8)`); D C with a heavier lash (0.24 eye radii at the
outer end, against 0.16) and a longer flick; E C plus a crease over the
outer half. On Katherina (amber), Krista (teal), red eyes on dark skin, and
Katherina "hollow" and "sorrow"; and at the smallest insert size.

**Seen:**

- **B fails**: without a lower line the white under the iris bleeds into
  pale skin, worst with the lids lowered. The reference gets away with it on
  a face drawn at a larger scale with a shaded lid; we cannot. C, D and E
  keep the faint line.
- **The iris band reads** on all three palettes, the red one included.
- **D is closest in spirit** to the reference: the lash reads as the one
  heavy line in the face, as there, and the flick shows. At the insert size
  it still reads as a darker lash line.
- **E's crease crowds our brows**, which sit at `eye_y - 1.30 * eye_r`, and
  at the insert size crease and brow merge into a double brow. A crease
  belongs with higher brows, which face maturity (D3) may bring.

**Recommendation: D, without the crease** (the crease revisited in D3).

### D1: the line weights built (2026-09-27)

The owner's pick: outlines at 0.75 of the old weight, interior lines at
0.55. `_stroke_w` keeps the old weight, since 18 places size geometry off
it; the drawn weight goes through `_outline_w` and `_interior_w`
(`_OUTLINE_SCALE`, `_INTERIOR_SCALE`), all 100 drawn sites classed by hand:

- **By meaning, not by the study's value rule.** An outline is a part's
  edge at whatever fraction it was drawn (the hands, cuffs, pouches, belt
  pieces, strap, robe front, the eyes' aperture and the brows); an interior
  line divides or decorates inside a part. So those edges come out 0.75 of
  their old weight where the study showed 0.55.
- **Kept**: the bust mask's widening stroke and the goggles' rim (a band
  sized off the lens).
- **Filled lines** (the bust fold, the bare breasts' line, the male chest
  lines) take the outline scale in their width: they meet the body's
  outline and have to match it there.
- **Every geometry use of the weight is untouched**, including the offsets
  that tuck a fill under a line (the bust over the arms, the arm's joint
  cap, the bare foot's ankle patch, the belt).
- Drawn weights print to two decimals now, not one, which cost up to 8% on
  the thinnest lines.

**Predicted:** with `stroke-width` stripped every SVG identical but the
three filled lines; the stroke ratios at 0.55 and 0.75, and 1 on the kept
sites. **Measured** (`harness/detail/d1_check.py` over two snapshot runs):
the only geometry changes are those filled lines and the coat-bust masks
whose content-hashed ids hold the bust line; ratios 0.53 to 0.56 and 0.72
to 0.77 (the old values' one-decimal rounding), 1.00 on 29 strokes. By eye
(`harness/detail/d1_look.py`): the whole figure lightens evenly; at 4x the
bust over the arm, the base layer, the belt, the hand and the bare foot show
no gap or overhang. `ref-out/` and the bases refreshed; 479 passed, 1
skipped.

**Seen, not caused by D1:** a short grey vertical mark at the bottom of
Keiko's coat-at-the-arm zoom, before and after alike. Left for D6.

### D1: the line-weight study (2026-09-27, at 9079ad7)

`harness/detail/line_weight.py` rescales only the drawn `stroke-width`
attributes (geometry untouched, as the change will be), silhouette strokes
(within 5% of `_stroke_w` or above) and interior strokes separately, on
Satoko, Krista, Keiko (a white coat on a light card, the worst case) and
Katherina. Variants (outline, interior): (1.0, 1.0) today, (0.75, 0.75),
(0.6, 0.6), (0.75, 0.55), (0.6, 0.4).

**Predicted:** (0.6, 0.4) closest to the reference at full size; at the
smallest size, 1x, the 0.6 outline goes faint.

**Measured, by looking:**

- Full size: (0.6, 0.4) reads closest to the reference, as predicted.
- Smallest size, 1x (`line_weight_small_zoom.png`): every variant's
  silhouette still reads, since the flat fills carry it; the prediction
  was wrong there. What fades is the interior: at 0.4, Keiko's lapels and
  glasses frame and the hair strands go near-invisible grey. At 0.55 they
  hold.
- **The reference's own weight**, measured on its chin line (a dark run of
  2 to 3 px across columns 610 to 665) at the calibrated 83.9 px per head
  radius: about 0.030 head radii, 0.70 of ours. Its finger lines measure
  the same.

**Recommendation: (0.75, 0.55).** It is within 7% of the reference's
measured line, and the interior survives the smallest view. (0.6, 0.4)
looks lighter still at full size but loses the interior in the chapter
inserts.

### The second eye style retired (2026-09-27)

`_eye_anime`, its `eye_glow` knob, the `eye_style` field and the
`EYESTYLES` registry are gone; `_eye_realistic` is now `_eye`, the one eye
D2 redraws. The web tool's eye style select went with the catalogue entry;
an old link carrying `eye_style` or `eye_glow` loads with the one eye
(`urlstate`, tested). **Predicted:** every render byte-identical, since no
preset used the style; the suite at 483 minus the 6 eye-style tests plus 2
old-link tests. **Measured:** `harness/tall_chibi/snapshot.py`, 105 renders
`cmp`-identical to the committed tree's (its two `eyes.*` cases dropped);
`./refresh-ref-out.sh --check` matches; 479 passed, 1 skipped.

### D0: the line-weight inventory (2026-09-27)

Full list: `docs/detail-inventory/strokes.md` (a Sonnet delegate's read,
109k tokens; its UNSURE classes are marked there). 105 `stroke-width` sites
plus 18 places the weight is used as geometry:

| class | sites | multipliers of `_stroke_w` |
|---|---|---|
| silhouette | 53 | 1.0 on 37; 0.7 to 0.9 on the rest |
| interior | 44 | 0.4 to 0.7 mostly; 1.0 on 2 |
| feature (eyes, brows, mouth, glasses) | 11 | eyes 0.85 (`_EYE_OUTLINE_W`); brows from `FaceStyle.brow_weight` |
| geometry, not ink | 18 | offsets, radii, thresholds, clamps |

What it means for D1, checked by reading:

- **Interior lines are already split off by a factor** almost everywhere, so
  "lighter silhouette" and "lighter interior" are two separate levers: the
  base in `_stroke_w`, and the interior factors.
- **The weight doubles as geometry in 18 places**, and not all of it should
  follow a lighter line. Offsets that cover or meet a drawn stroke (the bust
  over the arms, the arm joint cap's half stroke, the bare foot's ankle
  patch, the body inset under a garment) should follow the ink. Sizes and
  thresholds should not: the navel's size, the placket button's radius, the
  underskirt's and hakama's pleats (drawn only when wider than four
  strokes), the crystal spacing, the staff's and familiar's canvas clamps.
  D1 therefore gives the ink its own weight and keeps the current value for
  the geometry that must not move, site by site.
- **`hat_hair_margin`** allows for the stroke with a literal 0.06 head
  radii, not `_stroke_w`. A lighter line leaves it generous, which is
  harmless and keeps the canvas; leave it.
- **Existing lighter silhouettes**: the robe front (0.7), several at 0.85.
  A lighter base would make them lighter still; D1's study checks they
  still read.
- **Not tracking the weight**: the goggles' lens rim (from `lens_r`) and the
  staff crystal's outline (full weight on a small shape).

**The owner's answers (2026-09-27):** retire `_eye_anime`; commit as each
step lands with the usual one-liners.

### D0: the baseline (2026-09-27, at 7b8a2f7)

**Calibration** (`out/detail/calibration.txt`). Our face (Katherina, the
hat off, the skin component): widest visible row at 0.446 head radii below
the head centre, half-width 0.852, chin at 0.987. The reference's face
component: widest row y 330, x 564 to 707, chin y 399.

- Scale from face width: 83.9 px per head radius; the reference's head
  centre at (636, 293).
- Scale from the widest row to the chin: 127.7. They disagree by 52%, by
  design: at one face width the reference's chin is at 1.26 head radii
  against our 0.99, a longer lower face ending in a point. That is D3's
  direction (a chin that drops and narrows), not a calibration fault.
- The review's by-eye crop (88 px) was 5% off; the calibrated sheet is
  `out/detail/face_vs_reference.png`.

**The smallest view** (`out/detail/smallest.png`). `../valley_of_mist`'s
chapter inserts are `sheet.sh` sheets, up to four columns, 2576 px wide;
its reader (`.chapter-end`, `max-width: 40rem`) shows them about 600 CSS px
wide, a scale of 0.233. A tile scales the figure by `0.86 * 400 /
canvas_h`, so the head radius there is about 21 px at 1x (Satoko 21.6,
Katherina 20.3; the review's "13 px" was a guess) and today's line (0.0427
head radii) about 0.9 CSS px, 1.8 device px on a 2x screen. Halving it
leaves about 0.45 CSS px at 1x: D1's lighter weights must be judged at this
size first.

### D0: the face, body and hair inventory (2026-09-27)

Full list: `docs/detail-inventory/face-body-hair.md` (a Sonnet delegate's
read, 131k tokens); the load-bearing lines, checked by reading:

- **The realistic lerp is still in place, running at the pinned build.**
  `_head_pt` (the skull: `_SKULL_NARROW * build`, `jaw_pull = 0.20 * build`,
  `chin_drop = 0.05 * build`), `_eye_placement` (`eye_dx` and the eye's size,
  openness, width and corner scale with `sk.build`; `eye_y = cy + 0.16 r` has
  no build term), `_arms` (elbow and wrist taper by `0.15` and `0.34 *
  build`), `_legs_and_boots` (`taper = sk.build`). With `sk.build` pinned at
  0.1 each runs at a tenth. **D3 and D4b can drive these terms** from face
  maturity and height instead of drawing new shapes, keeping today's value
  at the default so the default stays byte-identical. The realistic values
  they lerp toward were measured off `ref/satoko-real.jpg`; D3's study
  decides how far along each the slider goes.
- **No nose exists anywhere**: D3's nose tick is new.
- **One hand shape**, `_hand`, a mitten with a thumb bump ("still no
  fingers"); props sit over it at `_hand_centre`.
- **`_KEEP_WS` holds all eight width fields** and `stretched()` rescales
  them with `head_r` only; D4a's follow-through goes there, and the hands,
  feet, belt, skirt and torso all read those fields, so they follow free.
- **Every hairstyle already draws strands** (open quadratic chains as thin
  strokes); `long_traced` has the fewest (4), `short_crop` the most (10).
- **`_eye_anime`**: no preset uses it, but the catalogue's eye style option
  lists it and two tests iterate `EYESTYLES`; retiring it is three small
  touches. An owner question for D2.
- **Discontinuities**: `eyes_closed`, `scar_side`, `eye_style` switch by
  design; no stray thresholds in the face.
