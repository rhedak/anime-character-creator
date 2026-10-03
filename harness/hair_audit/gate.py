"""The acceptance check for a new hair reference, before anything is traced
(`docs/detail-status.md`, D5 after the audit, step 2).

The new reference is meant to be `katherina_grok` (the tall-chibi design
reference `BODY_TYPES["tall_chibi"]` was measured off) with only the hair
changed. So it is compared against `katherina_grok` by this same code, a
difference of two measurements rather than one measurement against remembered
numbers, on the features the hair cannot reach:

- **the face**, the skin component seeded on the cheek: its widest row's width
  and the jaw's run, from the lowest row still at 90% of that width to the
  chin (the lower face, which the hair does not cover). Each gives a scale against
  `katherina_grok`'s face, and so a calibration in our head radii (that
  reference's own is the witch hat's, (650, 481) and 173.7 px per head
  radius). The trace skill's rule: the two scales agree within a few percent,
  or the head is drawn differently and one scale is a compromise.
- **the skirt hem**, the top of the legs (skin within 0.75 head radii of the
  centre line, more than two head radii below the chin, so the hands are out);
- **the soles**, the lowest lit row within one head radius of the centre line
  (the staff stands further out);
- **the skirt's half-width** a little above the hem.

Passes when the two scales agree within 5% and every landmark is within 0.1
head radii of `katherina_grok`'s. The chin is the anchor the head centre is
placed from, so it is printed but cannot fail. Prints the table, and writes
`out/hair_audit/gate_<name>.png`: the image, `katherina_grok` and our Katherina
at one head radius, the reference's hair placed by the calibration alone.

    ./harness/run.sh harness/hair_audit/gate.py PATH [--seed X,Y] [--name NAME]

`--seed` is a cheek pixel when the default (the largest skin component in the
upper half) picks something else. The controls, run first when this was
written: `katherina_grok` against itself passes with no difference, and
`katherina_grok_real` fails (soles 14.57 head radii against 5.94, the scales
78% apart, its lower face being longer). Off `katherina_grok` this code reads the soles at 5.941 and the
hem at 4.231, against the 5.94 and 4.26 `tall_chibi` records.
"""

import argparse
import io
from dataclasses import replace

import cairosvg
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/hair_audit"
BASE = "ref-local/katherina_grok/katherina_grok.jpg"
BASE_CAL = (650.0, 481.0, 173.7)
SKIN = np.array([248, 202, 167])
SCALE_TOL = 0.05
LANDMARK_TOL = 0.10
PX = 60
BOX = (-2.8, -2.2, 2.8, 6.4)


def skin_mask(a):
    return np.abs(a - SKIN).sum(2) < 60


def face(a, seed=None):
    """The face's skin component, holes filled: seeded, or the largest skin
    component in the upper half of the image."""
    lab, n = ndi.label(skin_mask(a))
    if seed is not None:
        f = lab == lab[seed[1], seed[0]]
    else:
        upper = lab[: a.shape[0] // 2]
        sizes = np.bincount(upper.ravel(), minlength=n + 1)
        sizes[0] = 0
        f = lab == int(np.argmax(sizes))
    return ndi.binary_fill_holes(f)


def measure(path, seed=None):
    """Pixel landmarks of one image: face centre x, widest row and its width,
    chin row, skirt hem row, sole row, skirt half-width above the hem."""
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    f = face(a, seed)
    widths = f.sum(1)
    wy = int(np.argmax(widths))
    row = np.nonzero(f[wy])[0]
    fw = int(row.max() - row.min())
    cx = (row.min() + row.max()) / 2
    chin = int(np.nonzero(f.any(1))[0].max())
    # The vertical scale is the jaw's run: from the lowest row still at 90% of
    # the face's width down to the chin. The widest row itself is no use here:
    # the face is at full width for some fifty rows, so which of them is the
    # widest turns on one pixel and moved by 49 rows between `katherina_grok`
    # and its hat-off redraw, whose faces otherwise match row for row.
    jaw = int(np.nonzero(widths >= 0.9 * widths.max())[0].max())
    run = chin - jaw
    # Provisional scale (px per face width) to place the windows below.
    s = fw / 2.0
    xs = np.arange(a.shape[1])
    near = np.abs(xs - cx) < 0.75 * s
    skin = skin_mask(a) & near[None, :]
    skin[: int(chin + 2 * s)] = False
    legs = np.nonzero(skin.any(1))[0]
    hem = int(legs.min()) if legs.size else None
    lit = a.sum(2) > 60
    lit_near = lit & (np.abs(xs - cx) < 1.0 * s)[None, :]
    soles = int(np.nonzero(lit_near.any(1))[0].max())
    skirt_w = None
    if hem is not None:
        y = int(hem - 0.15 * s)
        run_lit = np.nonzero(lit[y])[0]
        # The lit run containing the centre line.
        c0 = int(round(cx))
        if lit[y, c0]:
            left = c0 - np.argmax(~lit[y, c0::-1])
            right = c0 + np.argmax(~lit[y, c0:])
            skirt_w = (right - left) / 2
        elif run_lit.size:
            skirt_w = None
    return {
        "cx": cx,
        "widest": wy,
        "face_w": fw,
        "chin": chin,
        "run": run,
        "hem": hem,
        "soles": soles,
        "skirt_w": skirt_w,
    }


def calibrate(m, base):
    """`m`'s calibration in our head radii through the base reference's: the
    scale from face width and from the widest-row-to-chin run, and the head
    centre from the face-width scale."""
    _, oy, s0 = BASE_CAL
    sw = s0 * m["face_w"] / base["face_w"]
    sv = s0 * m["run"] / base["run"]
    chin_r = (base["chin"] - oy) / s0
    cy = m["chin"] - chin_r * sw
    return sw, sv, (m["cx"], cy)


def in_r(m, cal):
    s, _, (cx, cy) = cal
    out = {"chin": (m["chin"] - cy) / s, "soles": (m["soles"] - cy) / s}
    out["hem"] = (m["hem"] - cy) / s if m["hem"] is not None else float("nan")
    out["skirt half-width"] = m["skirt_w"] / s if m["skirt_w"] is not None else float("nan")
    return out


def tile(path, cal):
    s, _, (ox, oy) = cal
    img = Image.open(path).convert("RGB")
    k = PX / s
    img = img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)
    W, H = round((BOX[2] - BOX[0]) * PX), round((BOX[3] - BOX[1]) * PX)
    out = Image.new("RGB", (W, H), (0, 0, 0))
    out.paste(img, (round(-BOX[0] * PX - ox * k), round(-BOX[1] * PX - oy * k)))
    return out


def ours():
    p = PRESETS["katherina"]
    p = replace(p, familiar_color=None, outfit=replace(p.outfit, hat_color=None, hat_band_color=None, staff_color=None))
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="black")
    img = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode())))
    return tile_img(img, (sk.head_r, None, (sk.head_cx, sk.head_cy)))


def tile_img(img, cal):
    s, _, (ox, oy) = cal
    k = PX / s
    img = img.convert("RGB").resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)
    W, H = round((BOX[2] - BOX[0]) * PX), round((BOX[3] - BOX[1]) * PX)
    out = Image.new("RGB", (W, H), (0, 0, 0))
    out.paste(img, (round(-BOX[0] * PX - ox * k), round(-BOX[1] * PX - oy * k)))
    return out


def rules(im, label, marks):
    d = ImageDraw.Draw(im)
    W, H = im.size
    for yr in range(-2, 7):
        y = (yr - BOX[1]) * PX
        d.line([(0, y), (W, y)], fill=(80, 80, 80), width=1)
        d.text((2, y - 11), f"{yr}", fill=(255, 255, 0))
    for xr in (-1, 1):
        x = (xr - BOX[0]) * PX
        d.line([(x, 0), (x, H)], fill=(0, 120, 180), width=1)
    for name, v in marks.items():
        if name == "skirt half-width" or np.isnan(v):
            continue
        y = (v - BOX[1]) * PX
        d.line([(W - 40, y), (W, y)], fill=(0, 220, 0), width=3)
    d.text((4, H - 16), label, fill=(255, 255, 255))
    return im


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--seed", default=None)
    ap.add_argument("--name", default=None)
    args = ap.parse_args()
    seed = tuple(int(v) for v in args.seed.split(",")) if args.seed else None
    name = args.name or args.path.rsplit("/", 1)[-1].rsplit(".", 1)[0].replace(" ", "_")

    base = measure(BASE)
    new = measure(args.path, seed)
    base_cal = calibrate(base, base)
    new_cal = calibrate(new, base)
    sw, sv, _ = new_cal
    disagree = abs(sv - sw) / sw
    b, n = in_r(base, base_cal), in_r(new, new_cal)

    print(f"{name}: face-width scale {sw:.1f} px/r, vertical-run scale {sv:.1f} px/r, disagree {disagree:.1%}")
    ok = disagree <= SCALE_TOL
    print(f"  {'landmark':<18}{'katherina_grok':>16}{name[:16]:>18}{'diff':>8}")
    for k in b:
        d = n[k] - b[k]
        if k == "chin":
            # The head centre is placed from the chin, so it cannot disagree.
            print(f"  {k:<18}{b[k]:>16.3f}{n[k]:>18.3f}{'':>8}  anchor")
            continue
        good = abs(d) <= LANDMARK_TOL
        ok &= bool(good)
        print(f"  {k:<18}{b[k]:>16.3f}{n[k]:>18.3f}{d:>+8.3f}  {'ok' if good else 'FAIL'}")
    print(f"  {'PASS' if ok else 'FAIL'} (scales within {SCALE_TOL:.0%}, landmarks within {LANDMARK_TOL} r)")

    tiles = [
        rules(tile(args.path, (sw, None, new_cal[2])), name, n),
        rules(tile(BASE, (base_cal[0], None, base_cal[2])), "katherina_grok", b),
        rules(ours(), "ours, Katherina h1.0, hat off", {}),
    ]
    W, H = tiles[0].size
    sheet = Image.new("RGB", (W * 3 + 16, H), (128, 128, 128))
    for i, t in enumerate(tiles):
        sheet.paste(t, (i * (W + 8), 0))
    sheet.save(f"{OUT}/gate_{name}.png")
    print(f"  {OUT}/gate_{name}.png")


if __name__ == "__main__":
    main()
