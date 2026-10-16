# Soft hair: status and review record

The plan is `docs/soft-hair-plan.md`. This file is the running record: what was decided, what the
independent reviewers said, and what we did about each point.

## Where we are

- 2026-10-16: soft finish committed (02e3095). Plan draft 1 written, reviewed twice, revised to
  draft 2 and approved by the owner. Phase 0 mock-up built (`harness/soft_hair/mockup.py`) and
  defect-reviewed. Gate 0 picks received (below). No hair code is in the package.

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

## Review 3: defect-only review of the Phase 0 mock-up (sheets A to J, images only)

By eye at about 2000 px, nothing confirmed by pixel measurement.

| Finding | What we did |
| --- | --- |
| The left ear showed as a pale, semi-transparent patch on several variants, and sides differed. | Real: the overlay was drawn after the skin patches (`openings`). The mock-up now redraws the patches over it; the production version will draw the overlay before them. Fixed in `out/soft/v2`. |
| A pale band hugging the outer hair edge on both sides of the structure variants, unclear whether a rim light or a second outline. | Real enough to fix: the outermost clumps are now dark, so no pale clump sits on the silhouette. Fixed in `out/soft/v2`. |
| Hard-ended highlight shapes (the light-only band, the old gloss arc), streaks that cross lock boundaries (the fibre control). | Expected: the first two are what is being tested, the third is the control. |
| Greyish face and a lighter cap over the crown on the soft repairs. | Expected: the jaw shading and the depth wash are what the repair variants remove. |
| Doubled inner outline and a thicker top outline on the flat variant. | The flat house style, unchanged by design. |
| Fringe wedges differ left and right. | Deliberate: the part is off centre. |

Not judged: a 1 to 2 px spill past the silhouette, fine gradient banding, the lock tips in the zoom.

## Gate 0: the owner's blind picks on `out/soft/v2` (sheets A to J, key withheld until given)

Key: A=S, B=D, C=P, D=LS, E=L, F=r2, G=flat, H=r3, I=today, J=r1 (seed 1).

| Question | Answer | Variant |
| --- | --- | --- |
| Most like real hair | H, I, D | r3, today, LS |
| Most like a quick drawing | G, F | flat, r2 |
| Looks broken | A, B, C: polished at a glance, but the highlights do not match the red hair and read worse up close. E: highlights in odd places. | S, D (fibres), P, L |

Reading against the Gate 0 rule (does L, S or LS read as clearly more like hair than today's soft):

- Only LS reached the top three, beside today's soft and r3. It did not beat them, so the rule says stop on structure and light.
- S, P, D and L were named as broken. In the face crops the S highlights are a pale, desaturated pink grey wash over saturated red, which is a colour and placement defect, not proof that structure fails. This is an inference from one judge and one hair colour.
- r3 (gloss arc, depth wash and jaw shading all removed) is in the top three, and r2 (jaw shading still on) is in the bottom two. One judge, not a pair test, but it points at the jaw shading.

## Review 4: method review of the round 2 plan (a fresh agent, ran code and looked at the images)

| Finding | What we did |
| --- | --- |
| Diagnosis holds numerically: hue 350 to 352, saturation 0.71 to about 0.35 in composited highlights. | Confirmed by my own run as well. |
| Mock-up bug: `lens()` picks the lit side per point, and four right side guides flip it mid-guide, so the lit edge and the separation jump sideways. | Verified (b5, b6, o4, o3 flip once). Side chosen once per guide in round 2. |
| S and LS read as equal width stripes radiating from the crown; each highlight is paired with a near-black line, which may be the real "wishy". | Jitter plus no paired lines in S2. Separations softened. |
| Missing cheaper candidates: value steps without a lit tone; a single sheen. | Added SS and SH. |
| Gate 0b is not blind and the kill rule has no number. | Hidden duplicate of r3, new letters and crop; win rule written down in advance (plan section 11). |
| The guard was partly vacuous (hue passes on the failing S; hue meaningless for grey hair; constants are not the composited result). | Guard on rendered pixels, ratio with floor, wraparound. |
| Palette check was Risa only, no judge, and "raise value" fails at the extremes. | Owner sees red, dark, light and grey. Shadow-led for light and grey. |
| Size: the mock-up S is 127 KB (budget 90). | Production emits curves; checked in Phase 1. |
| Landing r3 first rests on one ranking. | Held until r3 is paired with today's soft. |

## Review 5: defect-only review of the round 2 sheets (a fresh agent, images only, no key)

| Finding | What we did |
| --- | --- |
| Base defects on every letter: boxy back hair block, pale wedge by the ear, a tan strip under the fringe edge, pale crescents on the jacket, floating short ticks in the fringe (the strand dashes). | Shared by r3 and everything else, outside the hair treatment. The tan strip is the soft finish's fringe shadow. Recorded as soft-finish repair candidates, not touched this round. |
| Old gloss arc (today): pale grey pink, cuts across the strands; face grey ring at the jaw. | Known, it is what r3 removes. |
| S2 and LS2: near-black stripes against bright red; dark band at the part above the forehead; muddy grey wedges on grey; olive shadows on blond. | Shadows gentler (value factor 0.87 not 0.80 to 0.65), separations lighter (0.74, opacity 0.6), no shadow clump at the part, and blond shadows pulled toward orange. |
| P2 (pointed fringe): six or seven evenly spaced petals, running down onto the temples. | Dropped from the sheets. Still in `render` for a later try. |
| Crown band (SH): hard diagonal lower edge, a seam. | Three stacked bands of rising opacity so the edge steps off. |
| The two copies of r3 were found identical. | Confirms the hidden duplicate is a valid noise row. |
| Not judged: stroke widths, sub-pixel seams, gradient banding, exact colour matches. | Pixel guard added (`harness/soft_hair/guard2.py`): lightened pixels keep 0.93 to 1.02 of the saturation of the r3 pixel under them, against 0.41 to 0.85 for today's soft. |

## Gate 0b, session 1: the owner's pair answers (`out/soft/v3/pairs-23`, one answer per row, given across the hair colours)

Key (same on the four r3 sheets): row 1 r3 left, LS2 right. Row 2 r3 left, r3b right (identical copies).
Row 3 r3 left, SH right. Row 4 SS left, r3 right. Row 5 S2 left, r3 right.

| Row | Answer | Reading | Owner's reason |
| --- | --- | --- | --- |
| 1 | left | r3 over LS2 | Highlights on the right a bit much, and the lack of hairlines. |
| 2 | no difference | control passes: identical copies seen as identical | |
| 3 | right | SH over r3 | Highlights subtle enough to work. |
| 4 | close call | SS about level with r3 | The highlights on the left work, but without hairlines it reads as one large segment, not individual hairs. |
| 5 | right | r3 over S2 | S2 highlights too much, and again no hairlines. On red they come closest. |

Nothing broken on any sheet. The `vs-today` sheet was not answered separately.

Against the pre-registered win rule (at least 5 of 6 judgments, never broken): none of LS2, S2, SS wins.
SH beat r3 once, on one session. By the rule the structure variants stop here.

What the owner's reasons add, which the rule does not capture: the one thing missing from every
structure variant is the hairlines. That is my doing. The structure variants switch the cut's strands
off (`strands_off`), which I chose in round 1 to avoid doubled lines, and r3 keeps them. The owner values
the hairlines. The second complaint is highlight strength: the subtle one (SH) works, the stronger ones
do not. Both are tunable, so the finding is not that structure fails but that two settings were wrong.
