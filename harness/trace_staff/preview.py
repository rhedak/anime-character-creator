"""Render the traced staff alone as flat SVG, next to the reference crop at the same scale."""

import io
import json
import sys

import cairosvg
from PIL import Image

OUT = "out/trace_staff"
REF = "/Users/henrik/git/time_slider_katherina/style-anchors/katherina_grok/katherina_grok.jpg"
OX, OY, SCALE = 650.0, 481.0, 173.7
data = json.load(open(f"{OUT}/staff_trace.json"))
C = data["colors"]
WOOD = sys.argv[1] if len(sys.argv) > 1 else C["wood_upper"]
X0, X1, Y0, Y1 = 140, 480, 290, 1540
SW = 0.041 * SCALE  # this generator's chibi stroke, in reference pixels


def path(c, close=True):
    def p(pt):
        return f"{pt[0] * SCALE + OX - X0:.1f} {pt[1] * SCALE + OY - Y0:.1f}"

    d = ["M " + p(c["start"])] + [f"Q {p(a)} {p(b)}" for a, b in c["segs"]]
    return " ".join(d) + (" Z" if close else "")


parts = [f'<rect width="100%" height="100%" fill="#000"/>']
parts.append(f'<path d="{path(data["wood"])}" fill="{WOOD}" stroke="#111" stroke-width="{SW:.1f}"/>')
for st in data["strands"]:
    parts.append(f'<path d="{path(st)}" fill="{WOOD}" stroke="#111" stroke-width="{SW * 0.6:.1f}" stroke-linejoin="round"/>')
parts.append(f'<path d="{path(data["crystal"])}" fill="{C["crystal_mid"]}" stroke="none"/>')
for f in data["facets_dark"]:
    parts.append(f'<path d="{path(f)}" fill="{C["crystal_dark"]}"/>')
for f in data["facets_light"]:
    parts.append(f'<path d="{path(f)}" fill="{C["crystal_light"]}"/>')
parts.append(f'<path d="{path(data["crystal"])}" fill="none" stroke="#111" stroke-width="{SW:.1f}"/>')
w, h = X1 - X0, Y1 - Y0
svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}">{"".join(parts)}</svg>'
ours = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))).convert("RGB")
ref = Image.open(REF).convert("RGB").crop((X0, Y0, X1, Y1))
c = Image.new("RGB", (w * 2 + 10, h), "white")
c.paste(ref, (0, 0))
c.paste(ours, (w + 10, 0))
c.save(f"{OUT}/preview_full.png")
c.crop((0, 0, w * 2 + 10, 420)).resize(((w * 2 + 10) * 2, 840)).save(f"{OUT}/preview_top.png")
print("ok")
