# Soft hair: status and review record

The plan is `docs/soft-hair-plan.md`. This file is the running record: what was decided, what the
independent reviewers said, and what we did about each point.

## Where we are

- 2026-10-16: soft finish committed (02e3095). Plan draft 1 written, reviewed twice, revised to
  draft 2. No hair build work started. Waiting for the owner's sign-off on draft 2.

## Review 1: blind visual diagnosis (images only, not told hair was the suspect)

Saw `out/soft/threeway-risa.png` and `out/soft/close-sheet.png`. Moderate confidence on the order
of the top three, lower on the shares.

| Finding | What we did |
| --- | --- |
| Hair about 30 percent of the gap, fixable in vector. Pack hair has clumps in three value steps with highlights that follow the flow and taper; ours is one mass with hairlines that read as scratches. | Supports the diagnosis. Hair stays first. |
| Face construction about 20 percent (wide round face, large eyes, no upper-lid shape), partly the chibi design. | Out of scope here. Written down for a later plan. |
| Line quality about 15 percent: constant width, near-black on skin and hair; wanted variable-width, tinted lines. | Out of scope here, except that tinted hair lines already exist in soft. |
| Form shading about 12 percent; the soft finish's jaw gradient reads as dirt at the zoomed size. | Jaw shading becomes a pair to test in Phase 0, and is removed if the pairs favour that. |
| The soft gloss arc is a halo or plastic band that ignores strand direction; the depth wash makes hair chalky and pink; on orange it looks like a helmet, on white two-tone like a cowl. | Gloss arc and depth wash become pairs to test in Phase 0. The arc is replaced by a lit band that follows the hair, or dropped. |
| Wanted 6 to 12 tapered clumps in three tones, a few sharp highlights following each clump, pointed fringe locks. | Clumps are treatment S, highlights and lit band are treatment L. Pointed locks change the traced contour: held back, owner's decision. |
| Body, silhouette, hands, clothes about 10 percent, inherent to the chibi build; organic imperfection about 8 percent. | Out of scope. |

## Review 2: method and verification review of draft 1

Verdict: proceed with specific changes. Checked facts by running code.

| Finding | Severity | What we did |
| --- | --- | --- |
| Strand counts 28 (23, 4, 1) confirmed; 23 of 28 shorter than 0.5 head radii, median about 0.2. | fact | Kept, with the new numbers. |
| Preset count: 22, not 20, once the two neutral bases are counted; render about 2.7 ms not 3.6. | minor | Plan now says 20 named presets plus two bases, and "about 3 ms". |
| "Largest gap code can address" is unproven. The soft crown treatment may be working against hair; cheap fixes (edge treatment, hard-edged light and shadow) were never tested against structure. | important | Treatment L (light and shadow only) is tested against S (structure) in Phase 0. |
| Blocker: no hand-made target. First draw one static answer for Risa; if it does not look like hair at app scale no method will, and we stop for one afternoon's cost. | blocker | Phase 0 is now the hand mock-up, with the first kill point after it, before any instrument or generator. |
| Candidate C (promote the strands) is nearly dead: short, open, sparse, no closed regions; `long_parted` has no strands by the owner's decision. | important | Dropped. |
| Candidate A (procedural flow between two edges) has a basic problem: visible hair is a fringe, two curtains and a strip, not one sheet. | important | Not tried first. Authored guides cover the front piece only. |
| Missing candidates: semi-transparent clump overlays, offset copies of the mass for the lit band, hard-edged shadows from `front_shade`. | important | Added to treatments L and S. |
| Feasibility: `_fall_q` warps y only and is pinned above the cheek line; new marks go after the fill and before `openings` and the hairline stroke; the tail is separate; hat, knot, tie and clip are safe. | note | Written into section 4. |
| The blind protocol is not blind: the pack differs in dress, body and rendering and always wins "most like real hair". | important | Pack removed from every ranking. Gate pairs are new against today's soft. |
| The reviewers are language models with weak resolution on fine differences and a primed bias to falsify. | important | Reviewers are for regressions and rule checks; taste is forced-choice pairs judged by the owner. My own judgement is stated as limited in the plan. |
| Proxy metrics (visible locks, long-line share) are defined by the method under test, and noise raises luminance spread. | important | Deleted. Only regression guards remain. |
| Forced choice: randomised pairs, at least 8 characters, a second day, 1x and close-up, a known-worse control. | important | Adopted in section 7. |
| Kill timing too late (Gate 1 after all of Phase 0); six gates times three checks is heavy. | important | Four owner touchpoints; first kill point is Gate 0. |
| Budget gate looks at Python time and bytes, but the app swaps parsed elements every 85 to 145 ms; the real cost is Chrome paint of clipped semi-transparent paths. | important | A measured Chrome frame time is part of the budget. |
| Start with two cuts, not one: Risa's cut is the most hand-authored and used by one preset. | important | Phase 1 builds on `long_fringed` and `long_traced`. |
| The pack drifts toward being the target; the trace skill forbids reproducing a reference's texture, shading or line weight. | important | Rule in section 2: looking and comparing only; nothing tuned to pack numbers. |
| The `CLAUDE.md` soft exception names "hair depth and gloss"; clump overlays go beyond it. Keep new code out of `_hair_defs` paths flat shares. Check ids with `id_prefix` across several frames. | minor | Owner approves new wording before Phase 1 lands structure; id and flat-path checks added to section 7. |

## Decisions log

- 2026-10-16: take both reviews' changes into draft 2 (above). Not taken: nothing set aside so far.
  The pointed-fringe request is deferred to the owner, not refused.
