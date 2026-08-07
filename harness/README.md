# Measurement harnesses

The scripts that measured `ref/` and judged what shipped against it. They are
here rather than under `out/` because `out/` is ignored end to end, so anything
left there is one cleanup away from gone. `out/variants/README.md` said as much
before the cleanup that produced this directory: *"if `out/` is ever cleaned the
script goes with it: copy it somewhere first."*

**The images these produced are not kept.** They were the 152MB that the
cleanup removed, and every one of them is a rerun away. What is worth keeping
is the code that took the measurement, because most of these numbers were not
obvious and several of the obvious ways to get them are wrong.

## Running one

    ./harness/run.sh harness/trace/see.py

The runner exists because there are two preconditions and both used to be
footguns: `cairosvg` needs `DYLD_FALLBACK_LIBRARY_PATH` set before the process
starts, and the scripts write into `out/` subdirectories that they do not
create. Running a script directly with `uv run python` works only if you have
already handled both.

## What is runnable

| State | Scripts |
| --- | --- |
| Runs | most of them, including all of `trousers/` and `ear2/` |
| Needs `numpy`, which is not in the venv | `ear/wedge.py`, and in `trace/`: `check`, `chibi`, `contour`, `fit`, `fringe`, `fringe2`, `fringe3`, `probe`, `probe2`, `satoko`, `volume` |

The numpy set is **record-only** until someone adds the dependency. That is a
deliberate non-fix: they measured what they measured, the results are written up
in `STATUS.md` and `docs/gap-analysis.md`, and adding a dependency to the
shipped package so that a scratch script runs is the wrong trade.

Nothing here is linted or formatted. `pyproject.toml` excludes the directory,
for the reason the ruff config already gives about the markdown examples: the
code that ships is what those tools police. Several of these scripts are kept
precisely because they are records of readings that did **not** work, and
tidying them would be editing the evidence.

## The passes

| Directory | What it measured |
| --- | --- |
| `trace/` | Satoshi's silhouette, fringe and both builds' calibration, plus Satoko's hair. The largest set, and its own README is the index |
| `ear/` | the first ear pass: variants with the hair suppressed, the depth question, a loud palette |
| `ear2/` | the ear re-traced off the owner's crop, including the solve for where the fold's band sits |
| `trousers/` | the trouser rebuild, measured off the silhouette rather than off colour |
| `variants/` | the hair and leg variant sweep, which regenerates a whole tree of candidates |
| `head/` | head taper candidates at the realistic build |
| `scar/` | the three heads cropped to a common box so a four-pixel scar is legible |

Each of `trace/`, `ear2/`, `trousers/` and `variants/` carries its own README
with the per-script table and, more usefully, what the measurement said. Read
those before rerunning anything.

## The recurring lesson

Written down because it cost the same mistake more than once: **naive pixel
measurement gave wrong answers here repeatedly, and the wrong answers looked
fine.** Picking a garment out by its colour fails on both sheets. Summed colour
distance lets a surplus in one channel pay for a deficit in another. A chibi's
hand sits at very nearly its hip's width, so the widest run below the belt is a
hand rather than a leg. The fixes are written into the scripts at the point
where they matter. `.claude/skills/gap-analysis/PITFALLS.md` is the same
material for the strip comparisons.
