# PLAN

What we are working on, and where to pick it up. This file is only a pointer; the detail is in the docs it names.

## Current campaign: Franzi and the adult-woman body (started 2026-10-17)

A new, separate body type, `adult_female`, about 6.4 heads tall, and a first character on it, Franzi (original, adult), drawn
as flat vector shapes traced from the references in `ref/franzi/`. SFW only: clothing and swimwear are fine, no nipples or other
sensitive parts anywhere, a bare view exists only under `harness/` and is never a web tool or API option, age floor 21 enforced
in the render code.

- Full plan, gates and stages: [docs/adult-body-plan.md](docs/adult-body-plan.md)
- Status, findings and decisions, newest first (start at its RESUME section): [docs/adult-body-status.md](docs/adult-body-status.md)
- Work happens on `dev` in `../anime-character-creator-dev`, in `ts/` (TypeScript; the Python in `src/` is frozen). Nothing is on
  `main`, nothing is released, and `ref/franzi/` is still untracked.

### Where it stands (end of the 2026-10-17 session)

| stage | state |
|---|---|
| 0 to 3: target, gate, profile, torso and limbs | done, owner signed off the body |
| 4: bust, bikini top, briefs | done, owner signed off the chest, top and underwear |
| 5a to 5c: head, hair, hands and feet | built; the head and hair are traced and approved (5e, committed to `dev`); the hands and feet are placeholders from the full-body reference |
| 5e: head and face polish | done: eyes, brows, hairline, strands, outlines, ears, strips, ponytail and shoulder junction all traced and approved by eye; small leftovers in `docs/adult-body-status.md` |
| 5f: hands and feet from the close-ups | feet done; relaxed hand done (traced, gate green); open palm, fist and pointing hands later as options |
| 5d: Franzi preset in `presets.ts` | done 2026-10-19: `FRANZI` and `ADULT_PRESETS` (kept out of `PRESETS` until stage 7); her SVG is 184 KB (the body outline is defined once and referred to with `<use>`) |
| 6: garments (dirndl, blouse, shorts) | not started |
| 7: age guard, rules tests, catalogue, web, CLAUDE.md amendment | not started |

### Next up, in order

1. **Feet, then hands, traced from the close-ups in `ref/franzi/hands/`** (the owner's call, 2026-10-18: the ones in the body are placeholders
   from the full-body reference, where the hands are only about 100 px tall). The close-ups are on a 1008 x 1792 canvas, scaled up and
   not registered to the body, so each needs a mapping first (feet: ankle width and the toe row against the body's; hands: wrist width
   and finger length). `feet-front.png` is the clean one and matches the standing pose. The hands are four poses (open palm, relaxed,
   fist, pointing), none of them our hanging pose, so which one drives the hanging hand is the owner's call. Trace like the head: masks of
   the visible regions, edges fitted and smoothed, interior lines snapped to the drawn ridges, each checked against the reference at
   8x or more. The body gate (IoU at least 0.93) covers the feet and hands in the silhouette, so run it on every change.
2. **Smaller eye leftovers**: the lid is slightly heavy at the wing end, a thin tail runs along the top of the white at the inner
   end (the owner removed the lash flicks), the lower lash tick is missing.
3. **5d**: the Franzi preset (the harness version is `harness/franzi/franzi.ts`).
4. **6**: garments traced from the segment layers, one at a time. Decision needed first: adult garments cannot add fields to
   `Outfit` or `CharacterParams` (the Python-mirrored tests would break), so my lean is named outfits in a TypeScript-only table
   applied by the preset; see the status file.
5. **7**: guard, tests, catalogue entry (a deliberate fixture change, needs the owner's say), web tool, and the CLAUDE.md amendment the
   owner approved (adult build as its own decision, the harness-only bare view with its limits, the bikini-level baseline for the
   adult body only, tapered lines allowed).

### How we work on this (kept in memory too)

- Every matching step is judged against the reference with the two overlays: `ZOOM=n ./harness/run.sh harness/franzi/aligned.py NAME x0 y0 x1 y1`
  (side by side and a 50% blend, aligned by the body gate's mapping, never hand-placed crops) and
  `harness/franzi_hair/overlay_lines.py` / `harness/franzi/eye_outline.py` (our traced lines drawn on the reference).
- Trace, do not draw by eye; measure each layer before blaming the last one drawn. A contrast-stretched view separates black hair
  from dark detail. The eye is traced on the left eye; the right is its mirror unless something has to differ.
- Gates after every change: `cd ts && npm run typecheck && npm test`; `./refresh-ref-out.sh --check`, `./refresh-catalogue.sh --check`,
  `./refresh-bases.sh --check`; `uv run ruff check .`; `uv run pytest`; and the body gate `./harness/run.sh harness/franzi/gate.py adult_female`
  (IoU at least 0.93). Existing characters must stay byte-identical; no fixture is edited.
- Agent reviews (read-only, `sonnet`) check renders against the references before the owner is called; the owner confirms at checkpoints.
- Commit to `dev` periodically (owner's permission, 2026-10-17): one line, no trailer, no em dashes or double hyphens.
