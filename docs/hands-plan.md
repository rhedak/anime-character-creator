# Hands plan

Settle how the tall chibi's hands are drawn. Today every preset wears the
mitten because the traced hands (D4d, `detail-plan.md`) did not work by eye.
This plan tries every way forward the audit of 2026-10-08 found, puts each in
front of the owner as a candidate, and lets the owner pick. Written 2026-10-08
at the owner's request; the audit that motivates it is the first entry in
`hands-status.md`.

The record is `hands-status.md`. The procedure is the one the last campaigns
used (`detail-strategy.md`): predict before measuring, one change per
measurement, study before building, only the owner signs off, one-line
commits without a trailer.

## Why

The audit (`hands-status.md`, "Audit, 2026-10-08") measured the traced relaxed
hand against the mitten on all 19 presets:

- It is 1.7 times as long (0.50 head radii against 0.29), narrower, and taller
  than wide (height over width 1.63 against 0.78).
- 45% of its pixels are outline, against 26% for the mitten.
- At the smallest consumer size (head radius about 21 px) it collapses into
  thin dark ticks, where the mitten still reads as a hand.
- Dropping its fingertip pieces and interior lines barely changed that
  (45.0% to 42.9% ink), and widening it did not fix the look. The silhouette is
  the problem, not the detail on it.
- The traced grip on Katherina's staff reads well. It is the one traced hand
  that works.

Separately, the code never grew the registry the D4d plan promised: there is
`HAND_STYLES` and two hardcoded pose constants, the grip is tied to
`side == -1 and staff_color`, no preset sets `hand_style`, and nothing guards a
hand's size or legibility.

## What is tried

Every proposal from the audit is built as a candidate, so the owner chooses by
looking rather than by argument.

| id | candidate | what it is |
|---|---|---|
| M | the mitten | today's default, kept as the baseline and the fallback |
| S | shrink and simplify the traced hand | a cheap control: the existing traced relaxed hand brought to the mitten's footprint and given fewer, heavier features. Expected to fail; it tests the footprint gate |
| W | the traced hand stretched wide (added after V1) | the traced relaxed hand at the gate's height, stretched across 1.6 and 2.0 times so it fills the arm. Added when the owner said the hands need to be wider; a per-axis scale, so a hand authored on its own terms, not a faithful trace |
| W3 | W2 with a square wrist, tips dropped | W2 with the traced outline's bevelled wrist replaced by a square cross-cut and the fingertip slivers and interior lines dropped (added after the owner's note on the transition) |
| K | constructed hands | drawn in code from the skeleton, no reference: a mitten with finger notches, a mitten with finger strokes, a half-closed relaxed hand |
| T | traced from a chibi-body reference | the hair method: the owner generates a hand reference on our tall-chibi body, it is gated, traced and built |
| G | the grip | kept, then fixed (owner's decision 2026-10-08: keep every hand as an option, and make the traced fist a proper fist; built as G1, the canon-style constructed fist, and G2, G1 kept upright against the arm's swing): either hand, a tube sleeve, and a study of the elbow |
| R | the registry | `HAND_POSES`, a pose per side, a guard test |

## Invariants

- **Defaults stay byte-identical.** Every new field and registry entry at its
  default leaves every render unchanged: `./refresh-ref-out.sh --check` and
  `harness/tall_chibi/snapshot.py` compared with `cmp`, the before taken from
  the committed tree with `git stash`. A step that deliberately changes
  renders says so and shows before and after.
- **Flat colour, hard edges.** No second tone across skin, as in `CLAUDE.md`.
- **Continuous, for later animation.** A pose parameter moves shapes
  continuously. Nothing pops in at a threshold.
- **Skeleton-relative.** Hands size off the skeleton, never off pixels.
  Traced hands map by one uniform scale, never per axis.
- **Legible at the smallest consumer size.** Every candidate is judged at full
  size and at the chapter-insert size (head radius about 21 px).
- **Nothing downstream moves mid-campaign.** `../valley_of_mist` and the covers
  are regenerated only at a checkpoint the owner picks.
- **No commits unless the owner asks.** One line, no trailer.

## The footprint gate

A candidate hanging hand has to pass a measured gate before the owner sees it,
so the owner's time goes to hands that are in the right range. The numbers come
from the mitten's measured footprint and are the owner's to change.

| measure | mitten (measured) | gate (proposed) |
|---|---|---|
| bounding-box height, head radii | 0.34 | 0.30 to 0.42 |
| height over width | 0.78 | 0.70 to 1.20 |
| outline share of the hand's pixels | 26% | at most 35% |
| narrowest skin run in the fingers | n/a | at least 1.5 outline widths |
| width where the hand meets the arm, against the mitten's | 1.00 | 0.90 to 1.10 |

`harness/hands/metrics.py` (promoted from the audit's scratch script in H0)
prints these per candidate and per preset. The gate covers hanging hands only:
a hand gripping a staff is bigger on purpose and is judged by eye (V5, V6). The
gate is a filter, not a verdict:
passing it earns a place on the owner's sheet, and only the owner's look decides.

## Owner checkpoints

Visual confirmation is the core of this plan. At every checkpoint below I
produce the images, say where they are, say exactly what to look at, and stop
until the owner answers. The owner's answer is recorded in `hands-status.md`
with its date. Nothing after a checkpoint is built before it is answered.

**The standard sheet.** Every checkpoint that shows hands uses the same views,
so candidates compare like for like (after V0 the list grew to seven views;
items 6 and 7 are new):

1. Both hands cropped at 5x, on five presets that cover the range: Krista
   (plain drawn sleeve), Gero (coat), Satoko (apron and skirt), Keiko (lab
   coat), Katherina (wide traced sleeve, staff).
2. The upper body at chapter-insert size (head radius about 21 px), enlarged
   3x with nearest-neighbour so the pixels show.
3. Heights 0.8 and 1.3.
4. A dark skin tone.
5. An arm swung out 30 degrees.
6. Clothes off, on the two neutral bases, to see where the hand meets a bare
   forearm.
7. Katherina's two hands at 8x with the arm: the wide cuff and the staff.

Each candidate is a labelled column next to the mitten, so a pick is a letter.

**How the owner answers.** One of: *pick* a candidate (a letter), *reject all*
(with what is wrong, so the next round targets it), *adjust* (a named change to
one candidate, which I make and show again), or *defer*.

## The order

### H0. Baseline and tools (read-only)

- Promote the audit's scratch scripts into `harness/hands/`: `sheet.py` (the
  standard sheet for any list of candidates), `metrics.py` (the footprint
  gate), `ablate.py` (drop a piece or an interior line, widen the hand, and
  measure), with `handlib.py`, a candidate registry `candidates.py` and a
  `README.md`, listed in `harness/README.md`. **Done 2026-10-08.** The control
  held: the promoted scripts reproduce the audit's numbers exactly.
- Snapshot for the byte guard (`harness/tall_chibi/snapshot.py`, 114 renders
  in `out/hands/before`). **Done 2026-10-08.**
- Confirm `ref-local/` is present. **It was not** at first; on 2026-10-08 the
  owner pulled `ref/katherina/katherina_grok.jpg` into the repo and a copy now
  sits at the path the gate hardcodes (control passed, see `hands-status.md`).
  T needs two things from it:
  the existing `ref-local/katherina_grok/katherina_grok.jpg` (the gate's
  baseline, hardcoded in `harness/hair_audit/gate.py`, and the image the owner
  edits to make the new reference) and the new reference, which the owner makes.
  Optionally `ref-local/katherina_grok_real/katherina_grok_real.png`, to test
  the realistic-body cause. The sibling repos are not needed for T; they only
  matter for the regeneration at H6, if the owner asks. S, K and G need none of
  this.
- **V0, owner checkpoint: the baseline.** The standard sheet with the mitten
  and today's `traced` side by side, plus the metrics table. The owner confirms
  that this matches what they see, and says what is wrong in their own words
  (too long, too thin, too sharp, the crooked tips, something else), so the
  candidates are judged against the owner's complaint and not only my
  measurement. **Answered 2026-10-08:** too thin, almost skeletal; does not
  connect to the arms well (best seen with clothes off); on Katherina it does
  not fit and parts are missing, the fist. Those three are now the criteria
  every candidate is judged on, and the standard sheet gained two views for
  them: `v6_bare.png` (clothes off, on the neutral bases only, never a named or
  younger character) and `v7_katherina.png`.

### H1. Candidate S: shrink and simplify (a control)

- Prediction, written first: the existing traced relaxed hand, brought to the
  gate's footprint by one uniform scale and with its tips simplified, still
  reads as an adult hand because the silhouette (pointed, curled inward) is the
  trouble. It passes the footprint gate and fails by eye.
- Build it as a throwaway variant under `harness/hands/`, not in `src/`.
- **V1, owner checkpoint.** The standard sheet: mitten, today's traced, S. The
  point is a clean answer to "is it just size?". If the owner likes S, it
  becomes a real candidate. If not, the audit's claim that the silhouette is
  the problem is confirmed by the owner's own eye, not only by my numbers.

### H2. Candidate K: constructed hands

Drawn in code from the skeleton, in the style of `_hand`'s mitten, with no
reference. All three share the mitten's footprint, so they pass the gate by
construction. One change per variant:

- **K1, notched mitten.** The mitten with two or three small notches on the
  outer edge marking fingers, thumb kept.
- **K2, stroked mitten.** The mitten's silhouette unchanged, with two or three
  short interior finger strokes.
- **K3, half-closed hand.** A relaxed hanging hand, fingers loosely curled,
  built from a few constructed shapes, the pose the traced hand was meant to
  give.

Prediction, written first: K1 and K2 read as a hand at full size and are
indistinguishable from the mitten at insert size, which is acceptable. K3 is
the one that risks looking clenched, which is how the earlier fists read.
Features narrower than 1.5 outline widths drop out, which the gate checks.

- **V2, owner checkpoint.** The standard sheet: mitten, K1, K2, K3. The owner
  picks, rejects all, or names an adjustment. A pick here is a complete
  answer for the relaxed hand and H3 is then optional.

### H3. Candidate T: traced from a chibi-body reference

The method that fixed the hair (`detail-status.md`, D5): never map a hand off a
body that is not ours.

1. **The owner generates the reference.** Katherina on the tall-chibi body with
   the hands changed to relaxed, hanging, closed or loosely curled, and nothing
   else changed. I write the prompt and attach the rules it must satisfy
   (same body, same scale, hands in view, no prop in the way). Saved under
   `ref-local/katherina_hands_chibi/`. A few candidates, one picked by the
   owner by eye.
2. **The gate, before any tracing.** The same calibration check the hair used
   (`harness/hair_audit/gate.py`) adapted for hands: head scale, hem, soles and
   wrist width against `katherina_grok`. A failure means regenerate.
3. **Trace** with the `trace-reference` skill, one outlined shape per piece,
   fitted loosely enough that no feature is under two stroke widths, emitted by
   script into `character.py` between marker lines.
4. **Build** as a pose in the registry (R), mapped to the wrist by one uniform
   scale and mirrored per side.

- **V3, owner checkpoint: the reference.** The candidate images and the gate's
  numbers. The owner picks one or asks for more.
- **V4, owner checkpoint: the trace over the reference.** The overlay at zoom,
  so the owner sees whether each chain rides its line, then the standard sheet
  with the mitten, the best K and T.

### H4. Candidate G: the grip

Kept as the owner's one working traced hand, then fixed. Three studies, one
per question, each ending in a checkpoint:

- **G1, either hand.** The grip is tied to `side == -1`. Make the holding hand
  a property of the outfit (which side holds the staff) and mirror the grip
  per side. Byte-identical for Katherina. **V5:** Katherina with the staff in
  each hand.
- **G2, the grip against a tube sleeve.** Deferred in D4d: the grip's size
  against a plain cuff rather than Katherina's wide traced one. Test the grip
  on Krista, Gero and Satoko holding the staff. **V6:** the three, at 5x and at
  insert size, with the grip at the current 0.50 length and one size either
  side.
- **G3, the elbow (a study, not a build).** The deferred elbow would let a hand
  come in from the side. Prototype only what answers "is it worth building":
  one arm as an upper and a lower arm about an elbow on one preset, three
  angles. **V7:** the owner decides go (a separate plan), no-go, or later.

### H5. R: the registry and the guard

Built after the owner has seen the candidates, so the registry holds the poses
the owner actually keeps and nothing speculative.

- `HAND_POSES: dict[str, HandPose]`, each pose its outline, interior lines,
  front pieces, a grip point where it holds something, and its hand frame.
  The mitten becomes a pose, its path unchanged.
- A pose per side on `CharacterParams`, defaulting to what `hand_style` gives
  today, so every render stays byte-identical. `hand_style` stays as the
  shorthand.
- The held prop, not the side, decides which hand grips.
- **The guard test**, in `tests/test_smoke.py`: for every pose in the registry
  the footprint gate's first three measures hold at a chosen preset, and no
  feature is under 1.5 outline widths. A hand that grows or collapses fails the
  suite, which nothing does today.
- **V8, owner checkpoint: the preset assignment.** A table of every preset with
  the owner's chosen pose for each hand, rendered as the standard sheet. The
  owner confirms or changes each row. Only then do preset values change.

### H6. Close

- `ruff check`, `ruff format`, `pytest`, and `./refresh-ref-out.sh` only if
  renders changed on purpose.
- Docs: `hands-status.md` RESUME, `detail-plan.md`'s D4d entry pointing here,
  `CLAUDE.md`'s line on Katherina's hands, `docs/api.md` for the new fields,
  the web tool's Hands control.
- **V9, owner checkpoint: the roster.** Every preset at full size and insert
  size with its final hands, before anything downstream moves.
- Regenerate `../valley_of_mist` and the covers only if the owner asks,
  pixel-checked against the previous commit so only the hands change.

## Checkpoint summary

| checkpoint | what the owner sees | the owner decides |
|---|---|---|
| V0 | baseline sheet and metrics | confirms the complaint, names what is wrong |
| V1 | S against mitten and traced | is it just size |
| V2 | K1, K2, K3 against the mitten | pick, reject all, or adjust; may end the relaxed-hand search |
| V3 | the generated chibi-hand references | pick one or ask for more |
| V4 | the trace over the reference, then T against the best K | pick |
| V5 | the staff in each hand | confirm the mirror |
| V6 | the grip on three sleeve types, three sizes | the grip's size |
| V7 | the elbow prototype | go, no-go, later |
| V8 | the preset assignment table | which preset takes which pose |
| V9 | the whole roster, final | sign-off |

## Decisions and open questions

- **Where the answers live.** `hands-status.md`, dated, one line each.
- **The gate's numbers** are proposed and the owner's to change at V0.
- **T needs the owner's time.** Generating the reference is outside what I can
  do, and `ref-local/` has to be on this machine. If either is a problem, K and
  G run without it and T waits.
- **Order.** H0, H1 and H2 come first and are cheap. H3 starts only if V2 does
  not settle the relaxed hand. H4 can run alongside H2 and H3. H5 waits for the
  picks.

## Deferred

- **Other poses** (pointing, waving, holding a cup or a book) join the
  registry after R, traced or constructed. Not in this plan.
- **Animation.** Jointed limbs are a separate plan. G3 only decides whether an
  elbow is worth building.
