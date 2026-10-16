"""Calibrate Franzi's reference against our own rendered face (trace-reference skill, step 2).

    ./harness/run.sh harness/franzi_hair/calib.py

Measures, on ref 04 and on our render (harness/franzi/franzi.ts, rendered at scale 4), the face skin component: its
lowest row (the chin), the row and span of the eyes' iris-coloured pixels, and the face's width at the eye row. The
scale (px per head radius) is solved twice, from the chin-to-eye run and from the face width at the eyes; they should
agree within a few percent. Writes out/franzi_hair/calib.json: {ref: {cx, cy_head, px_per_r}}.
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

OUT = Path("out/franzi_hair")
OUT.mkdir(parents=True, exist_ok=True)
subprocess.run(["node", "harness/franzi/franzi.ts", str(OUT / "r.svg"), "{}"], check=True)
subprocess.run([sys.executable, "harness/svg2png.py", str(OUT / "r.svg"), str(OUT / "r.png"), "--scale", "4"], check=True)

SKIN = np.array([0xFF, 0xD0, 0xB5])


def skin_face(rgba, cut_y):
    rgb = rgba[..., :3].astype(int)
    a = rgba[..., 3] > 128
    near = (np.abs(rgb - SKIN).sum(2) < 60) & a
    near[cut_y:] = False
    lab, n = ndimage.label(near)
    sizes = ndimage.sum(near, lab, range(1, n + 1))
    return lab == (1 + int(np.argmax(sizes)))


def eyes(rgba, face, y0, y1):
    """Rows of the iris: amber pixels inside the face's bounding box."""
    rgb = rgba[..., :3].astype(int)
    amber = (rgb[..., 0] > 150) & (rgb[..., 1] > 100) & (rgb[..., 1] < 190) & (rgb[..., 2] < 90)
    amber[:y0] = False
    amber[y1:] = False
    ys, xs = np.where(amber)
    return ys, xs


def measure(path, y_lo, y_hi):
    rgba = np.array(Image.open(path).convert("RGBA"))
    face = skin_face(rgba, y_hi)
    ys, xs = np.where(face)
    chin = ys.max()
    iy, ix = eyes(rgba, face, y_lo, chin)
    eye_row = float(np.median(iy))
    row = face[int(eye_row)]
    xs_row = np.where(row)[0]
    return {"chin": int(chin), "eye_row": eye_row, "face_l": int(xs_row.min()), "face_r": int(xs_row.max()), "eye_x": (float(ix.min()), float(ix.max()))}


ref = measure("ref/franzi/04-bikini-fullbody.png", 250, 540)
ren = measure(OUT / "r.png", 120, 420)
print("ref", ref)
print("render", ren)
for k, v in (("ref", ref), ("render", ren)):
    v["chin_to_eye"] = v["chin"] - v["eye_row"]
    v["width_at_eye"] = v["face_r"] - v["face_l"]
    v["cx"] = (v["eye_x"][0] + v["eye_x"][1]) / 2
print("chin-to-eye ratio ref/render", ref["chin_to_eye"] / ren["chin_to_eye"], "width ratio", ref["width_at_eye"] / ren["width_at_eye"])
print("eye span ratio", (ref["eye_x"][1] - ref["eye_x"][0]) / (ren["eye_x"][1] - ren["eye_x"][0]))
json.dump({"ref": ref, "render": ren}, open(OUT / "calib.json", "w"), indent=1)
