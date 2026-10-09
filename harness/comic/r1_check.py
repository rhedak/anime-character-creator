"""R1 and R3 look: one scene shot at every size, and the eyes looking sideways.

    ./harness/run.sh harness/comic/r1_check.py

Writes out/comic/r1.svg and .png.
"""

import sys
from dataclasses import replace

sys.path.insert(0, "src")

from anime_character_creator import PRESETS
from anime_character_creator.comic import Panel, Placement, Strip, frame, frame_point, write_strip

W = 752
wall = '<rect x="-2000" y="-2000" width="5000" height="2400" fill="#cfc6b4" />'
floor = '<rect x="-2000" y="400" width="5000" height="2000" fill="#a8946f" />'
chiyo = Placement(PRESETS["chiyo"], 0, 400, 340)
back = wall + floor

panels = []
for shot in ("full", "medium", "close", "choker"):
    h = 200 if shot != "full" else 300
    panels.append(Panel(W, h, backdrop=back, placements=(chiyo,), view=frame(chiyo, shot, h), gap_before="beat"))
hx, hy = chiyo.hand("left")
panels.append(Panel(W, 200, backdrop=back, placements=(chiyo,), view=frame_point(hx, hy, 90, 200), gap_before="pause"))

# Gaze: the same close-up looking left, ahead, right.
for g in (-1.0, 0.0, 1.0):
    c = replace(PRESETS["satoshi"], face=replace(PRESETS["satoshi"].face, gaze=g))
    pl = Placement(c, 0, 400, 340)
    panels.append(Panel(W, 190, backdrop=back, placements=(pl,), view=frame(pl, "close", 190), gap_before="beat"))
for path in write_strip(Strip(tuple(panels)), "out/comic/r1"):
    print(path)
