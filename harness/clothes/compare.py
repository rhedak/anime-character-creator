"""Score a character's garments against katherina_grok.jpg, region by region.

The acceptance number for every milestone of `docs/katherina-clothes-plan.md`.
Run from the repo root:

    ./harness/run.sh harness/clothes/compare.py [preset] [region ...]

Ours: the character rendered with every garment in its own key colour (no hat,
no staff, which cross the body), so no two surfaces can be confused the way the
hat's and the skirt's near-blacks are. Reference: the fill components the
reference's outlines separate (ids as `harness/body/landmarks.py` lists them).
Both are resampled onto one grid in head radii, on the hat's calibration for the
reference and the skeleton for ours, and each region reports:

  iou   overlap of the two masks, 1.0 identical
  dist  mean distance from each mask's boundary to the other's, head radii
        (symmetric), which is what a misplaced edge actually costs

Pixels either figure's hair covers are left out of both: our hair is not the
reference's, and a garment hidden by one and not the other is not a garment
error. Writes `out/clothes/<preset>_<region>.png` overlays (reference outline
green, ours magenta) and a side-by-side of the key-colour render.
"""

from __future__ import annotations

import dataclasses
import io
import sys
from pathlib import Path

import cairosvg
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

REF = Path(__file__).resolve().parents[3] / "time_slider_katherina/style-anchors/katherina_grok/katherina_grok.jpg"
OX, OY, SC = 650.0, 481.0, 173.7
GRID = 100  # px per head radius on the comparison grid
X0, X1, Y0, Y1 = -2.0, 2.0, 0.6, 6.1
OUT = Path("out/clothes")

KEY = {
    "collar": "#ff0000",
    "coat": "#00ff00",
    "tunic": "#0000ff",
    "skirt": "#ffff00",
    "belt": "#ff00ff",
    "boots": "#ff8000",
    "skin": "#00ffff",
    "hair": "#808080",
}

# Region -> (reference component ids, our key colours). A region is what the
# eye reads as one piece of clothing, whichever of our parts draws it.
REGIONS: dict[str, tuple[tuple[int, ...], tuple[str, ...]]] = {
    "collar": ((175, 176), ("collar",)),
    "neck": ((177,), ("skin",)),
    "jacket_upper": ((179, 180), ("coat", "tunic")),
    "dress_bodice": ((182,), ("tunic", "skirt")),
    "belt": ((192, 193, 194, 195, 196, 198), ("belt",)),
    "jacket_lower": ((202, 203), ("coat",)),
    "skirt": ((204,), ("skirt", "tunic")),
    "legs": ((212, 213), ("skin",)),
    "boots": ((216, 218), ("boots",)),
}
# Where each region can be, so a colour shared by two regions (skin: neck,
# hands, legs) is only counted in its own band. Head radii, y.
BANDS = {
    "collar": (0.8, 1.6),
    "neck": (0.8, 1.3),
    "jacket_upper": (1.0, 2.6),
    "dress_bodice": (1.2, 2.45),
    "belt": (2.1, 2.8),
    "jacket_lower": (2.3, 3.6),
    "skirt": (2.4, 4.6),
    "legs": (4.0, 5.0),
    "boots": (4.6, 6.1),
}


def grid_coords():
    ys = np.arange(Y0, Y1, 1 / GRID)
    xs = np.arange(X0, X1, 1 / GRID)
    return np.meshgrid(xs, ys)


def sample(mask: np.ndarray, ox: float, oy: float, scale: float) -> np.ndarray:
    gx, gy = grid_coords()
    px = np.round(ox + gx * scale).astype(int)
    py = np.round(oy + gy * scale).astype(int)
    ok = (px >= 0) & (py >= 0) & (px < mask.shape[1]) & (py < mask.shape[0])
    out = np.zeros(gx.shape, bool)
    out[ok] = mask[py[ok], px[ok]]
    return out


def boundary_distance(a: np.ndarray, b: np.ndarray) -> float:
    if not a.any() or not b.any():
        return float("inf")
    edge_a = a & ~ndi.binary_erosion(a)
    edge_b = b & ~ndi.binary_erosion(b)
    da = ndi.distance_transform_edt(~edge_b)[edge_a].mean()
    db = ndi.distance_transform_edt(~edge_a)[edge_b].mean()
    return float((da + db) / 2 / GRID)


def keyed(p: c.CharacterParams) -> c.CharacterParams:
    o = p.outfit
    outfit = dataclasses.replace(
        o,
        hat_color=None,
        hat_band_color=None,
        staff_color=None,
        staff_crystal_color=None,
        collar_color=KEY["collar"] if o.collar_color else None,
        coat_color=KEY["coat"] if o.coat_color else None,
        tunic_color=KEY["tunic"],
        skirt_color=KEY["skirt"] if o.skirt_color else None,
        belt_color=KEY["belt"] if o.belt_color else None,
        boot_color=KEY["boots"],
    )
    return dataclasses.replace(p, outfit=outfit, skin_tone=KEY["skin"], hair_color=KEY["hair"], hair_tip_color=None)


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "katherina"
    wanted = sys.argv[2:] or list(REGIONS)
    OUT.mkdir(parents=True, exist_ok=True)

    p = PRESETS[name]
    sk = c.skeleton_for(p)
    k = 4
    svg = c.render_character(keyed(p), sk)
    ours = np.asarray(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=k))).convert("RGBA")).astype(int)
    ocx, ocy, osc = sk.head_cx * k, sk.head_cy * k, sk.head_r * k

    def ours_mask(key: str) -> np.ndarray:
        col = np.array([int(KEY[key][i : i + 2], 16) for i in (1, 3, 5)])
        m = (np.abs(ours[..., :3] - col).sum(2) <= 30) & (ours[..., 3] > 200)
        return sample(m, ocx, ocy, osc)

    rgb = np.asarray(Image.open(REF).convert("RGB")).astype(int)
    lab, _ = ndi.label(rgb.sum(2) > 60)

    def ref_mask(ids: tuple[int, ...]) -> np.ndarray:
        return sample(np.isin(lab, ids), OX, OY, SC)

    _, gy = grid_coords()
    hidden = sample(lab == 8, OX, OY, SC) | ours_mask("hair")

    print(f"{name}  (commit the numbers with the render they came from)")
    print(f"{'region':14s} {'iou':>6s} {'dist':>7s}")
    for region in wanted:
        ids, keys = REGIONS[region]
        lo, hi = BANDS[region]
        band = (gy >= lo) & (gy <= hi)
        r = ref_mask(ids) & band & ~hidden
        o = np.zeros_like(r)
        for key in keys:
            o |= ours_mask(key)
        o &= band & ~hidden
        union = (r | o).sum()
        iou = (r & o).sum() / union if union else float("nan")
        print(f"{region:14s} {iou:6.3f} {boundary_distance(r, o):7.3f}")
        vis = np.zeros(r.shape + (3,), np.uint8)
        vis[r] = (40, 90, 40)
        vis[o] = (110, 40, 110)
        vis[r & o] = (120, 120, 120)
        vis[r & ~ndi.binary_erosion(r)] = (0, 255, 0)
        vis[o & ~ndi.binary_erosion(o)] = (255, 0, 255)
        Image.fromarray(vis).save(OUT / f"{name}_{region}.png")

    Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), scale=2))).save(OUT / f"{name}_keyed.png")


if __name__ == "__main__":
    main()
