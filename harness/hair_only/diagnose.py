"""Which piece draws what (D5 todo step 1): the claw-like tips over the sleeve.

Katherina at 1.3, no hat, the traced hair-only hair with each piece in its own
colour: the mass (behind the body) pale blue, the front piece (over the body)
pale green, the strands flagged front red, the others blue. Prints where the
front piece and the front strands sit against the arm. Writes
`out/hair_only/diagnose.png`.
"""

import sys

sys.argv.append("--hair-only")
sys.path.insert(0, "harness/trace_hair")

import json  # noqa: E402
from dataclasses import replace  # noqa: E402

from PIL import Image  # noqa: E402

import preview as pv  # noqa: E402
from anime_character_creator import character as c  # noqa: E402
from anime_character_creator.presets import PRESETS  # noqa: E402

HAIR = pv.HAIR


def colored():
    def mass(sk, p):
        sw = c._stroke_w(sk)
        d, _ = pv.pieces_d(sk, "mass")
        parts = [f'<path d="{d}" fill="#b8d0f0" fill-rule="evenodd" />']
        for st in HAIR["strands"]:
            if not st["front"]:
                parts.append(pv.stroke(sk, st["chain"], 1.5, None).replace(c.OUTLINE, "#1040c0"))
        parts.append(f'<path d="{d}" fill="none" stroke="{c.OUTLINE}" stroke-width="{c._outline_w(sw):.2f}" />')
        return "".join(parts)

    def front(sk, p):
        sw = c._stroke_w(sk)
        d, extra = pv.pieces_d(sk, "front")
        parts = [f'<path d="{d}" fill="#b8f0c0" fill-rule="evenodd" fill-opacity="0.85" />']
        for st in HAIR["strands"]:
            if st["front"]:
                parts.append(pv.stroke(sk, st["chain"], 2.5, None).replace(c.OUTLINE, "#e02020"))
        for e in [*HAIR["front_edges"], *extra]:
            parts.append(pv.stroke(sk, e, c._outline_w(sw)))
        return "".join(parts)

    return mass, front


def main() -> None:
    k = replace(PRESETS["katherina"], height=1.3)
    k = replace(k, outfit=replace(k.outfit, hat_color=None))
    sk = c.skeleton_for(k)
    orig = (c._hair_mass, c._hair_front)
    try:
        c._hair_mass, c._hair_front = colored()
        im, _ = pv.render(k, 3)
    finally:
        c._hair_mass, c._hair_front = orig
    t = pv.crop(im, sk, 3, (2.4, 1.5, 2.4, 4.8))
    t.save("out/hair_only/diagnose.png")
    print("out/hair_only/diagnose.png", t.size)
    n_front = sum(st["front"] for st in HAIR["strands"])
    print(f"strands: {len(HAIR['strands'])}, front {n_front}")
    print("front pieces:", len(HAIR["front_parts"]), "holes:", sum(len(h) for _, h in HAIR["front_parts"]))
    for i, (outer, holes) in enumerate(HAIR["front_parts"]):
        pts = pv.c_sample(outer)
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        print(f"  piece {i}: x {min(xs):+.2f}..{max(xs):+.2f}, y {min(ys):+.2f}..{max(ys):+.2f}, holes {len(holes)}")
    print(f"our shoulder y {(sk.shoulder_y - sk.head_cy) / sk.head_r:.2f} r, hem {(sk.hem_y - sk.head_cy) / sk.head_r:.2f} r")
    _ = json, Image


if __name__ == "__main__":
    main()
