"""D5 plan, steps 4 and 5: the parted cut (`long_parted`) on our figures, beside
its reference at one head radius.

Groups, one sheet each, `out/hair_parted/compare_<group>.png`:

- `katherina`: the reference (`katherina_grok_nohat`, on `gate.py`'s
  calibration), then Katherina in `long_parted` without her hat at her preset
  `hair_length` (0.83) and at the trace's own length, with the hat, and in
  `long_traced` as she is today.
- `cast`: every preset that wears `long_traced`, switched to `long_parted` at
  its own `hair_length`, and as it is today underneath.
- `heights`: Katherina without the hat at 0.8, 1.0, 1.15 and 1.3.
- `palettes`: Katherina's cut in blonde, near black and Satoko's pale tips.
- `small`: the insert size (head radius 21 px), 1x and 2x, shown 2x.

    ./harness/run.sh harness/hair_parted/compare.py [--only GROUP]
"""

import io
import sys
from dataclasses import replace

sys.path.insert(0, "harness/hair_audit")

import cairosvg
from PIL import Image, ImageDraw

import gate
from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/hair_parted"
REF = "ref-local/katherina_grok_nohat/katherina_grok_nohat.png"
PX = 80
BOX = (-2.3, -1.9, 2.3, 4.2)
GROUPS = ("katherina", "cast", "heights", "palettes", "small")


def frame():
    return round((BOX[2] - BOX[0]) * PX), round((BOX[3] - BOX[1]) * PX)


def place(img, cx, cy, r):
    k = PX / r
    img = img.convert("RGBA").resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)
    W, H = frame()
    out = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    out.alpha_composite(img, (round(-BOX[0] * PX - cx * k), round(-BOX[1] * PX - cy * k)))
    return out.convert("RGB")


def render(p):
    sk = c.skeleton_for(p)
    png = cairosvg.svg2png(bytestring=c.render_character(p, sk).encode(), scale=2)
    return place(Image.open(io.BytesIO(png)), sk.head_cx * 2, sk.head_cy * 2, sk.head_r * 2)


def reference():
    base = gate.measure(gate.BASE)
    m = gate.measure(REF)
    s, _, (ox, oy) = gate.calibrate(m, base)
    return place(Image.open(REF), ox, oy, s)


def label(im, text):
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, im.width, 14], fill=(255, 255, 255))
    d.text((3, 2), text, fill=(200, 0, 0))
    return im


def trace_length(p):
    """The `hair_length` at which `p`'s fall is the trace's own."""
    sk = c.skeleton_for(p)
    chin = sk.head_cy + sk.head_r
    tip = sk.head_cy + c._PARTED_BASE_TIP * sk.head_r
    return (tip - chin) / (sk.hip_y - chin)


def no_hat(p):
    return replace(p, outfit=replace(p.outfit, hat_color=None, hat_band_color=None))


def parted(p, **kw):
    return replace(p, hairstyle="long_parted", **kw)


def preset(name):
    """A preset; Katherina without her side tail, which the owner switched off
    with this cut (2026-10-03). Anyone else keeps theirs: Krista's ponytail is
    the same part."""
    p = PRESETS[name]
    return replace(p, hair_tail=0.0) if name == "katherina" else p


def group(name):
    kat = preset("katherina")
    if name == "katherina":
        bare = no_hat(kat)
        return [
            [
                (reference(), "reference: katherina_grok_nohat"),
                (render(parted(bare)), "long_parted, hair_length 0.83"),
                (render(parted(bare, hair_length=round(trace_length(bare), 3))), "long_parted at the trace's length"),
                (render(parted(kat)), "long_parted, hat"),
                (render(no_hat(PRESETS["katherina"])), "today: long_traced"),
            ]
        ]
    if name == "cast":
        wearers = [k for k, p in PRESETS.items() if p.hairstyle == "long_traced"]
        return [
            [(render(parted(preset(k))), f"{k} {PRESETS[k].hair_length}") for k in wearers],
            [(render(PRESETS[k]), f"{k} today") for k in wearers],
        ]
    if name == "heights":
        bare = parted(no_hat(kat))
        return [[(render(replace(bare, height=h)), f"katherina h{h}") for h in (0.8, 1.0, 1.15, 1.3)]]
    if name == "palettes":
        bare = parted(no_hat(kat))
        sat = PRESETS["satoko"]
        return [
            [
                (render(replace(bare, hair_color="#e3b448")), "blonde"),
                (render(replace(bare, hair_color="#1d1b22")), "near black"),
                (render(replace(bare, hair_color=sat.hair_color, hair_tip_color=sat.hair_tip_color)), "satoko's tips"),
                (render(parted(sat)), "satoko"),
            ]
        ]
    if name == "small":
        row = []
        for p, text in ((parted(kat), "hat"), (parted(no_hat(kat)), "no hat")):
            sk = c.skeleton_for(p)
            for dpr in (1, 2):
                scale = dpr * 21 / sk.head_r
                png = cairosvg.svg2png(bytestring=c.render_character(p, sk, background="white").encode(), scale=scale)
                im = Image.open(io.BytesIO(png)).convert("RGB")
                im = im.resize((im.width * 2 // dpr, im.height * 2 // dpr), Image.NEAREST)
                row.append((im, f"{text} {dpr}x"))
        return [row]
    raise SystemExit(f"unknown group {name}")


def sheet(rows, path):
    tiles = [[label(im.copy(), t) for im, t in row] for row in rows]
    W = max(sum(t.width + 6 for t in row) for row in tiles)
    H = sum(max(t.height for t in row) + 6 for row in tiles)
    out = Image.new("RGB", (W, H), (150, 150, 150))
    y = 0
    for row in tiles:
        x = 0
        for t in row:
            out.paste(t, (x, y))
            x += t.width + 6
        y += max(t.height for t in row) + 6
    out.save(path)
    print(path, out.size)


def main() -> None:
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    for g in GROUPS:
        if only and g != only:
            continue
        sheet(group(g), f"{OUT}/compare_{g}.png")


if __name__ == "__main__":
    main()
