# Soft hair: making drawn hair read as hair

Status: **draft 2, before any build work**. Draft 1 went to two independent reviewers on 2026-10-16;
their findings and what we did about each are in `docs/soft-hair-status.md`. This draft is for the
owner's sign-off.

## 1. The question

The companion app shows a character either drawn by this package or as a picture pack made with
an image model. Side by side (`harness/soft_finish/threeway.py`) the drawn one looks less
polished. `finish="soft"` (commit 02e3095) closed some of that. The owner's verdict: a step up,
do not push it much further.

The owner's read of the largest remaining gap is the hair: traced, but a quick drawing and not
real hair. This plan is about that, and about repairing the parts of the soft finish that turned
out to hurt the hair (section 3).

**Success, in one sentence:** at the size the companion shows her (about 840 px tall, close-up), the
owner, shown pairs in random order, picks the new soft hair over today's soft hair clearly and on
most of the cast, and the flat house style is untouched.

If we cannot reach that, the right outcome is to stop and keep what we learned.

## 2. Constraints that do not move

- `"flat"` stays byte for byte what it is: `./refresh-ref-out.sh --check` passes after every
  commit. All new drawing is behind `finish="soft"`.
- The silhouette is canon. The mass, the fringe edge, the hairline, the side curtains and the
  lock tips keep their traced contour, so new marks are clipped to the existing hair shapes and
  add no silhouette (the hair contract in `docs/architecture.md`, and
  `test_hair_stays_under_the_canvas_ceiling`). A reviewer and the owner both asked for pointed
  fringe locks; that changes the traced contour and is a separate decision for the owner, not
  part of this plan.
- Deterministic output: same arguments, same bytes. Variation comes from a fixed hash of lock
  index and cut name, never `random` and never set ordering.
- Gradients, strokes and fills only, no blur: cairosvg writes the PNGs and has none.
- No reference pixels are shipped, traced or reproduced, and nothing here uses a model. The
  picture packs are for **looking and comparing only** (`.claude/skills/trace-reference/SKILL.md`
  forbids reproducing a reference's texture, shading, gradients or line weight, and `CLAUDE.md`
  says the references are not a target). No lock count, highlight share, width or tone is tuned to
  a number measured off a pack. The target is hand-drawn anime conventions and our own mock-up.
- The `CLAUDE.md` soft-finish exception names "hair depth and gloss". Overlays that give the hair
  structure go beyond that wording, so the owner approves new wording before it lands (section 8).
- Work is on `dev` in `../anime-character-creator-dev`. Commits are small and single-line, no
  trailer. Nothing is pushed, merged or released unless the owner says so. The companion app is not
  touched in this plan.

## 3. What we know, and what we are guessing

Verified (run or read, by me and re-checked by a reviewer unless noted):

- A cut (`Hairstyle`) is a set of callables of traced chains in head-radius units: `mass`,
  `hairline` (the front piece), `fall_edge`, `tip_edge` regions, optional `strands`, `underside`,
  `tip_lines`, `openings`, `front_shade`. They stretch with the hair's fall (`_fall_q`, which
  warps y only and is pinned above the cheek line).
- Draw order: the mass is drawn behind the body, the front piece after the head. Almost all the
  hair that shows is the front piece: the fringe, two side curtains and the dark strip between
  them. The mass shows mostly as tips below the shoulders. The tail is a separate function.
- Risa's cut, `long_fringed`, has 28 strands: 23 are one quadratic segment, 4 have two, 1 has
  three. 23 of 28 are shorter than 0.5 head radii against a fall of 3.44, median about 0.2. They
  are short dashes at one weight.
- Preset usage by cut: `long_traced` 7 (linnea, lindita, satoko, kyoko, chiyo, keiko, krista),
  `short_layered` 7 (gero, daizen, elara, haruto, reinhard, tenno, viktor), `short_crop` 3 (dritan,
  satoshi, tomohiro), `long_parted` 2 (katherina, reika), `long_fringed` 1 (risa). That is the 20
  named presets; the two neutral bases add one `short_crop` and one `long_blunt`.
- A render is about 3 ms and 50 KB flat, 65 KB soft. The companion shows 7 emotions, each as 5
  SVG documents (4 mouth openings and a blink), every one carrying the whole hair, and swaps the
  parsed element roughly every 85 to 145 ms (`public/avatar.js`). So hair cost is paid up to 35
  times, and the real cost is the browser's paint of many clipped, semi-transparent paths, not
  Python time.
- Two independent viewers disagree with each other in useful ways, and agree on this: the soft
  finish's gloss arc reads as a halo or plastic band that ignores strand direction, the depth wash
  makes the crown chalky and pink, the jaw shading reads as dirt at the zoomed size, and on the
  orange and the white two-tone hair it looks like a helmet and a cowl.

Reported by a blind reviewer who saw only the images (moderate confidence, rough shares): hair
about 30 percent of the gap and fixable in vector, face construction about 20 percent and partly a
design choice, line quality about 15 percent, form shading about 12 percent, body and silhouette
about 10 percent, organic imperfection about 8 percent. So hair first is supported, but not by
a wide margin, and the face and eyes come next. They are out of scope here and are written down for
a later plan.

Not yet known (the plan exists to find out):

- Whether lock structure, or hard-edged light and shadow with better edges, is what turns "quick
  drawing" into "hair". The owner's hypothesis is structure; the method reviewer's is that light
  and edges may carry more. Phase 0 tests both.
- Whether anything we build survives app scale, the 1.5x close-up crop and the CSS bob.
- Whether it holds on light, dark and vivid hair, and across cuts.

## 4. Candidate treatments

All new marks go after the front piece's fill and before its `openings` (skin patches) and its
hairline stroke, clipped to the front fill (and to the mass for the mass), so they cannot add
silhouette and compose with the two-tone `tip_edge` clip. Overlays are semi-transparent tint and
shade shapes, not opaque fills.

- **L. Light and shadow only.** One hard-edged lit band that follows the fringe and the curtains
  in place of the single gloss arc, and 2 or 3 hard-edged shadow shapes (from `front_shade`, which
  exists, and the sides of the curtains). No new lock lines.
- **S. Structure.** Clump shapes: 6 to 12 tapered bodies on the front piece, each with a lit
  side and a shadow side, built from authored guide chains for the front piece only (a new optional
  `locks(fall)` on the cut, in head radii, stretched like the strands; widths are computed after
  the stretch).
- **L+S.** Both.
- **D. Fibre texture control.** Many thin tapered low-opacity strokes. Not expected to win. It is
  in the test to calibrate the judge and to show whether density alone fools anyone.
- **Dropped:** promoting the existing strands to lock boundaries. They are short, open and sparse
  and enclose no regions. Fully procedural flow from the outline: the visible hair is a fringe,
  two curtains and a strip, not one sheet between two edges, so it is not tried first.

## 5. Phases and gates

There are four owner touchpoints, each a forced choice between pictures, not a general "do you
like it". Independent reviewers are used for what they are good at (finding regressions, broken
clipping, gaps between frames, id clashes, rule violations), not for taste: they are language
models with weak resolution on fine hair differences.

### Phase 0. Mock-up, before any instrument or generator

Because a generator that makes the wrong thing well is the worst outcome, first draw the answer by
hand.

- Hand-author, for Risa only, a throwaway overlay for the visible hair as static numbers in a
  script (not production code, no `locks` field yet): variants **L**, **S**, **L+S**, and **D**,
  next to today's soft, a soft with the gloss arc removed, and flat.
- In the same pass, repair the soft finish's own regressions as variants: gloss arc on and off,
  depth wash on and off, jaw shading on and off. These are cheap and the evidence says some of them
  hurt.
- Render at the app's close-up size and at full-body size, on the dark stage ground.

**Gate 0 (kill point, owner):** shown the variants in random order as pairs, does any of L, S or
L+S read as clearly more like hair than today's soft, and which? If none does, stop here: the
cost is one afternoon and the finding is that the gap is not in hair structure or light. If one
does, that variant is what the generator must produce, and the owner has already approved the
look.

A fresh reviewer checks the mock-up only for defects: marks outside the hair, seams, odd edges.

### Phase 1. Make it real on two cuts

Build the generator for the winning treatment on **Risa's cut (`long_fringed`)** and on a second
cut that the creator's own roster uses, **`long_traced`** (7 presets), so we find early whether it
generalises. Add the optional `locks(fall)` on a cut only if S is in the winner. Add the proxy
**regression guards** only: ink ceiling, bytes, ids, determinism.

Tests and checks as in section 7. A measured Chrome frame time is part of the budget (below).

**Gate 1 (owner):** forced choice, new soft against today's soft, on Risa and two `long_traced`
presets, at app scale. Reviewer: regressions only.

### Phase 2. The other cuts and the cast

`short_layered` (7), `short_crop` (3), `long_parted` (2, which has no strands by the owner's
decision, so it needs L or its own guides). Hair length at three settings, two-tone tips, a tail and
a knot, ties and clips, a hat and a headband, light, dark and vivid colours.

**Gate 2 (owner):** a contact sheet of the whole roster, today's soft against new, in random
order. The owner marks any character that looks worse than today's soft; each is fixed or excluded,
never waved through. The reviewer tries to break it (clipping, gaps, odd colours).

### Phase 3. Hardening and sign-off

Tests, budgets, parity, determinism, docs, the `CLAUDE.md` wording, and a final read of the whole
diff.

**Gate 3 (owner, plus a code reviewer):** a fresh reviewer reads only the diff and the tests; the
owner signs off. A release, a version bump and the companion wiring are separate decisions.

## 6. When we stop

- **At Gate 0** if no variant is clearly better than today's soft. Keep the repairs to the soft
  finish that the pairs favour, and stop.
- **At Gate 1** if the owner sees no clear gain at app scale on a real generated hair, or if the
  generated hair is worse than the hand mock-up that was approved. Revert the hair work.
- **Narrow at Gate 2** if a cut will not work: ship the cuts that do and leave the rest on today's
  soft, with the reason written down.
- **Always:** any commit that moves `flat` output is reverted, not fixed forward.

## 7. Verification

**Every commit, automatic:** `./refresh-ref-out.sh --check`, `ruff check`, `ruff format --check`,
`pytest` and the soft-finish tests; XML well formed; every id defined once and every `url(#...)`
resolving, with and without `id_prefix`, and with several frames of one character in one page (the
ids `hair-depth`, `soft-hair-clip` and the new ones must not clash); same arguments give the same
bytes twice; the hair ink ceiling test; the new code stays out of any `_hair_defs` path flat shares.

**Budget, set at Gate 0 and checked every commit on the cast:** soft SVG at most 90 KB per document
(today 65 KB); Python render at most 10 ms; and a **measured Chrome frame time** for a page that
swaps a whole emotion's 5 frames the way the app does (about every 85 to 145 ms), compared with
today's soft. If the budget cannot hold, the fallback is to describe the hair once and share it
across frames, which is a companion change and so needs its own decision.

**Browser parity:** the same SVG drawn by cairosvg and by Chrome, compared at each gate. Gradients
and clip paths are where they differ.

**Taste is decided by forced-choice pairs, not by metrics or by reviewers.** New against today's
soft, left and right randomised, at app scale and at the close-up crop, on at least 8 characters.
Repeated on a second day, with a control pair that is known to be worse (the D fibre noise) to
calibrate the judge. Shown unlabelled. No pack image is ranked against ours: it differs in dress
and body and in rendering and is identifiable at a glance, so it would always win and tells us
nothing.

**What I do not rely on:** my own judgement of "looks like real hair" is a language model's, with
the same resolution limit as the reviewers' and the same stake in the outcome. I use it for
regressions and for catching obvious defects, and I show the owner the pictures.

**Proxy metrics:** only regression guards (ink ceiling, bytes, ids, determinism). "Number of
locks" and similar measures are defined by the method being tested and noise can raise a luminance
spread, so they are not used to judge.

## 8. Review and sign-off

- Independent reviewers are fresh agents with no memory of this conversation, given artefacts and
  criteria, told to try to falsify, and not given my conclusion first. Their findings, and what we
  did about each, are kept in `docs/soft-hair-status.md`.
- **Done (draft 1):** a method reviewer on this plan, and a blind reviewer on the images. Both
  changed the plan.
- **Gate 0:** a defect-only review of the mock-up. **Gate 1, 2:** regression and break-it reviews.
  **Gate 3:** a code review of the diff.
- **The owner** has the four touchpoints, sees the pictures and the one question that matters at
  each, and can stop or redirect at any point. The owner also approves the new wording of the
  `CLAUDE.md` soft-finish exception before Phase 1 lands any structure.

## 9. Risks

- The gain is real up close and invisible at the size she is mostly seen. All judgement is at app
  scale, and Gate 0 is the earliest kill.
- Tuning to one character, or to the one character with a pack frame. The two-cut spike and the
  full-roster Gate 2 are there for that.
- Light and white hair shows highlights badly, dark hair shows shadows badly; the cast has both.
- Browser paint cost with many clipped semi-transparent paths; measured in Chrome from Phase 1.
- Scope creep into the face, the eyes and the clothes. Written down for later, not done here.
- The flat canon eroding quietly. Flat stays byte-identical and the exception stays opt-in.
- The pack drifting into being the target. Rule in section 2; any number measured off a pack is
  informational and goes nowhere near a parameter.

## 10. Questions for the owner

1. Do you approve this order, with the hand mock-up first and the first kill point after it?
2. Which characters matter most for the Gate 1 and Gate 2 pairs? Proposed: risa, a `long_traced`
   (satoko, linnea and lindita cover light, vivid and orange), katherina, gero, satoshi.
3. Is up to about 40 percent more bytes per document acceptable (65 KB to 90 KB), or is the
   budget tighter?
4. Pointed fringe locks need the traced contour to change. Is that off the table for now, as I
   have assumed?
5. Are you happy to be the judge at the touchpoints, with randomised pairs, while the reviewers
   only look for defects?
