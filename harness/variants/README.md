# Variants

Everything tried while reworking Satoshi's hair and legs, full size, both as
`.svg` and `.png`. Regenerate with `export_variants.py`, which sits next to this
file.

**None of the folders below exist until you run that script.** The tree lived
under `out/variants/` and went in the 2026-08-07 cleanup; the warning this file
used to carry, that a cleanup would take the script with it, is why the script
was promoted here first. What follows describes what a run rebuilds, and the
per-variant notes are the point of keeping it: they say what each candidate was
for and why it lost, which no rerun recovers. Note that the script still writes
its own copy of this text into `out/variants/README.md`, without this preamble.

Read the `compare/` sheets first. They are the same renders cropped and tiled,
and they are the point: each one settles a question by putting the candidates
next to `ref/satoshi.png` rather than by argument.

## One caveat about the superseded variants

Every variant here is rendered by the *current* skeleton, which has the
`hair_margin` headroom fix in it. So the ones named `as_committed` reproduce the
committed **shape** but not the committed **output**: the committed chibis had
the top of their hair sliced flat against the canvas edge, and these do not.
`committed_baseline/` holds the actual four committed renders for that
comparison, and `compare/headroom.png` shows the clipping directly.

## Folders

| Folder | What is in it |
| --- | --- |
| `committed_baseline/` | The four targets exactly as committed at `92736d0`, before any of this |
| `targets/` | The shipped four, plus each character at 4 heads |
| `compare/` | Side-by-side sheets, one per question settled |
| `hair/` | The short cut in eight states, worst to shipped, each at both builds |
| `hair_length/` | Lock length 0.45 / 0.65 / 0.85 / 1.00 on the winning shape |
| `hair_fade/` | Where the two tones meet, four depths |
| `hair_strand_weight/` | Strand line weight, 0 through 0.85 of the outline |
| `legs/` | Five leg profiles, both characters, both builds |
| `boots/` | Three foot-against-shaft ratios at the tall build |
| `cross_checks/` | A palette far from the defaults, each cut on the other character, flat mode |

## What shipped, and what each variant was for

**Hair**, in `hair/`:

1. `01_pot_as_committed` shape the complaint was about: the mass follows the
   skull, so hair and head are nearly the same outline, and there is no interior
   line anywhere.
2. `02_jagged_mass` pointed lock ends, still hugging the skull. Barely moves it.
3. `03_wedge_fringe` fringe in wedge locks. Big change, but the notches between
   them rise the whole way and it comes out as a row of teeth.
4. `04_wedges_plus_strands` first version that reads as hair.
5. `05_full_volume` the mass standing off the skull, softened notches.
6. `06_full_no_strands` **the control.** Everything above except the strands, and
   it is a pot again. This is what proved the strands carry it.
7. `07_crown_tufts_rejected` sharpened crown. Rejected: reads as notches cut into
   the hair, and the reference's crown is smooth anyway.
8. `08_shipped` 05 with the lock length and fade settled.

**Legs**, in `legs/`:

1. `01_cone_as_committed` 1.55 thigh to 0.55 ankle, a two-to-one cone.
2. `02_straight_tube` no taper at all. Beats the cone, which was the useful
   finding: the thigh was not too wide, the shin was too thin.
3. `03_measured` measured off `ref/satoshi.png`: 1.42 / 1.03 / 1.01 / 0.85 at
   thigh / knee / calf / ankle.
4. `04_measured_slim` the same with a 1.26 thigh instead of 1.42. Won on
   preference: the reference's leg sits on a hip wider than this skeleton's, so
   the full measurement came out heavy here.
5. `05_shipped` 04's widths, hung so the outer edge of the thigh lands on the
   hip, plus the boot from `boots/03`. 04 still overhangs the body's side there
   and carries the intermediate boot.

`targets/` is byte-identical to what `./render.sh --preset ...` writes, checked.

**Boots**, in `boots/`: the foot used to be a multiple of the ankle, so it
doubled the moment the leg stopped tapering to a point. `02` is the intermediate
where the shaft came out wider than the foot and the boot narrowed going down;
`03` shipped, with the foot measured off the leg instead.
