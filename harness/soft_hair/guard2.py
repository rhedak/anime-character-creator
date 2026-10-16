"""Round 2 guard (`docs/soft-hair-plan.md`, section 11), on composited rendered pixels.

    ./harness/run.sh harness/soft_hair/guard2.py

Where a variant lightens r3, the lightened pixel should keep its saturation (ratio to the r3 pixel
under it), and its hue should stay close to the one under it (wraparound handled, skipped for
near-grey hair). It exists to stop the "wishy" failure coming back, not as a target to tune to: no
threshold here is fitted to make Risa look good.
"""

from __future__ import annotations

import colorsys
import sys

import numpy as np

sys.path.insert(0, "harness/soft_hair")
sys.path.insert(0, "src")
import mockup2 as K  # noqa: E402
import mockup3 as K3  # noqa: E402


def hsv_arr(im: np.ndarray) -> np.ndarray:
    return np.array([colorsys.rgb_to_hsv(*px) for px in im.reshape(-1, 3)])


def main() -> None:
    for tag, hair in K.PALETTE.items():
        base = np.asarray(K3.draw("r3", "face", hair)).astype(float) / 255
        bh = hsv_arr(base)
        for v in ["SH", "SSh", "S2h", "LS2h"]:
            im = np.asarray(K3.draw(v, "face", hair)).astype(float) / 255
            h = hsv_arr(im)
            lit = h[:, 2] > bh[:, 2] + 0.03
            n = int(lit.sum())
            if n < 200:
                print(f"{tag:7s}{v:6s} lit px {n}")
                continue
            grey = np.median(bh[lit, 1]) < 0.15
            ratio = np.median(h[lit, 1]) / max(np.median(bh[lit, 1]), 1e-6)
            dh = np.minimum(abs(h[lit, 0] - bh[lit, 0]), 1 - abs(h[lit, 0] - bh[lit, 0])) * 360
            print(
                f"{tag:7s}{v:6s} lit px {n:6d}  S ratio {ratio:5.2f}  median S {np.median(h[lit, 1]):.2f}"
                f"  hue drift p90 {np.percentile(dh, 90):4.1f}" + ("  (near grey: hue skipped)" if grey else "")
            )


if __name__ == "__main__":
    main()
