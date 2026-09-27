"""D4 of `docs/detail-plan.md`: a knee on the bare leg.

The bare leg (`_bare_seat` through `_seat_notch_d`, shared with the trousers)
runs thigh to knee to ankle with the calf only a control point, and its inside
is one curve from the ankle to the crotch, so it is a tube with no knee: the
adult taper it rides was measured on trousers, nearly straight below the thigh.
This draws the bare leg with a knee for the study: the leg narrows by
`inset` at the knee (outside and inside alike) and swells by `swell` into the
calf below it, the inside split at the knee into two curves; the crotch and
the trousers are left as they are.

The owner then asked for realistic ratios; measured, the firm knee left the
calf 1.12 and the ankle 1.0 of the knee (a real leg, front on: the upper thigh
1.4 to 1.6, the calf about 1, the ankle about 0.6). So a last row,
"realistic": the knee in by 0.10, the calf peaking about 1.03 of it (its
control 1.15), the bare ankle and foot to 0.70 of it (the boots keep theirs),
all with the height.

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
STATE = {"inset": 0.0, "swell": 0.0, "follow": False, "ankle": None, "calf": None}
FOOT = c._bare_foot


def strength(sk) -> float:
    return min(1.0, sk.limb_taper / 0.5) if STATE["follow"] else 1.0


def realistic_ankle(sk, w_ankle: float) -> float:
    """The bare ankle toward `STATE["ankle"]` of the (narrowed) knee."""
    if STATE["ankle"] is None:
        return w_ankle
    k = strength(sk)
    wk = sk.leg_half_w * (1.00 + 0.03 * c._limb_build(sk)) * (1 - STATE["inset"] * k)
    return w_ankle + (wk * STATE["ankle"] - w_ankle) * k


def bare_foot(sk, p, cx, w_ankle, side):
    return FOOT(sk, p, cx, realistic_ankle(sk, w_ankle), side)


def knee_notch(sk, cx, gap, top_y, crotch_y, w_top, w_knee, w_calf, w_ankle) -> str:
    k = strength(sk)
    inset, swell = STATE["inset"] * k, STATE["swell"] * k
    w_ankle = realistic_ankle(sk, w_ankle)
    if inset == 0 and swell == 0:
        return NOTCH(sk, cx, gap, top_y, crotch_y, w_top, w_knee, w_calf, w_ankle)
    calf_y = sk.knee_y + (sk.ankle_y - sk.knee_y) * 0.35
    knee_ctrl_y = sk.knee_y - (sk.knee_y - top_y) * 0.3
    wk = w_knee * (1 - inset)
    wc = w_calf * (1 + swell) + (w_calf - wk) * 0.6
    if STATE["calf"] is not None:
        wc = wk + (wk * STATE["calf"] - wk) * k
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


def booted(name):
    p = PRESETS[name]
    off = [n for n in c.Outfit.__dataclass_fields__ if n.endswith("_color") and n not in ("underwear_color", "boot_color")]
    return replace(p, outfit=replace(p.outfit, **dict.fromkeys(off)))


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
    c._bare_seat, c._bare_foot = bare_seat, bare_foot
    try:
        for label, inset, swell, follow, ankle, calf in (
            ("no knee", 0.0, 0.0, False, None, None),
            ("light", 0.05, 0.05, False, None, None),
            ("firm", 0.10, 0.08, False, None, None),
            ("firm, with height", 0.10, 0.08, True, None, None),
            ("realistic, with height", 0.10, 0.0, True, 0.70, 1.15),
        ):
            STATE.update(inset=inset, swell=swell, follow=follow, ankle=ankle, calf=calf)
            row = [legs(replace(base(n), height=h), f"{n} h{h}: {label}") for n in ("krista", "gero") for h in (0.8, 1.0, 1.3)]
            row.append(legs(replace(booted("krista"), height=1.3), f"krista booted h1.3: {label}"))
            rows.append(row)
    finally:
        c._bare_seat, c._bare_foot = BARE, FOOT
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
