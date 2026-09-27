"""D4d H0 of `docs/detail-plan.md`: calibrate the reference's two hands.

Each hand's frame is its wrist: where the skin meets the sleeve's cuff. For
each hand this takes the skin component seeded inside it, finds its pixels
touching the sleeve's navy (the cuff line), fits a line through them (the
wrist, its centre and width), and takes the direction into the hand as the
line's normal pointing at the skin's mass. The hand's length is how far the
skin reaches along that direction. Our mitten's wrist and length come from
`_arms` and `_hand` in the same units, for the size question the owner left
for later.

Writes `out/trace_hands/calib.png` (the reference with each wrist line and
direction drawn) and `out/trace_hands/calib.json`, and prints the numbers.
"""

import json

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

REF = "ref-local/katherina_grok_real/katherina_grok_real.png"
OUT = "out/trace_hands"
# A pixel inside each hand's skin, a box the component is kept to, and the box
# the wrist is looked for in: where the skin meets the cuff, read off the
# gridded close-ups (`out/trace_hands/grid_*.png`). The sleeve and the dress
# are the same navy and the page is near black, so "skin touching navy" alone
# ran down the whole side of the relaxed hand.
HANDS = {
    "grip": {"seed": (410, 760), "box": (330, 690, 450, 810), "cuff": (424, 722, 446, 796)},
    "relaxed": {"seed": (820, 880), "box": (780, 840, 900, 990), "cuff": (796, 848, 846, 868)},
}


def skin_mask(a: np.ndarray, seed: tuple[int, int], box) -> np.ndarray:
    col = a[seed[1], seed[0]].astype(int)
    m = np.abs(a.astype(int) - col).sum(2) < 110
    x0, y0, x1, y1 = box
    keep = np.zeros_like(m)
    keep[y0:y1, x0:x1] = True
    # Closed first, so the hand's own interior lines (between the grip's finger
    # rolls) do not cut it into pieces: the trace skill's step 3.
    closed = ndi.binary_closing(m & keep, iterations=3)
    lab, _ = ndi.label(closed)
    return ndi.binary_fill_holes(lab == lab[seed[1], seed[0]])


def measure(a: np.ndarray, spec) -> dict:
    hand = skin_mask(a, spec["seed"], spec["box"])
    x0, y0, x1, y1 = spec["cuff"]
    cuff = np.zeros_like(hand)
    cuff[y0:y1, x0:x1] = True
    edge = hand & ~ndi.binary_erosion(hand) & cuff
    ys, xs = np.nonzero(edge)
    pts = np.stack([xs, ys], 1).astype(float)
    centre = pts.mean(0)
    _u, _s, vt = np.linalg.svd(pts - centre)
    along = vt[0]
    width = float(np.ptp((pts - centre) @ along))
    normal = np.array([-along[1], along[0]])
    hys, hxs = np.nonzero(hand)
    mass = np.stack([hxs, hys], 1).astype(float)
    if ((mass - centre) @ normal).mean() < 0:
        normal = -normal
    length = float(((mass - centre) @ normal).max())
    return {
        "wrist_centre": centre.tolist(),
        "wrist_width": width,
        "into_hand": normal.tolist(),
        "across": along.tolist(),
        "length": length,
        "length_over_width": length / width,
        "area_px": int(hand.sum()),
    }


def ours() -> dict:
    p = PRESETS["katherina"]
    sk = c.skeleton_for(p)
    _top, _elbow, centre_wrist, wrist_y = c._arm_line(sk)
    lb = c._limb_build(sk)
    w_wrist = sk.arm_half_w * (1.0 - 0.34 * lb)
    hw = w_wrist * 1.02
    length = c._hand_length(sk)
    return {"wrist_width": 2 * hw, "length": length, "length_over_width": length / (2 * hw), "head_r": sk.head_r}


def main() -> None:
    a = np.asarray(Image.open(REF).convert("RGB"))
    out = {name: measure(a, spec) for name, spec in HANDS.items()}
    out["ours_mitten"] = ours()
    im = Image.fromarray(a).convert("RGB")
    d = ImageDraw.Draw(im)
    for name in HANDS:
        m = out[name]
        cx, cy = m["wrist_centre"]
        ax, ay = m["across"]
        nx, ny = m["into_hand"]
        hw = m["wrist_width"] / 2
        d.line([(cx - ax * hw, cy - ay * hw), (cx + ax * hw, cy + ay * hw)], fill=(255, 0, 0), width=2)
        d.line([(cx, cy), (cx + nx * m["length"], cy + ny * m["length"])], fill=(0, 255, 0), width=2)
    x0, y0, x1, y1 = 300, 660, 920, 1000
    im.crop((x0, y0, x1, y1)).resize(((x1 - x0) * 2, (y1 - y0) * 2), Image.NEAREST).save(f"{OUT}/calib.png")
    with open(f"{OUT}/calib.json", "w") as f:
        json.dump(out, f, indent=2)
    for k, v in out.items():
        print(k, {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.items() if kk not in ("across",)})


if __name__ == "__main__":
    main()
