# Satoshi tall-chibi plan

Written 2026-09-20 at the owner's request: `--body tall_chibi` on Satoshi
(`out/satoshi_tall_chibi/base.png`) reads wrong, and the owner fed that render
through an image model to get a traceable target,
`ref-local/satoshi-tall-chibi/satoshi-tall-chibi.jpg` (not `ref/`, and not
consulted for the AI-generated-reference retirement `CLAUDE.md` records for
the fourteen presets: this is a fresh, owner-directed comparison for a body
type gap, the same kind of work `katherina-clothes-plan.md` did off a
different reference). Two separate problems, not one:

1. A rendering bug that clips Satoshi's hair against the canvas top, which by
   itself makes the head read oversized.
2. `tall_chibi`'s proportions, measured once off Katherina's reference alone,
   may not be the right numbers for every wearer.

They need different fixes and are not to be conflated: fixing (1) is a
correctness bug with no visual trade-off; (2) is a design decision that needs
looking at, not calculating.

## What is wrong now, measured and looked at

Side by side at one head scale (`out/satoshi_tall_chibi/base.png` next to the
reference, normalized to the same crop height):

- **Hair clips flat against the canvas top.** Root cause: `skeleton_for()`
  (`character.py:3098`) builds the `tall_chibi` skeleton's headroom off
  `heads=3.47` (`build_skeleton`'s margin formula gives ≈0.61 there), but the
  hair itself always draws at the *chibi* build — `BodyProfile.applied` pins
  `sk.build` back to the chibi value (`skeleton.py:114`) precisely so the face
  and hair keep their chibi style — and the chibi build wants ≈0.71 of
  headroom. Katherina's witch hat hides the gap: `hat_hair_margin` floors her
  margin well above either number. Satoshi's hat-less `short_crop` has no such
  floor, so it clips. Confirmed by re-rendering with a forced
  `min_hair_margin=0.75`: the clipping disappears and the head immediately
  reads smaller, closer to the reference, with no other change.
- **Legs and torso read shorter than the reference even once the clip is
  fixed.** Rough pixel measurement of the reference (face width at its widest
  row → head radius ≈173px; chin ≈451px to sole ≈1505px) puts it closer to a
  **4-head figure**, not `tall_chibi`'s measured 3.47. That profile
  (`character.py:3066`) was solved from one reference, Katherina's, on her own
  build's landmarks; nothing has yet checked whether those numbers generalize
  to a different figure. Treat "4 heads" as a hypothesis from a rough
  measurement, not a target: milestone T2 is where it gets checked properly.
- **Face shape (jaw, eye size) will not change from a body-profile fix
  either way.** `sk.build` stays pinned to the chibi value under any
  `BodyProfile`, so the face draws identically regardless of which body it
  sits on. The reference's narrower jaw and smaller eyes are a `FaceStyle`
  question, out of this campaign's scope, not something `tall_chibi` tuning
  can reach.
- **Not gaps:** the reference's extra hair-strand detail and the eyes'
  gradient shading are the image model's own embellishment against a hard
  style constraint (flat colour, no gradients, `CLAUDE.md`) and are not
  targets. The scar placement, belt height, and boot shaft/lace styling
  already read close; deferred rather than dropped, in case they move once T1
  and T2 land.

## Milestones

### T1. Fix the headroom bug

**Status: done, 2026-09-20.** `default_hair_margin(heads)` extracted from
`build_skeleton` (`skeleton.py`) so `skeleton_for` (`character.py:3098`) can
floor the profile skeleton's margin at the chibi build's own value, not just
`hat_hair_margin(p)`: `margin = max(margin, default_hair_margin(heads))`
before building the tall skeleton. Satoshi on `tall_chibi` no longer clips;
the head reads smaller, closer to the reference, with no other change.
`refresh-ref-out.sh` reports all 37 renders unchanged, including Katherina
(both her default and `real/katherina`, confirming the fix is a no-op
wherever a hat's own floor already covered it). `ruff check`, `ruff format
--check`, `pytest` (438 passed) all green.

- [x] **T1a.** In `skeleton_for` (`character.py:3098`), compute
      `min_hair_margin` for the profile skeleton off the chibi build's own
      margin, not `profile.heads`'s. Landed as an additional floor alongside
      `hat_hair_margin`, not a wholesale replacement, so a profile taller
      than chibi with a hat needier than the chibi margin still keeps the
      hat's floor.
- [x] **T1b.** Render Satoshi on `tall_chibi` and confirm no clipping, by eye
      and by checking the topmost hair pixel stays inside the canvas with
      margin to spare.
- [x] **T1c.** Re-render Katherina (both her default and `--build realistic`,
      which does not take this path) and confirm byte-identical; `ref-out`
      snapshot test is the check (`refresh-ref-out.sh` reports no unintended
      changes).
- [x] **T1d.** `ruff check`, `ruff format --check`, `pytest` green.

### T2. Experiment with proportions before deciding anything

Not a calculation: render variants, look at them beside the reference, and
let the owner pick. The open question is whether one `tall_chibi` profile can
serve both a Katherina-shaped figure and a Satoshi-shaped one, or whether the
name is really "Katherina's proportions" and a second, male-leaning profile is
needed.

- [ ] **T2a.** A small harness script (`harness/body/`, same pattern as
      `landmarks.py`/`measure.py`) that measures the *reference*'s own
      landmarks (chin, shoulder, waist, hip, hem, knee, ankle, sole; leg
      half-width) in head radii, the way `tall_chibi` was originally solved
      from Katherina's. This turns the "maybe 4 heads" hypothesis above into
      real numbers, the same rigor the existing profile has.
- [ ] **T2b.** Render Satoshi at a few candidate profiles side by side with
      T1 fixed: `tall_chibi` unchanged (baseline), a profile solved from
      T2a's measurement, and one or two hand-nudged points between them if
      the solved one overshoots. Compare against the reference and against
      plain chibi Satoshi, since the goal is "looks like a taller reading of
      the same character," not "matches the reference pixel-for-pixel."
- [ ] **T2c.** Render Katherina against every candidate too — a profile that
      only looks right on Satoshi is not a fix, it is a new problem.
      `out/`-only comparison sheet, not a committed change yet.
- [ ] **T2d.** Owner's call, informed by T2a-c: keep one shared `tall_chibi`
      tuned to split the difference, or add a second named profile (e.g.
      `tall_chibi_male`, naming pending) and decide by eye which characters
      want which. If it splits, the catalogue's body-type list
      (`catalogue.py:474`) and `docs/katherina-clothes-plan.md`'s
      `_GARMENT_REF_BODY` assumption (garments traced in `tall_chibi`'s head
      radii, mapped by the shared landmark set) both need checking against
      whichever profile(s) survive.

**Held until T1 and T2 land:**

- **T3.** Re-measure and resolve whichever profile(s) T2 lands on, the same
  way `tall_chibi` documents its own derivation (`character.py:3066`'s
  comment is the template).
- **T4.** Boot/toe silhouette — the reference's toe is more tapered than
  ours; minor, and shape work on a skeleton that is about to move is wasted
  work.
- **T5.** Anything else the reference suggests, deliberately not itemized yet:
  looking closely at cosmetic gaps before the proportions are settled invites
  fixing them on the wrong body.

## Acceptance

- T1: no clipping on Satoshi, no regression on Katherina, tests and lint
  green.
- T2: not a metric, an owner sign-off. Bring renders, not a recommendation
  framed as already decided.

## Risks

- **Retuning a shared profile moves Katherina too.** Any change to
  `BODY_TYPES["tall_chibi"]` itself (as opposed to adding a second profile)
  reopens `katherina-clothes-plan.md`'s traced cuts, which were fitted to
  `tall_chibi`'s exact landmarks and treat the identity mapping on it as
  their correctness check. If T2d splits the profile instead of retuning the
  shared one, this risk doesn't apply.
- **The 4-head hypothesis is a rough pixel measurement**, not a calibrated
  trace (no known head-radius calibration exists for this reference the way
  the witch hat gave one for Katherina's). T2a's harness measurement is what
  makes it trustworthy; nothing downstream should be solved from the number
  in this doc.
