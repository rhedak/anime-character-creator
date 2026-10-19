"""Draw the traced chains over the reference, zoomed (trace-reference step 3 check). ./harness/run.sh harness/franzi_hair/show.py"""

import json

import numpy as np
from PIL import Image, ImageDraw

import sys

sys.path.insert(0, "/Users/henrik/git/anime-character-creator/.claude/skills/trace-reference")
import trace_lib as tl

OX, OY, S = 660.0, 270.5, 175.7
import sys as _s
res = {}
for f in (_s.argv[1:] or ["out/franzi_hair/chains.json"]):
    res.update({f.split("/")[-1][:-5] + ":" + k: v for k, v in json.load(open(f)).items()})
im = Image.open("ref/franzi/04-bikini-fullbody.png").convert("RGBA")
bg = Image.new("RGBA", im.size, (200, 200, 200, 255))
bg.alpha_composite(im)
rgb = np.array(bg.convert("RGB")).astype(float)
rgb = np.clip(rgb * 1.0, 0, 255).astype(np.uint8)
img = Image.fromarray(rgb)
d = ImageDraw.Draw(img)
colors = {"back": (0, 160, 255), "front": (255, 0, 0), "line": (0, 220, 0), "stroke1": (255, 160, 0), "stroke2": (255, 0, 255), "rest": (255, 255, 0)}
for name, (start, segs) in res.items():
    pts = tl.sample_chain(tuple(start), [(tuple(c), tuple(e)) for c, e in segs], 10)
    px = [(OX + x * S, OY + y * S) for x, y in pts]
    d.line(px, fill=colors.get(name.split(":")[-1], (255, 80, 80)), width=2)
# skull circle
d.ellipse((OX - S, OY - S, OX + S, OY + S), outline=(255, 255, 255))
img.crop((440, 60, 900, 560)).resize((920, 1000)).save("out/franzi_hair/trace.png")
