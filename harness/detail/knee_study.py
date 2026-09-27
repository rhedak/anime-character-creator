"""D4 of `docs/detail-plan.md`: a knee on the bare leg.

The bare leg (`_bare_seat` through `_seat_notch_d`, shared with the trousers)
runs thigh to knee to ankle with the calf only a control point, and its inside
is one curve from the ankle to the crotch, so it is a tube with no knee: the
adult taper it rides was measured on trousers, nearly straight below the thigh.
This draws the bare leg with a knee for the study: the leg narrows by
`inset` at the knee (outside and inside alike) and swells by `swell` into the
calf below it, the inside split at the knee into two curves; the crotch and
the trousers are left as they are.

Rows: no knee (today); a light knee (inset 0.05, swell 0.05 of the leg's
half-width); a firm one (0.10, 0.08); the firm one scaled by the limb taper
(`Skeleton.limb_taper / 0.5`: none at height 0.8, full from 1.3), so a short
figure keeps the chibi's plain leg. Columns: Krista and Gero in the base
layer, barefoot (adults), at heights 0.8, 1.0 and 1.3, the legs at 2x.
Writes `out/detail/knee_study.png`.
"""

import io
import os
from dataclasses import replace

import cairosvg
from PIL import Image, ImageDraw

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

OUT = "out/detail"
NOTCH = c._seat_notch_d
BARE = c._bare_seat
STATE = {"inset": 0.0, "swell": 0.0, "follow": False}


def knee_notch(sk, cx, gap, top_y, crotch_y, w_top, w_knee, w_calf, w_ankle) -> str:
    k = 1.0
    if STATE["follow"]:
        k = min(1.0, sk.limb_taper / 0.5)
    inset, swell = STATE["inset"] * k, STATE["swell"] * k
    if inset == 0 and swell == 0:
        return NOTCH(sk, cx, gap, top_y, crotch_y, w_top, w_knee, w_calf, w_ankle)
    calf_y = sk.knee_y + (sk.ankle_y - sk.knee_y) * 0.35
    knee_ctrl_y = sk.knee_y - (sk.knee_y - top_y) * 0.3
    wk = w_knee * (1 - inset)
    wc = w_calf * (1 + swell) + (w_calf - wk) * 0.6
    thigh_in_y = crotch_y + (sk.knee_y - crotch_y) * 0.5

    def outer_down(s):
        return (
            f"Q {cx + s * (gap + w_top):.1f} {knee_ctrl_y:.1f} {cx + s * (gap + wk):.1f} {sk.knee_y:.1f} "
            f"Q {cx + s * (gap + wc):.1f} {calf_y:.1f} {cx + s * (gap + w_ankle):.1f} {sk.ankle_y:.1f} "
        )

    def inner_up(s):
        return (
            f"L {cx + s * (gap - w_ankle):.1f} {sk.ankle_y:.1f} "
            f"Q {cx + s * (gap - wc):.1f} {calf_y:.1f} {cx + s * (gap - wk):.1f} {sk.knee_y:.1f} "
            f"Q {cx + s * (gap - w_top):.1f} {thigh_in_y:.1f} {cx:.1f} {crotch_y:.1f} "
        )

    def inner_down(s):
        return (
            f"Q {cx + s * (gap - w_top):.1f} {thigh_in_y:.1f} {cx + s * (gap - wk):.1f} {sk.knee_y:.1f} "
            f"Q {cx + s * (gap - wc):.1f} {calf_y:.1f} {cx + s * (gap - w_ankle):.1f} {sk.ankle_y:.1f} "
            f"L {cx + s * (gap + w_ankle):.1f} {sk.ankle_y:.1f} "
        )

    def outer_up(s):
        return (
            f"Q {cx + s * (gap + wc):.1f} {calf_y:.1f} {cx + s * (gap + wk):.1f} {sk.knee_y:.1f} "
            f"Q {cx + s * (gap + w_top):.1f} {knee_ctrl_y:.1f} {cx + s * (gap + w_top):.1f} {top_y:.1f} "
        )

    w_waist = gap + w_top
    return (
        f"M {cx - w_waist:.1f} {top_y:.1f} L {cx + w_waist:.1f} {top_y:.1f} "
        + outer_down(1) + inner_up(1) + inner_down(-1) + outer_up(-1) + "Z"
    )


def bare_seat(*a, **k):
    c._seat_notch_d = knee_notch
    try:
        return BARE(*a, **k)
    finally:
        c._seat_notch_d = NOTCH


def base(name):
    p = PRESETS[name]
    off = [n for n in c.Outfit.__dataclass_fields__ if n.endswith("_color") and n != "underwear_color"]
    return replace(p, outfit=replace(p.outfit, **dict.fromkeys(off)))


def legs(p, label):
    sk = c.skeleton_for(p)
    svg = c.render_character(p, sk, background="#ffffff")
    im = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=2))).convert("RGB")
    r, cx = sk.head_r * 2, sk.head_cx * 2
    t = im.crop((int(cx - 1.1 * r), int(sk.hip_y * 2 - 0.2 * r), int(cx + 1.1 * r), int(sk.foot_y * 2 + 0.1 * r)))
    h = 520
    t = t.resize((int(t.width * h / t.height), h), Image.LANCZOS)
    ImageDraw.Draw(t).text((3, 3), label, fill=(200, 0, 0))
    return t


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    c._bare_seat = bare_seat
    try:
        for label, inset, swell, follow in (
            ("no knee", 0.0, 0.0, False),
            ("light", 0.05, 0.05, False),
            ("firm", 0.10, 0.08, False),
            ("firm, with height", 0.10, 0.08, True),
        ):
            STATE.update(inset=inset, swell=swell, follow=follow)
            rows.append([legs(replace(base(n), height=h), f"{n} h{h}: {label}") for n in ("krista", "gero") for h in (0.8, 1.0, 1.3)])
    finally:
        c._bare_seat = BARE
    tw = max(t.width for r in rows for t in r)
    th = max(t.height for r in rows for t in r)
    sheet = Image.new("RGB", (len(rows[0]) * (tw + 3), len(rows) * (th + 5)), (190, 190, 190))
    for j, r in enumerate(rows):
        for i, t in enumerate(r):
            sheet.paste(t, (i * (tw + 3), j * (th + 5)))
    sheet.save(f"{OUT}/knee_study.png")
    print(f"{OUT}/knee_study.png", sheet.size)


if __name__ == "__main__":
    main()
