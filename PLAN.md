# PLAN

What we are working on, and where to pick it up. This file is only a pointer; the detail is in the docs it names.
Last updated 2026-10-20.

## Current campaign: Franzi's emotions and gestures for the companion (planned 2026-10-20)

The companion app (`../anime_ai_companion`) shows a character as a set of pictures: seven emotions (`neutral`, `happy`, `sad`,
`angry`, `surprised`, `shy`, `thinking`), each with a rest picture, a blink and three mouth openings, plus two gestures, `wave` and
`cheer`, of two pictures each. It asks this repo for them through the face and arm fields of `CharacterParams`. Franzi was built
without them, and until 2026-10-20 **none of those fields changed her drawing**: the adult head draws its own traced eyes, brows and
mouth, and the adult arms ignore `right_arm_out` and `left_arm_out`. The blink and the mouth fields work now; the brows, blush, lids, gaze and arms do not yet. Checked by rendering her with each field at several values
(every render was byte-identical to her default one). Today the companion can only show her through the AI-made pack
`packs/franzi-dress` in its own repo.

- Plan, findings, open questions for the owner: [docs/franzi-expressions-plan.md](docs/franzi-expressions-plan.md)
- State: steps 0 and 1 done 2026-10-20, uncommitted: the byte-identity baseline for her default drawing, the blink (`eyes_closed`) and the mouth (`mouth_curve`,
  `mouth_width`, `mouth_open`). Next is step 2, the rest of the face (brows, blush, lids, gaze), then hands, arms and the gestures. The bikini pack
  (`../anime_ai_companion-packs/packs-src/franzi-bikini`) is the reference for the arms. Decisions 3 (blush), 6 (the frame) and 8 (release) are still open.
- Work happens on `dev` in `../anime-character-creator-dev`, in `ts/`, as before.

## Last campaign: Franzi and the adult-woman body (2026-10-17 to 2026-10-19), done and released as v0.5.0

A separate body type, `adult_female`, about 6.4 heads tall, and Franzi (original, adult) on it, drawn as flat vector shapes traced from
`ref/franzi/`. SFW only: clothing and swimwear are fine, no sensitive parts anywhere, a bare view exists only under `harness/`, age
floor 21 enforced in the render code.

- Plan, gates and stages: [docs/adult-body-plan.md](docs/adult-body-plan.md)
- Status, findings and decisions, newest first: [docs/adult-body-status.md](docs/adult-body-status.md)
- Her outfits and what each garment is cut from: [docs/franzi-outfits-plan.md](docs/franzi-outfits-plan.md)
- Released: `main` at `eb1d505` (the merge of `dev`), tag `v0.5.0`, `ts/package.json` at 0.5.0. `ref/franzi/` is tracked.

| stage | state |
|---|---|
| 0 to 4: target, gate, profile, torso, limbs, bust, top, briefs | done, owner signed off |
| 5: head, face, hair, hands, feet, the `FRANZI` preset | done (head and hair traced; relaxed hand only) |
| 6: garments | done: dirndl (blouse, bodice, skirt, apron, bow), shorts, boots, knee socks, belt, pouches, crystals, coat, robe, hakama, collar |
| 7: age guard, rules tests, catalogue, web, Python removal | done in 0.5.0 |

Gates on 2026-10-20 (run, not carried over): 915 TypeScript tests pass, 7 skipped, 0 fail; typecheck, `refresh-ref-out.sh --check`,
`refresh-bases.sh --check` and `refresh-catalogue.sh --check` green. The body gate (IoU at least 0.93) was not rerun; its last
recorded value is 0.957.

### Leftovers from that campaign

- Dirndl detail: the apron's gathers, the skirt's second tone, the bodice's panel seams, the blouse neckline's scallops (smoothed).
- Coat with sleeves, the robe's kimono collar band, a traced look for the coat, robe, hakama, belt and collar (first pass, cut from the
  body's tables with no reference). The strap and shoulder bars are still the chibi's shapes.
- A `trouser_cut` choice for full-length trousers; the owner has not been asked.
- The open palm, fist and pointing hands (`ref/franzi/hands/`): only the relaxed hand is traced. The wave and the cheer need the first two.
- **`CLAUDE.md` still lacks the amendment the owner approved on 2026-10-17** (the adult build as its own decision, the harness-only bare
  view, the age guard in the render code). As of 2026-10-20 it still says every figure is the tall chibi and keeps "no NSFW or
  anatomical content, until there is a proper adult body" as written. It needs the owner's wording before it is edited.
- The companion's `python/make_sample_pack.py` still imports the removed Python package, so it cannot draw a pack any more (read from its
  source, not run). It is on that repo's side but the expressions plan depends on replacing it.

## How we work on this (kept in memory too)

- Every matching step is judged against the reference with the two overlays: `ZOOM=n ./harness/run.sh harness/franzi/aligned.py NAME x0 y0 x1 y1`
  (side by side and a 50% blend, aligned by the body gate's mapping, never hand-placed crops) and
  `harness/franzi_hair/overlay_lines.py` / `harness/franzi/eye_outline.py` (our traced lines drawn on the reference).
- Trace, do not draw by eye; measure each layer before blaming the last one drawn. Nothing below the chin is traced off a reference whose
  body is not ours.
- Gates after every change: `cd ts && npm run typecheck && npm test`; `./refresh-ref-out.sh --check`, `./refresh-catalogue.sh --check`,
  `./refresh-bases.sh --check`; and the body gate `./harness/run.sh harness/franzi/gate.py adult_female` (IoU at least 0.93). On macOS the
  PNG tools need `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib` (the refresh scripts and `harness/run.sh` set it; a bare call of
  `harness/svg2png.py` does not). `ts/node_modules` exists only in the `dev` worktree.
- Existing characters stay byte-identical; no fixture is edited without the owner's say (the rules for a deliberate change are in
  `harness/ts_port/golden-updates-stage7/README.md`).
- Agent reviews (read-only, `sonnet`) check renders against the references before the owner is called; the owner confirms at checkpoints.
- Commit to `dev` with the owner's permission (periodic commits were allowed on 2026-10-17; nothing from 2026-10-20 is committed yet): one
  line, no trailer, no em dashes or double hyphens. `main` and tags only on the owner's say.
