# Tracing the ear off the owner's crop

Run from the repo root. Only `band.py` needs cairo, so only that one
wants `DYLD_FALLBACK_LIBRARY_PATH=":/opt/homebrew/lib"` in front.

| Script | What it does |
| --- | --- |
| `place.py` → `place.png` | finds where `ref/satoshi-ear.png` came from and at what scale, and draws the fit back on |
| `trace.py` → `check.png` | the rim, as the rightmost ink in each row, fitted and drawn back on |
| `inner.py` → `inner.png` | the fold, isolated by eroding the silhouette until the rim is gone, then walked to its centreline |
| `band.py` | solves where the fold's band sits across an ear narrower than the canon's, and prints the attach chord's tilt |
| `depth.png` | the canon beside both z-orders: the ear over the head, and under it |
| `shipped.png` | the two heads that show an ear, as they now render |

`fold.py` is kept as a record of a reading that does not work: taking the
second run of ink along each row hops between the upper crescent, the
hook and the rim, and comes out a zigzag lying on none of the three.

## What it is a crop of

`satoshi-chibi.jpg`, the viewer-right ear, at (579, 355) and 76x110
pixels. The chibi is the only one of the three sheets that draws the ear
with a heavy black rim: the adult photo has hair across it and
`satoshi.png` draws it in thin grey line. Settled by eye first and then
by template match, 0.101 disagreement, which is the hand-cut alpha rather
than a bad fit.

Everything is traced off the **sheet pixels under the crop's alpha**,
never off the crop itself. The crop is a 4.3x resample of a 76x110 patch,
so it carries nothing the sheet does not, plus the resampler's ringing
and a selection edge that clips the rim at the bottom left. The alpha is
used only to say which ink is ear and which is the hair lock beside it.

## What it said

- The rim runs 0.024 to 0.614 head radii, against the adult's 0.03 to
  0.49. A chibi's ear is about 30% taller against its skull.
- It stands 0.213 r clear of the chord between its attach points, which
  is 0.361 of its own height. Ours was already 0.370, so the width we had
  by eye was right and was left alone.
- It is widest at 0.50 of its height, not the adult's 0.59.
- The fold reaches a third of the stand-out *left* of the attach chord,
  because the canon's ear overlaps the cheek. Ours is welded to the skull
  and has no room there, so the fold's shape is kept and the band it
  lands in is solved for: the widest one that keeps every point of it a
  crease's width clear of both the skull and the rim at both builds. It
  comes out 0.30 to 0.75 of the stand-out, with a hundredth of slack. The
  band picked by eye first was infeasible at the adult.
- The attach chord is 16 degrees off vertical at the chibi and 19 at the
  adult, so the stand-out is measured along x deliberately rather than
  perpendicular to it.
- The canon draws the face's outline *across* the ear, one unbroken heavy
  line with the ear behind it. Ours was over the head, where the rim ran
  into that outline and joined it. `depth.png` is the three side by side
  and the ear now sits under `_head`.
