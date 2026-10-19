"""Franzi's head beside the reference's, at one scale: ./harness/run.sh harness/franzi/head_compare.py [OVERRIDES_JSON] [NAME].

Renders harness/franzi/franzi.ts with the overrides, crops the head and shoulders of the render and of ref 04 to the
same head height, and writes out/franzi/head-NAME.png. By eye only: there is no number for a face.
"""

import subprocess
import sys

from PIL import Image

over = sys.argv[1] if len(sys.argv) > 1 else "{}"
name = sys.argv[2] if len(sys.argv) > 2 else "compare"
subprocess.run(["node", "harness/franzi/franzi.ts", "out/franzi/franzi.svg", over], check=True)
subprocess.run([sys.executable, "harness/svg2png.py", "out/franzi/franzi.svg", "out/franzi/franzi.png", "--scale", "4.894"], check=True)


def flat(p):
    im = Image.open(p).convert("RGBA")
    bg = Image.new("RGBA", im.size, "white")
    bg.alpha_composite(im)
    return bg.convert("RGB")


ref = flat("ref/franzi/04-bikini-fullbody.png").crop((360, 60, 960, 760))
# 4.894 = 175.7 reference px per head radius / 35.9 canvas px per radius: the same size as the reference; origin (979, 301)
ren = flat("out/franzi/franzi.png").crop((679, 90, 1279, 790))
W = 600
im = Image.new("RGB", (2 * W + 10, 700), "white")
im.paste(ref, (0, 0))
im.paste(ren, (W + 10, 0))
im.save(f"out/franzi/head-{name}.png")
