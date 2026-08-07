"""Head taper candidates for task 62, side by side at the realistic build."""

import math
import sys

import cairosvg

from anime_character_creator import BUILDS, PRESETS, build_skeleton, render_character
from anime_character_creator import character as C

SEG = C._HEAD_SEGMENTS


def shape(jaw_pull_k, chin_drop_k, cheek, power, width=1.0):
    """Variant of _head_shape with the taper knobs exposed.

    cheek: y in head radii where the taper starts (0.0 is the current cheek
    line, negative starts it above centre so the temples are the widest point).
    power: 2 is the current quadratic ease, 1 is a straighter jaw line.
    """

    def fn(build):
        jaw_pull = jaw_pull_k * build
        chin_drop = chin_drop_k * build
        w = 1.0 - (1.0 - width) * build
        k = 1 / math.cos(math.pi / SEG)

        def pt(deg, radius):
            th = math.radians(deg)
            x, y = math.sin(th) * radius * w, -math.cos(th) * radius
            if y > cheek:
                lean = min(1.0, (y - cheek) / (1.0 - cheek))
                x *= 1.0 - jaw_pull * lean**power
                y *= 1.0 + chin_drop * lean
            return (x, y)

        step = 360 / SEG
        anchors = [pt(i * step, 1.0) for i in range(SEG)]
        controls = [pt((i + 0.5) * step, k) for i in range(SEG)]
        return anchors[0], [(controls[i], anchors[(i + 1) % SEG]) for i in range(SEG)]

    return fn


VARIANTS = [
    ("now 0.30", shape(0.30, 0.05, 0.0, 2)),
    ("a 0.42", shape(0.42, 0.05, 0.0, 2)),
    ("b 0.52", shape(0.52, 0.05, 0.0, 2)),
    ("c 0.42 cheek -0.25", shape(0.42, 0.05, -0.25, 2)),
    ("d 0.42 cheek -0.25 p1.4", shape(0.42, 0.05, -0.25, 1.4)),
    ("e 0.52 cheek -0.25 p1.4", shape(0.52, 0.05, -0.25, 1.4)),
    # A second axis: the canon face is narrower than ours everywhere, not only at
    # the jaw, so try losing width off the whole adult skull and tapering less.
    ("f w0.93 jaw0.30", shape(0.30, 0.05, -0.25, 1.4, 0.93)),
    ("g w0.90 jaw0.30", shape(0.30, 0.05, -0.25, 1.4, 0.90)),
    ("h w0.93 jaw0.36", shape(0.36, 0.05, -0.25, 1.4, 0.93)),
    # The canon jaw is not only narrow, it is a straighter side than ours: read at
    # matched depths its jaw-to-cheek ratio is 0.56 where ours was 0.44. So lose
    # the width off the whole skull and taper it less, rather than the reverse.
    ("i w0.90 jaw0.20", shape(0.20, 0.05, -0.25, 1.4, 0.90)),
    ("j w0.92 jaw0.24", shape(0.24, 0.05, -0.25, 1.4, 0.92)),
]

orig = C._head_shape
preset = sys.argv[1] if len(sys.argv) > 1 else "satoko"
sk = build_skeleton(heads=BUILDS["realistic"], frame=PRESETS[preset].frame)
for i, (label, fn) in enumerate(VARIANTS):
    C._head_shape = fn
    svg = render_character(PRESETS[preset], sk)
    cairosvg.svg2png(
        bytestring=svg.encode(), write_to=f"out/head/v{i}_{preset}.png", output_width=800
    )
    print(i, label)
C._head_shape = orig
