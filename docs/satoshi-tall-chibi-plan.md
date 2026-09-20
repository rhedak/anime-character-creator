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

**Status: done, 2026-09-20; T2d resolved by the owner (no new profile), below.**
`harness/body/satoshi_tall_chibi_landmarks.py` measured the reference (head
calibrated off the widest row of face skin, since unlike Katherina's this
reference has no prior trace-derived calibration — flagged as an estimate,
not trace-grade):

| landmark | measured | `tall_chibi` |
| --- | --- | --- |
| heads | 3.98 | 3.47 |
| shoulder_y | 0.965 | 1.13 |
| waist_y (belt) | 2.628 | 2.384 |
| hip_y (crotch — the only visible pelvis-adjacent landmark on a trouser leg) | 2.762 | 2.955 |
| ankle_y | 5.669 | 5.55 |
| sole_y | 6.959 | 5.94 |
| waist_half_w | 0.59 | 0.563 |
| leg_half_w | 0.253 | 0.23 |

`hem_y`/`hem_half_w` were left unmeasured: `tall_chibi`'s hem is a skirt hem,
which has no equivalent on a straight trouser leg, so the base lerp's own
values carry through in every candidate below.

`harness/body/satoshi_tall_chibi_variants.py` rendered three profiles (T1's
headroom fix applied to all of them) on both Satoshi and Katherina, to
`out/body_variants/` — a look, not a metric:

- **`baseline`**: today's `tall_chibi`, unchanged.
- **`heads_only`**: `tall_chibi`'s landmarks, only `heads` bumped to the
  measured 3.98. Tests whether a leaner head-to-body ratio alone, with no
  other shape change, closes most of the gap.
- **`measured`**: a profile built from the table above (`hip_y`, `hem_y` etc.
  left `None` where unmeasured, so those keep the base lerp).

Looked at (`out/body_variants/*_{baseline,heads_only,measured}.png`, and a
normalized crop beside the reference):

- **On Satoshi**, both `heads_only` and `measured` read far closer to the
  reference than `baseline` — smaller head, longer legs, no longer reading
  "toddler in adult's clothes." Between the two, `measured` tracks the
  reference's proportions more closely: its belt sits at close to the
  reference's own waist height (≈40% down the figure); `heads_only`'s belt,
  carrying `tall_chibi`'s own `waist_y` at the new taller `heads`, sits
  noticeably lower than the reference's.
- **On Katherina, both `heads_only` and `measured` break the fit**: her skirt
  hem no longer reaches her boot tops, exposing bare leg between them. This
  is exactly the risk this doc flagged going in — `tall_chibi`'s landmarks
  (and `katherina-clothes-plan.md`'s traced cuts, fitted to those exact
  numbers) are Katherina's own, and stretching `heads` without also moving
  her hem breaks what was already fitted. **Confirms a shared profile cannot
  serve both**: retuning `tall_chibi` itself is off the table, and this
  campaign should land as a second, additive profile that never touches
  `BODY_TYPES["tall_chibi"]` or anything that reads it.

- [x] **T2a.** Measurement harness, table above.
- [x] **T2b.** Three candidates rendered and looked at beside the reference
      and plain chibi Satoshi.
- [x] **T2c.** Same three candidates rendered on Katherina; both non-baseline
      candidates break her skirt/boot fit, confirming the split.
- [x] **T2d. Owner's call, 2026-09-20: no new profile.** Looking at the sheet,
      the owner found the **baseline `tall_chibi` proportions the most
      pleasing** and named the real problem: Satoshi's *upper body and
      arm/shoulder sections* look odd, not his proportions. Neither `measured`
      nor `heads_only` is adopted; `BODY_TYPES` is untouched. The harness
      scripts stay as the record of what was tried and why it was declined
      (and `measured`'s numbers stay in the table above, in case a taller
      figure is wanted later).

### T3. Shoulders and sleeves

**Status: done, 2026-09-20. The owner made it the default for everyone.**
Compared at one head scale from the neck to the wrists (reference first), the
gap is in how the cap sleeve meets the arm, not in any landmark: the vertical
structure already matches (cap tip 1.43 head radii against the reference's 1.40,
armpit 1.66 against 1.63, sleeve outer edge 1.07 at the top against 1.03 to
1.11). What differs:

- The cap's underside is a **flat horizontal shelf** in ours and a **slanted
  line, tip to armpit**, in the reference.
- Our tip stands 0.17 head radii past the arm's outer edge; the reference's
  overhangs by about 0.07, so ours reads as a shoulder pad wider than the arm.
- Our arm is a **square-topped tube** starting at the shelf, with its own thick
  top edge; the reference's sleeve **comes out from under the cap**, its outer
  edge running up beneath the tip.

`Outfit.sleeve_under_cap` (default `True`) draws it the reference's way: the tunic's tip is cut back to
`_cap_tip_x` (the arm's outer edge plus 0.07 head radii) with a small round on
it, the underside is a straight line to the armpit, and the arm's top edge
follows the same line (`_cap_underside_y`), so the two strokes land on each
other and read as one edge, the same trick the arm's top and the flat hem
already used. No z-order change, no overlay. Ignored under a traced jacket or a
traced sleeve, which draw their own shoulders. Catalogued as a "Sleeve under
cap" toggle on the tunic, so it can be tried in the web tool on `tall_chibi`.
Looked at on `tall_chibi`, the shared chibi and realistic (all three read
cleanly); judged against the reference on `tall_chibi` only.

- [x] **T3a.** The slanted cap, rounded tip and matching arm top, opt-in.
- [x] **T3b. Owner's call, 2026-09-20: on by default.** `sleeve_under_cap`
      defaults to `True`; `False` is the old flat shelf. 27 of the 37 `ref-out`
      renders changed (every chibi and realistic render with a plain tunic, and
      the cover and sheets); Katherina and anyone under a coat are unchanged,
      since a coat, a traced jacket or a traced sleeve draws its own shoulder
      and the flag is ignored there. Looked at across the whole roster at both
      builds against the previous renders: the caps read tidier, and at the
      realistic build the sleeve now comes out from under the cap closer to
      the canon than the shelf did. `../valley_of_mist` consumes these
      renders, so its references, cover and inserts need regenerating.
- [x] **T3c-i.** The tan line trimming the tunic's V, which the reference does
      not draw: `Outfit.neckline_trim` (default `True`, the canon's), off on
      Satoshi. Only his own renders, the cover and the sheets changed.
- [x] **T3c.** Neck and collar, 2026-09-20: `Outfit.neckline_stand`, **on by
      default for everyone** (owner's call, after a before/after sheet). A small
      tab rises on each side of the neck and the V's edges start on the neck's
      own contour, running 0.30 head radii deep, in place of a V that started
      inside the neck at the shoulder line. The neck itself was already the
      reference's width (0.28 against 0.26 head radii), so only the collar
      changed. It replaces the undersleeve trim on the V for everyone; a
      standing collar (`collar_color`) and a round neckline are unaffected.
      25 of the 37 `ref-out` renders and both bases changed; looked at across
      the changed roster at both builds. Remaining gap, left as is: our tabs are
      boxy steps where the reference's are small angled points, and our V is a
      little wider and deeper.
- [ ] **T3d.** The arms' outward flare (the reference's sleeve leans out about
      0.15 head radii over its length; ours about 0.11) and the torso's taper to
      the belt, if the cap alone does not close the look.

- [x] **T3e. Belt line, 2026-09-20.** `CharacterParams.waist_shift` (head radii,
      default 0; shifts the waist and hip lines together, so the belt and
      everything hung from it rides up or down while the shoulders, knees and
      soles stay put), a "Belt line (up / down)" slider in the web tool (-1.0 to
      1.5) and `--waist-shift` on the CLI, to experiment with the upper/lower
      body split. Satoshi's preset carries **`waist_shift=0.5`**, the owner's
      pick: a longer torso for the tunic, on `tall_chibi`. Measured, that puts
      the belt at 0.565 of crown-to-sole against 0.493 at 0 and the reference's
      0.456, with 0.418 of the figure below it against the reference's 0.530:
      a deliberate step away from the reference, not toward it. The hands
      hang from the hip line, so the arms lengthen with it.

- [x] **T3f. Experiment, 2026-09-20: `tall_chibi` as the default body for
      everyone** (`CharacterParams.body` defaults to `"tall_chibi"`; `None` is
      still the shared chibi, selectable). Committed on its own so it can be
      reverted alone. 17 chibi renders, both bases and the cover changed;
      realistic builds do not (a profile only applies at the chibi build) and
      Katherina is identical. Looked at across the roster: uniforms, coats,
      trousers and simple tunics read as taller, slimmer versions of the same
      character, with a much smaller head. What looks off: the waist sashes
      (Reika's, Daizen's) turn blocky, Chiyo's apron pouch becomes a tall narrow
      rectangle, tall boots (Krista, Viktor) read as knee-high, and the cover's
      Satoshi shrinks in the frame. All of those size themselves off the waist
      and hip bands `tall_chibi` moves and were only ever fitted on Katherina.
      Not judged yet: whether the smaller head costs too much of the chibi look.

- [x] **T3g. Tall boots, 2026-09-20.** With the lower belt, `sk.knee_y` on the
      tall profiles (Katherina's, set so her default shaft lands on her
      reference's boot top, under a skirt) sits *above the hip*, so
      `boot_shaft` "toward the knee" came up to the belt on the six
      tall-boot characters (Elara, Krista, Kyoko, Reinhard, Tenno, Viktor).
      `_boot` now aims the extension at a real knee, the lower of `knee_y` and
      mid-leg, and leaves the default shaft alone (Satoshi's and Katherina's
      boots are unchanged; so are the shared chibi and realistic builds, whose
      knee was already below mid-leg). The shafts now start about mid-calf.

### Open issues on the tall-chibi default

Found looking at the roster (`out/tall_default_roster_*.png`), taken one by
one; not yet fixed unless ticked above.

- [x] **Belts with a coat, 2026-09-20.** The belt was `waist_half_w * 1.03`
      wide over everything, but a coat's panels hang out to the arms, so on
      Tomohiro, Keiko, Kyoko and Gero it stopped short and read as a patch on
      the middle panel. Widening it to the arms fixed the gap and read as a strap
      laid across the coat, so the owner's call was **under the coat**: with an
      open coat the belt is drawn before it, and shows only in the opening. Tunic
      wearers and Katherina's traced belt are unchanged.
- [x] **Crystal harness, 2026-09-20.** Its four gems were spaced off the waist
      width and sized in head radii, so on the narrow-waisted body they crowded
      the centre and sat on the buckle (which is sized off the belt's depth, deeper
      there). The middle pair now stand clear of the buckle, the outer pair a gem
      beyond them, and the gems shrink (to about 0.9) only as far as it takes to
      fit inside the belt; the shared chibi keeps its old fractions and the
      realistic build is untouched (`out/crystals_before_after.png`). The pouches
      and the crystals also stopped recomputing the belt band with their own copy
      of the maths and take `_belt_band`, so they follow it.
- [x] **The trouser-corner notch, 2026-09-20.** On the narrow-waisted body the
      trousers hang 0.614 head radii wide at the top against the belt's 0.580, so
      their square corners stood out under the belt's rounded ends as a small step.
      The belt now reaches the trousers' outer edge on the chibi-range builds
      (`_leg_gap_and_top` is the width the legs use, pulled out so the belt can read
      it); the shared chibi's belt is wider than its legs anyway and is unchanged, as
      is the realistic build. The trade: the belt now overhangs the tunic above it by
      about 0.06 head radii a side (a few pixels at normal size), so it reads as a
      belt with some thickness (`out/trouser_notch_before_after.png`). The other
      way, narrowing the trousers' tops to the belt, would move the legs and the
      boots with them.
- [x] **Sashes, apron and pouches, 2026-09-20.** All sized off the waist width
      and the waist-to-hip distance, fitted to a shared chibi whose waist is about
      as wide as its hip and whose waist-to-hip is a sliver. On a body with a real
      waist and a longer drop the sashes (Reika, Daizen, Haruto; aspect 1.7 to 2.2
      against 4.8 to 6 on the chibi) came out boxes, the aprons (Chiyo, Satoko) a
      narrow strip to the hem, and the pouches crowded its corners. They now take
      their width from `_belt_line_half_w` (the waist on the chibi, so nothing
      moves there; the hip's width at the chibi's own ratio where the waist is
      narrower), a sash's depth is capped by its width, and the apron by its own
      width. Chibi-range builds only; the realistic build is untouched.
- [x] **Skirt hems, 2026-09-20: not a problem, the earlier note was wrong.** The
      hem is a share of the hip-to-ankle distance and moves with the hip, so it
      keeps its place on the figure; measured against the boot tops the gap is no
      bigger than on the shared chibi (Reika 0.05 head radii against 0.25, Satoko
      0.32 against 0.38, Keiko 0.19 against 0.32). The difference is that the
      default body's boots reach the hem, so the bare shins the shared chibi shows
      are mostly covered. Looked at (`out/skirt_hems_now.png`): the hems read
      cleanly. Nothing changed.
- [x] **The cover** (`cover.py`), 2026-09-20: the layout scales the figure's
      whole canvas to a share of the page, so the default body's smaller head
      (about 0.7 as wide as the shared chibi's) shrank the face the cover is
      built around and left the page empty. `figure_height` 0.56 to 0.60 and
      `figure_feet_y` 0.865 to 0.885: the largest scale that keeps the hair 31px
      clear of the title (0.62 puts it on the last line). The head is 228px across
      against 213px before and 296px on the shared chibi, so the cover is a
      taller, quieter figure than the chibi one; `out/cover_before_after.png`.
      The owner's call: the cover uses the tall chibi (its docstring's "the design"
      was the shared chibi). The front mist bank's seed went from 59 to 128 for the
      same reason: with 59 one large bump buried 77% of his right boot (the viewer's
      left) and the other boot only 27%; 128 buries both 56%, measured on the boots'
      own columns. The seed has to be re-picked if the figure's scale or build moves
      the feet.
- [x] **Head size, 2026-09-20: the head is 1.1 times as big.** Judged on Satoshi
      alone at 0.85, 1.0, 1.1, 1.2 and 1.4 against a fixed body
      (`harness/body/head_size_variants.py`, `out/head_size_variants.png`), then on
      the cover at 1.0, 1.1 and 1.2 (`harness/body/head_size_covers.py`): 1.0 read as
      a small-headed teenager, 1.4 as a bobblehead with no neck, and the owner's pick
      was 1.1. `BodyProfile.head_scaled(s)` re-expresses a profile under a bigger
      head with the chin held (landmarks `(y - 1 + s) / s`, widths `w / s`, and
      `(heads - 1 + s) / s` heads tall); `heads` alone would only rescale the whole
      figure. It is applied to `tall_chibi_long_torso` only, so Katherina's profile
      and her traced cuts are untouched. Every default-body render changed (17
      characters, both bases and the cover); the realistic builds and Katherina did
      not. The cover: hair still 31px under the title, head 242px across (228px
      before, 296px on the shared chibi), and the front mist seed re-picked to 111
      because the feet moved (128 buried one boot 47% and the other 70%).
- [ ] **Realistic builds** need their own pass (Satoshi's and the cast's), left
      for later by the owner.

**Held:**

- **T4.** Boot/toe silhouette: the reference's toe is more tapered than ours;
  minor.
- **T5.** Anything else the reference suggests, deliberately not itemized yet.

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
  their correctness check. Moot now that T2d declined any profile change.
- **The 4-head hypothesis is a rough pixel measurement**, not a calibrated
  trace (no known head-radius calibration exists for this reference the way
  the witch hat gave one for Katherina's). T2a's harness measurement is what
  makes it trustworthy; nothing downstream should be solved from the number
  in this doc.
