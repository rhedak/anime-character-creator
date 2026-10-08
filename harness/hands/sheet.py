"""The standard sheet of `docs/hands-plan.md`: the owner's view of a set of candidates.

    ./harness/run.sh harness/hands/sheet.py OUTDIR mitten traced [more candidates]

Writes five images into OUTDIR, every candidate a lettered column, the first
column the baseline, so a pick is a letter:

    v1_crops.png    both hands at 5x on the five sheet presets
    v2_insert.png   the upper body at chapter-insert size (head radius about 21 px),
                    enlarged 3x with nearest-neighbour so the pixels show
    v3_heights.png  Krista's hands at heights 0.8 and 1.3
    v4_dark.png     Krista's hands in a dark skin tone
    v5_swung.png    Krista with each arm swung out 30 degrees
    v6_bare.png     clothes off, on the two neutral bases (never a named or younger
                    character, `CLAUDE.md`): where the hand meets a bare forearm
    v7_katherina.png  Katherina's two hands at 8x with the arm: the wide cuff and the staff

Candidates are registered in `candidates.py`.
"""

import os
import string
import sys
from dataclasses import replace

from candidates import pick
from handlib import DARK_SKIN, SHEET_PRESETS, crop_hand, label, render, with_height
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import NEUTRAL_BASES, PRESETS

S = 5  # px per canvas unit for the crops
TILE = 200
GAP = 4
HEAD = 22
ROWLAB = 78


def letters(cands):
    return [f"{string.ascii_uppercase[i]}: {c.label}" for i, c in enumerate(cands)]


def header(cols, width_each, row_label_w):
    im = Image.new("RGB", (row_label_w + sum(w + GAP for w in width_each), HEAD), "white")
    d = ImageDraw.Draw(im)
    x = row_label_w
    for text, w in zip(cols, width_each, strict=True):
        d.text((x + 4, 4), text, fill=(0, 0, 160))
        x += w + GAP
    return im


def stack(parts):
    im = Image.new("RGB", (max(p.width for p in parts), sum(p.height for p in parts)), "white")
    y = 0
    for p in parts:
        im.paste(p, (0, y))
        y += p.height
    return im


def row_of(cells, row_label_w, text):
    im = Image.new("RGB", (row_label_w + sum(c.width + GAP for c in cells), max(c.height for c in cells) + GAP), "white")
    ImageDraw.Draw(im).text((3, 4), text, fill=(200, 0, 0))
    x = row_label_w
    for c in cells:
        im.paste(c, (x, 0))
        x += c.width + GAP
    return im


def pair_cell(p, cand, scale=S, size=TILE):
    """Both hands of one candidate on one preset, side by side."""
    im, sk, centres = render(p, scale, cand)
    a = crop_hand(im, sk, centres[-1], scale, size=size)
    b = crop_hand(im, sk, centres[1], scale, size=size)
    cell = Image.new("RGB", (2 * size + 2, size), "white")
    cell.paste(a, (0, 0))
    cell.paste(b, (size + 2, 0))
    return cell


def v1(cands, out):
    cols = letters(cands)
    w = 2 * TILE + 2
    rows = [header(cols, [w] * len(cands), ROWLAB)]
    for name in SHEET_PRESETS:
        rows.append(row_of([pair_cell(PRESETS[name], c) for c in cands], ROWLAB, name))
    stack(rows).save(f"{out}/v1_crops.png")


def insert_cell(p, cand):
    sk_scale = 21.0 / render(p, 1, cand)[1].head_r  # px per unit for head radius 21
    im, sk, _ = render(p, sk_scale * 4, cand)
    im = im.resize((im.width // 4, im.height // 4), Image.LANCZOS)
    top = int(sk.shoulder_y * sk_scale - 5)
    bot = int(sk.hip_y * sk_scale + 1.6 * 21)
    left = int((sk.head_cx - 2.2 * sk.head_r) * sk_scale)
    right = int((sk.head_cx + 2.2 * sk.head_r) * sk_scale)
    t = im.crop((left, top, right, bot))
    return t.resize((t.width * 3, t.height * 3), Image.NEAREST)


def v2(cands, out):
    cols = letters(cands)
    cells_by_preset = {n: [insert_cell(PRESETS[n], c) for c in cands] for n in SHEET_PRESETS}
    w = cells_by_preset[SHEET_PRESETS[0]][0].width
    rows = [header(cols, [w] * len(cands), ROWLAB)]
    for n in SHEET_PRESETS:
        rows.append(row_of(cells_by_preset[n], ROWLAB, n))
    stack(rows).save(f"{out}/v2_insert.png")


def v3(cands, out):
    cols = letters(cands)
    w = 2 * TILE + 2
    rows = [header(cols, [w] * len(cands), ROWLAB)]
    for h in (0.8, 1.3):
        rows.append(row_of([pair_cell(with_height(PRESETS["krista"], h), c) for c in cands], ROWLAB, f"krista h{h}"))
    stack(rows).save(f"{out}/v3_heights.png")


def v4(cands, out):
    cols = letters(cands)
    w = 2 * TILE + 2
    rows = [header(cols, [w] * len(cands), ROWLAB)]
    p = replace(PRESETS["krista"], skin_tone=DARK_SKIN)
    rows.append(row_of([pair_cell(p, c) for c in cands], ROWLAB, "krista dark"))
    stack(rows).save(f"{out}/v4_dark.png")


def v5(cands, out):
    cols = letters(cands)
    w = 2 * TILE + 2
    rows = [header(cols, [w] * len(cands), ROWLAB)]
    k = PRESETS["krista"]
    rows.append(row_of([pair_cell(replace(k, right_arm_out=30.0, left_arm_out=30.0), c) for c in cands], ROWLAB, "krista 30"))
    stack(rows).save(f"{out}/v5_swung.png")


KEEP = ("boot_color", "underwear_color")


def clothes_off(p):
    """Every optional garment off; the base layer's underwear stays, as in the snapshot."""
    import dataclasses

    optional = [f.name for f in dataclasses.fields(c.Outfit) if f.name.endswith("_color") and f.name not in KEEP]
    return replace(p, outfit=replace(p.outfit, **dict.fromkeys(optional)))


def arm_cell(p, cand, side, scale=8, size=300, half=1.0):
    im, sk, centres = render(p, scale, cand)
    return crop_hand(im, sk, centres[side], scale, half_hr=half, size=size)


def v6(cands, out):
    cols = letters(cands)
    w = 300
    rows = [header(cols, [w] * len(cands), ROWLAB)]
    for nm, base in NEUTRAL_BASES.items():
        p = clothes_off(base)
        rows.append(row_of([arm_cell(p, c_, 1) for c_ in cands], ROWLAB, f"{nm} base"))
    stack(rows).save(f"{out}/v6_bare.png")


def v7(cands, out):
    cols = letters(cands)
    w = 360
    rows = [header(cols, [w] * len(cands), ROWLAB)]
    kat = PRESETS["katherina"]
    rows.append(row_of([arm_cell(kat, c_, -1, 8, 360, 1.1) for c_ in cands], ROWLAB, "staff hand"))
    rows.append(row_of([arm_cell(kat, c_, 1, 8, 360, 1.1) for c_ in cands], ROWLAB, "other hand"))
    stack(rows).save(f"{out}/v7_katherina.png")


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    cands = pick(sys.argv[2:])
    for fn in (v1, v2, v3, v4, v5, v6, v7):
        fn(cands, out)
    print("wrote", out, "for", [c.label for c in cands])


if __name__ == "__main__":
    main()
