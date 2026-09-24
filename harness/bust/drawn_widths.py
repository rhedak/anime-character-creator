"""Where the torso and the arm actually are, measured off their ink.

`bare.py` printed skeleton anchors (`arm_x - arm_half_w`, `bust_half_w`) and
the plan read them as the drawn figure. They are not: the arm is not drawn at
`arm_x`, and the tunic's torso is far narrower than the anchor that runs from
`shoulder_half_w`. This rasterizes `_tunic` and `_arms` on their own and reads
their outermost and innermost ink at the bust and waist rows, in head radii
from the centre line, so the numbers are what is on the page.

It is the retraction's evidence (`docs/bust-plan.md`, "What the first draft got
wrong"): at `bust = 0.01` the chibi torso jumps 0.37 head radii, and at the
chibi the torso's side meets the arm's inner edge rather than hiding behind it.

Prints a table; writes nothing.
"""

import io
from dataclasses import replace

import cairosvg
import numpy as np
from PIL import Image

from anime_character_creator import character as c
from anime_character_creator.presets import PRESETS

SCALE = 4
CASES = (("satoko", None), ("keiko", None), ("satoko", "realistic"))
VALUES = (0.0, 0.01, 0.5, 1.0)


def ink(inner: str, sk) -> np.ndarray:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{sk.canvas_w:.0f}" '
        f'height="{sk.canvas_h:.0f}" viewBox="0 0 {sk.canvas_w:.0f} {sk.canvas_h:.0f}">'
        f"{inner}</svg>"
    )
    png = cairosvg.svg2png(bytestring=svg.encode(), scale=SCALE)
    return np.array(Image.open(io.BytesIO(png)).convert("RGBA"))[..., 3] > 128


def right_of_centre(mask: np.ndarray, y: float, cx: float) -> np.ndarray:
    xs = np.nonzero(mask[int(round(y * SCALE))])[0]
    return xs[xs >= cx * SCALE]


def main() -> None:
    print("half-widths in head radii, right of the centre line, from the drawn ink")
    for preset, build in CASES:
        for bust in VALUES:
            p = replace(PRESETS[preset], bust=bust)
            if build == "realistic":
                p = replace(p, body=None, heads=c.BUILDS["realistic"])
            sk = c.skeleton_for(p)
            r, cx = sk.head_r, sk.head_cx
            torso, arm = ink(c._tunic(sk, p), sk), ink(c._arms(sk, p), sk)
            cells = []
            for label, y in (("bust row", sk.bust_y), ("waist", sk.waist_y)):
                t, a = right_of_centre(torso, y, cx), right_of_centre(arm, y, cx)
                cells.append(
                    f"{label}: torso {(t.max() / SCALE - cx) / r:.3f}"
                    f"  arm {(a.min() / SCALE - cx) / r:.3f}-{(a.max() / SCALE - cx) / r:.3f}"
                )
            print(
                f"  {preset:7s} {build or 'chibi':9s} bust {bust:4.2f}"
                f"  anchor {sk.bust_half_w / r:.3f} | " + " | ".join(cells)
            )


main()
