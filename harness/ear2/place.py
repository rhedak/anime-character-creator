"""Where the owner's ear crop came from, and at what scale.

Same job the fringe crop needed: a crop on its own says nothing about size, and
every measurement off it has to end up in head radii, so it has to be put back
into the sheet it was cut from first.

The sheet is `satoshi-chibi.jpg`, settled by eye before this ran: the chibi is
the only one of the three that draws the ear with a heavy black rim, and its
viewer-right ear has the crop's own Y-fold in it. `satoshi-real.jpg` draws the
same ear with hair across it and `satoshi.png` draws it in thin grey line.

Matched on ink alone. The crop's alpha is a hand selection whose edge is nowhere
near the drawing's, and the crop carries a stripe of the hair's white tip along
one side, so the score is the share of pixels where the two masks disagree, and
a few percent of disagreement is the selection, not a bad fit.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

REF = Path(__file__).resolve().parents[2] / "ref"
SHEET = "satoshi-chibi.jpg"
# The neighbourhood of the viewer-right ear, generous. A full-sheet sweep at
# every scale is minutes of work for an answer that is already this narrow.
WINDOW = (540, 320, 700, 480)


def ink(im: Image.Image) -> list[list[bool]]:
    rgb = im.convert("RGB")
    w, h = rgb.size
    px = rgb.load()
    if im.mode == "RGBA":
        a = im.load()
        return [[sum(px[x, y]) < 330 and a[x, y][3] > 128 for x in range(w)] for y in range(h)]
    return [[sum(px[x, y]) < 330 for x in range(w)] for y in range(h)]


sheet = Image.open(REF / SHEET)
big = ink(sheet)
crop = Image.open(REF / "satoshi-ear.png")

best = None
for step, scales in (
    (2, [i / 200 for i in range(16, 40, 2)]),
    (1, None),
):
    if scales is None:
        f0 = best[1]
        scales = [f0 + i / 1000 for i in range(-9, 10)]
    for f in scales:
        sw, sh = round(crop.width * f), round(crop.height * f)
        small = ink(crop.resize((sw, sh), Image.LANCZOS))
        for oy in range(WINDOW[1], WINDOW[3] - sh, step):
            for ox in range(WINDOW[0], WINDOW[2] - sw, step):
                bad = 0
                for y in range(sh):
                    row, brow = small[y], big[oy + y]
                    for x in range(sw):
                        if row[x] != brow[ox + x]:
                            bad += 1
                s = bad / (sw * sh)
                if best is None or s < best[0]:
                    best = (s, f, ox, oy, sw, sh)

err, f, ox, oy, sw, sh = best
print(f"{SHEET}: disagreement {err:.3f}  scale {f:.3f}  at ({ox},{oy})  size {sw}x{sh}")

# The fit, drawn back on the sheet, because a number this small is worth seeing.
shot = sheet.convert("RGB").crop((ox - 40, oy - 40, ox + sw + 40, oy + sh + 40))
over = crop.resize((sw, sh), Image.LANCZOS)
tint = Image.new("RGBA", over.size, (255, 0, 160, 255))
tint.putalpha(over.getchannel("A").point(lambda v: 130 if v > 128 else 0))
shot = shot.convert("RGBA")
shot.alpha_composite(tint, (40, 40))
shot.resize((shot.width * 4, shot.height * 4), Image.LANCZOS).save(
    Path(__file__).resolve().parent / "place.png"
)
print("wrote out/ear2/place.png")
