# Adult body plan

A new body type for an adult woman, about 6.4 heads tall, drawn in the same flat, hard-edged style as the tall
chibi. Written 2026-10-17 at the owner's request. The record is `adult-body-status.md`.

The first character is Franzi (original, adult), with references in `ref/franzi/` (five images on one canvas,
Grok segment layers, a measured proportion table). An earlier adult-body attempt failed for want of references and
because the shapes drifted from them. This plan exists to stop that second cause: every shape is checked against a
number before anyone judges it by eye.

## Owner's decisions (2026-10-17)

1. A **separate body type** in `BODY_TYPES`, not a mode of the chibi and not a second build slider.
2. **SFW, always.** Clothing, swimwear and underwear are fine. No nipples or other sensitive parts anywhere. The
   bare view exists only as a harness for checking shapes (`harness/`), shows no sensitive parts either, and is never
   a web tool option.
3. Every figure is at or above `ADULT_FACE_AGE` (21). The guard lives in the render code, not in a form field.
4. The owner confirms visually at the checkpoints below, and is called only after the agent review has passed.

## Invariants

- **Every existing render stays byte-identical** at every step: the body type is an addition. The TypeScript tests,
  `./refresh-ref-out.sh --check`, `./refresh-bases.sh --check` and the frozen Python suite all stay green with no
  fixture edited. The new body type stays out of the web catalogue until stage 7, so `./refresh-catalogue.sh --check`
  stays strict until then. (Editing the catalogue fixture at stage 7 is a deliberate change and needs the owner's say.)
- Shapes read `sk.*` anchors, never pixel coordinates. Flat color, no gradient, no shading plane across a garment.
- Python in `src/` is frozen. All new code is TypeScript in `ts/src/`, harness scripts in `harness/franzi/`.

## The target and the gates

`harness/franzi/measure.py` writes `out/franzi/target.png`, the fused silhouette (refs 1 to 3 to the mid-thigh crop,
ref 4 below, thighs widened to meet), and `measurements.json` (row widths in head heights below the chin).

**G0, the silhouette gate** (`harness/franzi/gate.py`, built in stage 1). Render the figure in its underwear layer
only, no hair, no garment, rasterise, take the neck-down silhouette, scale it so chin to sole matches the target and
compare:

- silhouette IoU against the target, neck down: at least **0.93**;
- width at the landmark rows (shoulder, waist, hip, thigh, knee, calf, ankle): each within **5%** of the target;
- landmark heights (shoulder, waist, hip, crotch, knee, ankle) each within **0.05 H** of the target.

The thresholds are fixed here, before any shape is tuned, and are changed only with a note in the status file and
the owner's say. A gate that fails is a finding about the shape, not about the threshold.

**G1, the control gate.** Typecheck, `npm test`, the three refresh checks, `uv run ruff check .` and `uv run pytest`,
all green and no fixture edited. Run after every stage.

**G2, the agent review.** A read-only `sonnet` agent is given the renders, the references and a defect checklist
(stage-specific, listed below) and returns file:line or image-region findings, each marked OBSERVED or INFERRED. It
may not modify anything. Findings that are real are fixed and the review is repeated until it reports nothing. Only
then is the owner called.

**G3, the owner.** One message per checkpoint: a side-by-side image, the gate numbers, and what to judge. The
owner's answer is recorded in the status file.

## Stages

Each stage: write the predicted gate numbers in the status file first, change one thing, measure, record the gap.

| stage | work | gates | owner |
|---|---|---|---|
| 0 | Plan, status and strategy files. Fused target and measurement table (done). | n/a | no |
| 1 | `gate.py` and the harness render of the underwear layer. Run it on the chibi first as a control that must fail loudly, so the gate is known to work. | G0 harness works, G1 | no |
| 2 | **Profile.** An `adult_female` entry in `BODY_TYPES` (`heads` near 6.4, a head scale chosen from the reference head, landmarks from the measurement table). No new drawing code: the existing limb and torso code on the new anchors. Chibi, tall_chibi and the rest untouched. | G1, anchors within tolerance of the table, G2 (anchors and proportions) | no |
| 3 | **Torso and limbs.** Waist, hips, thigh gap, shoulder and neck shapes, limb taper, knee and calf, so the underwear-only figure matches the target. This is the stage where the last attempt drifted, so each change is one anchor or one curve, measured by G0. | G0, G1, G2 (silhouette defects: kinks, lumps, asymmetry, self-intersection, limb joins) | **Checkpoint 1**: silhouette over target, plus the figure in its underwear |
| 4 | **Bust, swimsuit and underwear.** The bust shape under cloth, a one-piece, a two-piece. A garment never shows more of the body than the always-worn underwear does. A test asserts that the new render paths draw no skin-tone detail inside a garment. | G0, G1, G2 (coverage and nothing anatomical), the new coverage test | no |
| 5a | **Head and face, only after stages 3 and 4 are signed off.** A proper adult head for Franzi traced from the new references (`00-base-dirndl.png`, the segment layers for hair and eyes), not the chibi head merely scaled down: skull and jaw, neck join, eyes, brows, nose, mouth, ears. Face maturity at or above the floor. If the existing face code cannot reach the reference, the head becomes a new face style behind a neutral default, so no existing character moves. | G1, G2 (face centred, eyes level, jaw and neck join, head to body scale) | no |
| 5b | **Hair.** The black ponytail and fringe from the hair segment layers, via the `trace-reference` skill, fitted to the new skull. A new `Hairstyle` entry, no change to the existing ones. | G1, G2 (hair meets the skull, no gap, symmetry) | no |
| 5c | **Hands and feet.** Hands from `ref/franzi/hands/` (relaxed first, the other poses only if a garment or prop needs them), bare feet from the segment layers, both at the 6.4-head scale. | G1, G2 (finger and toe count and proportions, wrist and ankle joins) | **Checkpoint 2**: Franzi in underwear, front, beside ref 1 and ref 4, head, hands and feet included |
| 5d | **The Franzi preset** in `presets.ts` (black ponytail, yellow-brown eyes, the adult floor). | G1, G2 | no |
| 6 | **Garments.** The dirndl (blouse, bodice with lacing, apron), the blouse and shorts, traced from the segment layers one garment at a time. The `trace-reference` skill applies, with the rule about nothing below the chin traced off a body that is not ours, which here is satisfied because the references are on this body. | G1, G2 per garment (hem, seams, overlaps, colour), IoU of each garment against its segment layer | **Checkpoint 3**: the dirndl and one casual outfit |
| 7 | **Guard, tests, catalogue, web.** The age floor enforced in the render code for the adult body, the rules tests (no bare option, no sensitive parts, floor holds for any preset built from outside), the catalogue entry and the refresh of its fixture, CLAUDE.md and README amended, version raised on `dev`. | G1 plus the new rules tests, G2 on the web tool at desktop and phone width | **Checkpoint 4**: sign-off for release. Merging to `main` and the tag stay the owner's call |

### G2 checklists

- Stage 2: anchors in order top to bottom, no negative width, head scale and body consistent, chibi unchanged.
- Stage 3: left and right symmetry, no kink or flat spot on a curve, hip to thigh and knee to calf joins smooth,
  nothing outside the target by more than the tolerance, limbs not detached at the shoulder or the crotch.
- Stage 4: the garment covers no less and shows no more than the underwear, no seam gap, strap and neckline
  symmetric, nothing drawn that is not a flat garment edge.
- Stage 5a to 5d: face centred on the head, eyes level, hair meets the skull with no gap, hands and feet in the
  right places, five fingers and toes in proportion (or the mitten convention used elsewhere), head to body scale
  matches the 6.4-head reference.
- Stage 6: each garment edge on the body line, overlaps in the right order, hem level, colours from the palette, no
  second tone across a garment.
- Stage 7: every control present and working, the floor cannot be set below 21 from the form or from a link.

## Risks

- **The head.** The existing head and face are drawn at the chibi build and scaled with `head_r`. At 6.4 heads the
  head is small. If the chibi face does not read as adult on it, stage 5 needs face work, and that is the largest
  unknown. It is measured first (stage 2 renders the head at the chosen scale) so it does not arrive late.
- **Ref 4 is a different generation** (hips about 6% narrower, thinner legs). The fused target already corrects the
  thighs; the hip width takes ref 1, and ref 4 is used for length only.
- **Silhouette widths cannot see the bust**, because the arms merge with the torso. Stage 4 is judged by eye against
  the swimsuit and bodice images at checkpoint 2.
- **Byte-identity of the old figures** is the cheapest way to detect an accidental global change, so G1 runs at the
  end of every stage and not only at the end of the campaign.

## Agents

Read-only diagnosis and the G2 reviews go to `sonnet` (the orchestrator skill's table). Shape decisions, anchor
choices, the status file and any commit stay with the orchestrator. Every `Agent` call sets `model` explicitly and
names the paths it may not modify. One stage's review is one agent; a delegate above about 100k tokens is a sign to
split the next brief.
