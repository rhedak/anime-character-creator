---
name: gap-analysis
description: Compare the rendered characters against the canon reference art in ref/ and produce a prioritised gap analysis. Use when asked how close the output is to the references, what is still wrong, what to fix next, or to re-run the comparison after a shape pass to see what moved.
---

# Gap analysis: renders against the canon

Turns "how close are we?" into a ranked, evidenced list of what to change,
with the measurement separated from the judgement. The output is a
refreshed `docs/gap-analysis.md`, a set of comparison strips, and a
summary that says which findings are measured and which are seen.

**This is analysis, not a shape pass. Do not edit `character.py` while
running it.** Acting on a finding is a separate piece of work, and mixing
the two loses the record of what the state was.

## Ground rules for this repo

- **The style anchor is `ref/satoko-chibi.jpg` and `ref/satoko-real.jpg`,
  applied to both characters**, unless the owner says otherwise. The
  Satoshi references are the source for his haircut and his trousers and
  nothing else, because they are drawn as a more extreme chibi and on a
  different palette. Where the two disagree, Satoko wins, and the
  disagreement gets reported as reference inconsistency rather than as a
  gap.
- **The references are guides, not targets.** Measure to find out what is
  wrong, then choose by eye. A number that differs is a lead, not a
  verdict.
- **Never quietly re-open a decision the owner already took.** Several
  values in the code are deliberate calls recorded in comments, and the
  Satoshi crown tousle is parked outright with a bar of beating the plain
  circle by eye. `iris_size` and `eye_dx` are the two that a naive
  measurement will want to change. If the measurement disagrees with one
  of these, say so *and* say that it was a prior call, so the owner
  decides.
- **Anything that needs a rule in `CLAUDE.md` relaxed is the owner's
  call**, not a step in a plan. Present it as an option with its
  tradeoff.

## Step 1: strips first, and look at them

Do this before measuring anything. Most of a good report comes from
looking at a normalised pair, and the measurements exist to pin down what
looking already suggested.

Everything runs through `probe.sh`, which is a wrapper around `probe.py`
for the project's venv. Call it by path and do not put it in a shell
variable: the user's shell is zsh, which does not word-split an unquoted
variable, so `P="... probe.py"` followed by `$P strip` fails with "no such
file or directory".

Make sure the renders are current first (`./refresh-ref-out.sh --check`),
then pick a fresh `out/NN/` and build:

```bash
S=.claude/skills/gap-analysis/probe.sh   # a path is fine in a variable, a command is not

# full figures, ref beside ours, guide lines every 0.1 of figure height
$S strip --guides --out out/NN/cmp_satoko.png \
  --panel "K chibi REF=ref/satoko-chibi.jpg" --panel "K chibi OURS=ref-out/satoko.png" \
  --panel "K real REF=ref/satoko-real.jpg"  --panel "K real OURS=ref-out/real/satoko.png"

# heads at 2x
$S strip --band 0,0.42 --zoom 2 --out out/NN/heads_satoko.png --panel ... --panel ...

# garment construction, and the hem and boots
$S strip --band 0.42,0.78 --zoom 2 --out out/NN/torso_chibi.png --panel ... --panel ...
$S strip --band 0.74,1.0  --zoom 2 --out out/NN/legs.png       --panel ... --panel ...
```

Read every strip with the Read tool. Write down what you notice before
you measure, so the measurement is testing an observation rather than
fishing for one.

## Step 2: compute ours, measure the references

Asymmetric on purpose. Our own landmarks are known exactly, so counting
pixels on our own output only adds error and does not name the constant to
change:

```bash
$S skeleton                                  # every anchor, as a fraction of H
$S skeleton --preset satoko --heads 4.0      # or one build
```

For the references, each tool answers one question and nothing is derived
from another tool's output:

```bash
$S column ref/satoko-chibi.jpg               # garment stack down the centre, with hex
$S profile ref/satoko-chibi.jpg ref-out/satoko.png    # silhouette width, both, with bars
$S eyes ref/satoko-chibi.jpg --chin 0.46     # eye apertures
$S sample ref/satoko-chibi.jpg --box 0.44,0.51,0.53,0.55   # exact colour, for palette
$S rows ref/satoko-chibi.jpg --colors "#e6b845,#eaead8" \
        --against "#f5d8c4,#486848,#a89888,#0a0a0a"        # hair span and per-lock width
```

`rows` needs `--against` on a reference. Pale hair and light skin are
within any tolerance wide enough to survive JPEG, and without competitors
to lose to, "hair" runs to the bottom of the figure.

Run the same `rows` and `eyes` on our render with our exact colours and
`--tol 6`, so the two sides are measured the same way.

## Step 3: confirm any landmark before quoting it

`column` gives you runs of colour, not names. A mouth line and a jaw
stroke are both a few rows of dark and they are easy to swap, which
changes a headline proportion. For anything you are going to put in the
report:

```bash
$S strip --band 0.34,0.60 --zoom 3 --guides --out out/NN/probe_chin.png \
   --panel "chin=ref/satoko-chibi.jpg"
```

Then look, and use what you saw. If a number cannot be confirmed, quote
it to one significant figure or drop it and describe what the strip shows.

## Step 4: write it up

Refresh `docs/gap-analysis.md`, keeping its shape:

1. **Method and units.** H is figure height. Ours computed, references
   measured. Which strips are the evidence and where they are.
2. **What already matches, and should not be disturbed.** As important as
   the gaps: it is what stops the next pass moving something that was
   already right. Include the palette table from `sample`.
3. **Where the references disagree.** Any delta explained by the
   references themselves, so nobody chases it.
4. **The gaps, ranked by how much of the "not the canon style"
   impression each carries**, not by category and not by ease. For each
   one: what the canon does, what we do, the number if there is a
   trustworthy one, the function to change, and whether it needs a
   decision.
5. **Suggested order**, cheapest-with-most-effect first, with anything
   needing the owner's call at the end.

Then update `STATUS.md` to point at it, and note anything the analysis
closes off the existing backlog.

## Reporting

In the summary, keep three things apart:

- **measured** and reproduced, with the number
- **seen** on a strip, described
- **needs a decision**, with the options and the tradeoff

Say which findings the previous run already listed and which are new, so
a re-run after a shape pass reads as progress rather than as a fresh
audit. `docs/gap-analysis.md` is the baseline of record for that.

## Before declaring done

- Every quoted number came from a tool that reported agreement, or from a
  crop you looked at.
- No number is normalised by anything except figure height.
- No shape changed: `git diff --stat src/` is empty. Touching `out/`,
  the docs, or this skill is expected; touching `src/` means the analysis
  turned into a shape pass.
- `.venv/bin/python -m ruff check .` and `-m pytest -q` still pass.

`PITFALLS.md` in this directory has the failure modes that produced wrong
numbers here before, each with what it looked like and what fixed it.
Read it if a measurement looks surprising, and before writing any new
measuring code.
