"""One lock over each shoulder (the owner, 2026-09-29).

On `katherina_grok_real` one lock a side hangs over the shoulder onto the
chest; the rest of that side's hair goes behind the shoulder and the arm.
`hair_with_human_shape.png` keeps every lock in front, so on our narrower
body they all draw over the arms.

The cut is made in the new reference's pixels, then refitted. Above our
shoulder line the front piece is unchanged (the fringe and the curtains).
Below it each side keeps only its innermost lock, the one against the body:
the original's front lock measures 0.36 head radii wide, so the band kept is
`LOCK_W` from that inner edge, ending where the hair itself gaps.

Rewrites `front`, `front_parts` and `front_edges` in `out/hair_only/hair.json`,
and which strands are in front. The mass is untouched. Writes
`out/hair_only/shoulders.png`: kept (green) against dropped (red).
"""

import json
import sys

sys.path.insert(0, "harness/hair_only")
sys.path.insert(0, "harness/trace_hair")

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

import trace as T
import trace_lib as tl
from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS  # noqa: E402

OUT = "out/hair_only"
ORIGIN, S = T.ORIGIN, T.S
# The original's front lock measures 0.36 head radii wide.
LOCK_W = 0.38
# How far the lock's inner edge may move in one row, in the new reference's
# pixels, before it counts as a different lock.
STEP = 12


def main() -> None:
    reg = json.load(open(f"{OUT}/register.json"))
    sc, (dx, dy) = reg["scale"], tuple(reg["offset"])
    hair = json.load(open(f"{OUT}/hair.json"))
    k = hair["squeeze"]

    img = np.asarray(Image.open(f"{T.DIR}/hair_only.png").convert("RGBA")).astype(float)
    full = T.alpha("hair_only") | T.alpha("hair_with_human_shape")
    front = T.alpha("hair_with_human_shape")
    ow = T.outline_width(img, full)
    half = max(1, int(round(ow / 2)))
    front_c = ndi.binary_erosion(front, iterations=half)

    import dataclasses

    sk = c.skeleton_for(dataclasses.replace(PRESETS["katherina"], height=T.HEIGHT))
    our_sh = (sk.shoulder_y - sk.head_cy) / sk.head_r
    # Our shoulder, back through the squeeze, in the new reference's rows.
    ref_sh = T.CHEEK + (our_sh - T.CHEEK) / k
    row = int(round((ORIGIN[1] + ref_sh * S - dy) / sc))
    print(f"shoulder: ours {our_sh:.3f}, old reference {ref_sh:.3f}, new row {row}")

    # Below the shoulder, the innermost band of the front hair: one lock wide,
    # from the edge against the body outward. The band ends early where the
    # hair itself gaps (a lock's tip), and its outer edge is smoothed so the
    # cut does not step row by row.
    width = LOCK_W * S / sc
    ox_new = (ORIGIN[0] - dx) / sc
    kept_below = np.zeros_like(front_c)
    for side in (-1, 1):
        xs0 = np.nonzero(front_c[row])[0]
        xs0 = xs0[xs0 < ox_new] if side < 0 else xs0[xs0 > ox_new]
        edge = float(xs0.max() if side < 0 else xs0.min())
        outer = np.full(front_c.shape[0], np.nan)
        inner = np.full(front_c.shape[0], np.nan)
        for y in range(row, front_c.shape[0]):
            xs = np.nonzero(front_c[y])[0]
            xs = xs[np.abs(xs - edge) <= max(STEP, width)]
            xs = xs[xs < ox_new] if side < 0 else xs[xs > ox_new]
            if not len(xs):
                break
            edge = float(xs.max() if side < 0 else xs.min())
            reach = edge - width if side < 0 else edge + width
            band = xs[xs >= reach] if side < 0 else xs[xs <= reach]
            if side < 0:
                cuts = np.nonzero(np.diff(band) > 6)[0]
                band = band[cuts[-1] + 1 :] if len(cuts) else band
            else:
                cuts = np.nonzero(np.diff(band) > 6)[0]
                band = band[: cuts[0] + 1] if len(cuts) else band
            inner[y], outer[y] = edge, (band.min() if side < 0 else band.max())
        for arr in (inner, outer):
            known = np.nonzero(~np.isnan(arr))[0]
            if len(known) > 5:
                arr[known] = ndi.median_filter(arr[known], size=15)
        for y in range(row, front_c.shape[0]):
            if np.isnan(inner[y]):
                continue
            lo, hi = sorted((int(round(inner[y])), int(round(outer[y]))))
            kept_below[y, lo : hi + 1] = True
        print(f"side {side:+d}: lock followed for {(~np.isnan(inner[row:])).sum()} rows")
    kept_below &= front_c
    print(f"one lock: {width:.0f} px ({LOCK_W} head radii) wide")
    new_front = front_c.copy()
    new_front[row:] = kept_below[row:]
    # A tip of some other lock can fall inside the band once the tracked lock
    # ends. Only what touches the hair above the shoulder stays.
    above = new_front.copy()
    above[row:] = False
    lab, n = ndi.label(new_front)
    keep = np.unique(lab[ndi.binary_dilation(above, iterations=3)])
    new_front = np.isin(lab, keep[keep > 0])
    new_front = ndi.binary_opening(new_front, iterations=1)

    def to_head(pts):
        out = []
        for x, y in pts:
            hx = (x * sc + dx - ORIGIN[0]) / S
            hy = (y * sc + dy - ORIGIN[1]) / S
            out.append((hx, T.CHEEK + (hy - T.CHEEK) * k if hy > T.CHEEK else hy))
        return out

    def parts(mm, min_px=200):
        res = []
        lab_p, n_p = ndi.label(mm)
        for i in range(1, n_p + 1):
            piece = lab_p == i
            if piece.sum() < min_px:
                continue
            outer = tl.fit_closed(to_head(tl.boundary(piece)), T.TOL_SHAPE)
            holes = []
            hl, nh = ndi.label(ndi.binary_fill_holes(piece) & ~piece)
            for j in range(1, nh + 1):
                if (hl == j).sum() >= min_px:
                    holes.append(tl.fit_closed(to_head(tl.boundary(hl == j)), T.TOL_SHAPE))
            res.append([outer, holes])
        return res

    front_parts = parts(new_front)
    largest = max(front_parts, key=lambda pr: len(pr[0][1]))[0]
    print(f"front: {len(front_parts)} pieces, {sum(len(h) for _, h in front_parts)} holes")

    # A strand is in front when its middle lies in the new front piece.
    def in_front(chain):
        pts = [chain[0], *[e for _, e in chain[1]]]
        hx, hy = pts[len(pts) // 2]
        hy = T.CHEEK + (hy - T.CHEEK) / k if hy > T.CHEEK else hy
        x = (hx * S + ORIGIN[0] - dx) / sc
        y = (hy * S + ORIGIN[1] - dy) / sc
        xi, yi = int(round(x)), int(round(y))
        if not (0 <= yi < new_front.shape[0] and 0 <= xi < new_front.shape[1]):
            return False
        return bool(new_front[yi, xi])

    n_front = 0
    for st in hair["strands"]:
        st["front"] = in_front(st["chain"])
        n_front += st["front"]
    print(f"strands in front: {n_front} of {len(hair['strands'])}")

    hair["front_parts"] = front_parts
    hair["front"] = largest
    hair["front_edges"] = [largest]
    json.dump(hair, open(f"{OUT}/hair.json", "w"), indent=1)

    view = np.where(front[..., None], np.clip(img[..., :3] * 2.2, 0, 255), 255)
    view[front_c & ~new_front] = (220, 60, 60)
    view[new_front] = (60, 180, 70)
    im = Image.fromarray(view.astype(np.uint8))
    ImageDraw.Draw(im).line([(0, row), (im.width, row)], fill=(255, 255, 0), width=3)
    im.crop((200, 250, 1120, 1450)).resize((690, 900)).save(f"{OUT}/shoulders.png")
    print(f"{OUT}/shoulders.png")


if __name__ == "__main__":
    main()
