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
| 5a to 5c: head, hair, hands and feet | built; head and hair being polished (5e) |
| 5e: head and face polish | in progress: eyes, brows, lid, crease approved by eye; hairline pass done (uncommitted, awaiting the owner's look), lock-to-dome steps next |
| 5d: Franzi preset in `presets.ts` | not started |
| 6: garments (dirndl, blouse, shorts) | not started |
| 7: age guard, rules tests, catalogue, web, CLAUDE.md amendment | not started |

### Next up, in order

1. **Hair, after the hairline pass.** The hairline itself is done (the face chain above the brows is traced as it is, includes the
   forehead's shadow strip, smoothed; details in `docs/adult-body-status.md`). Left from the whole-hair recheck: the steps in the
   silhouette where the lock pieces meet the dome (about y 215 on both sides), a flat ledge on the left lock's inner edge under the
   eye, the ponytail's tip (a wedge, the reference flicks out) and a flat cut on its right side, the left ear is hidden, the strand
   lines are now traced one by one on the stretched reference (27, most secondary fine lines still missing, see
   the status file), the hair colour is near-black with lighter strands.
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
