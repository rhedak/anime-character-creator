"""What became what (`docs/hands-plan.md`, `docs/hands-status.md`).

The hands campaign prototyped every candidate here as a code variant that patched
`character` while it rendered, so the owner could compare them before anything
shipped. On 2026-10-08 the owner chose to keep them all as options and they were
built into `src/`, so this module's prototypes are gone and this note stays as the
map from the names in the status doc to the shipped styles:

| prototype | shipped as |
| --- | --- |
| K1, mitten with its tip notched into three fingers | `hand_style="notched"` |
| K2, the mitten's silhouette with two finger strokes | `hand_style="stroked"` |
| K3, a half-closed hand | `hand_style="curled"` |
| W3, the traced relaxed hand: length 0.36, stretched 2.0 across, wrist filling 1.1 of the cuff, squared at the wrist, fingertip slivers and interior lines dropped | `hand_style="traced"` |
| G2, the canon-style fist, kept upright against the arm's swing (0.85 of it) | `grip_style="fist"` |
| S, the traced hand shrunk to the gate's height | not shipped: the control that failed (outline share 55%, a third of the mitten's skin area) |
| W and W2, the traced hand stretched 1.6 and 2.0 times | W2's stretch is `_HAND_OPEN_STRETCH`; W was the step before |
| G1, the fist following the cuff's angle | not shipped: G2 is G1 at zero swing and more canon-like above it |

`ablate.py` ran on the old traced hand's pieces and is kept as a record of the
audit: it patches constants that no longer exist.
"""
