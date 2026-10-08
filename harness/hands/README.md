# Hands harness

The tools of the hands campaign (`docs/hands-plan.md`, record in
`docs/hands-status.md`). Promoted on 2026-10-08 from the audit's scratch scripts.

Run from the repo root with the runner, which sets cairo and makes `out/`:

    ./harness/run.sh harness/hands/metrics.py mitten traced
    ./harness/run.sh harness/hands/sheet.py out/hands/v0 mitten traced

| Script | What it does |
| --- | --- |
| `handlib.py` | shared helpers: render with a candidate applied, crop to a hand, isolate one hand's SVG, measure it against the gate |
| `candidates.py` | the candidates, now the real styles in `src/`: `mitten`, `notched`, `stroked`, `curled`, `open`, `fist` |
| `variants.py` | a note only: which prototype became which shipped style (the code moved to `src/`) |
| `sheet.py` | the owner's standard sheet: five images, one lettered column per candidate, the baseline first |
| `metrics.py` | the footprint gate per candidate, per preset (`--all-presets` collapses identical results) |
| `ablate.py` | a record of the audit: `pieces` and `widen` ran on the old traced hand and patch constants that no longer exist |

## The footprint gate

For hanging hands, not for a hand gripping a staff (that is judged by eye).
Proposed from the mitten's measured footprint, the owner's to change, in
`handlib.GATE`:

| measure | mitten | gate |
| --- | --- | --- |
| bounding-box height, head radii | 0.34 | 0.30 to 0.42 |
| height over width | 0.78 | 0.70 to 1.20 |
| outline share of the hand's pixels | 26% | at most 35% |
| narrowest skin run in the fingers, outline widths | about 10 | at least 1.5 |
| width where the hand meets the arm, against the mitten's | 1.00 | 0.90 to 1.10 |

The narrowest-run measure reads the narrowest skin run between 30% and 85% of the
hand's height. A figure near 0.07 means the fingers hold a pixel or less of
visible skin between their strokes. It is a legibility indicator, not a precise
width: antialiasing sets its floor at about one pixel.

## Adding a candidate

Register a `Candidate` in `candidates.py`: a label (the owner answers with its
letter on the sheet, in the order given on the command line), a transform of the
`CharacterParams`, and a `patch` context manager when it is a code variant that
is not in `src/` yet (the traced widening in `ablate.py` is an example of
patching `_traced_placement`).

## Known limits

- An arm swung out is drawn in a `rotate(...)` group that `metrics.py` does not apply, so
  Katherina's staff arm (swung 36 degrees) is measured unrotated. No other preset swings.
  The gate excludes the grip.
- The skin mask is a colour match. A skin tone close to the outline or to the
  white background would defeat it; the sheet's dark tone is the one tested.
- `metrics.py` rasterises each hand alone, so it does not see how a hand meets
  its cuff or sleeve. The sheet shows that; the metrics do not.
