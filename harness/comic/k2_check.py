"""K2 look: a strip of three panels that exercises placement, a crop and a flip.

    ./harness/run.sh harness/comic/k2_check.py

Writes out/comic/k2.svg and .png. Not a test; the thing to do is look at it.
"""

import sys

sys.path.insert(0, "src")

from anime_character_creator import PRESETS
from anime_character_creator.comic import Panel, Placement, Strip, write_strip

W = 752
wall = '<rect width="752" height="100%" fill="#cfc6b4" />'
floor = '<rect y="300" width="752" height="200" fill="#a8946f" />'

# 1. Two figures facing each other, the right one flipped.
talk = Panel(W, 360, backdrop=wall + floor.replace('y="300"', 'y="250"'), placements=(
    Placement(PRESETS["chiyo"], 230, 340, 330),
    Placement(PRESETS["satoshi"], 520, 340, 330, flip=True),
))
# 2. A close-up that crops: the head and shoulders of one figure.
close = Panel(W, 260, backdrop=wall, placements=(Placement(PRESETS["satoshi"], 376, 560, 700),))
# 3. A narrow panel, centred, with a figure at its edge.
edge = Panel(420, 300, backdrop=wall, placements=(
    Placement(PRESETS["chiyo"], 120, 280, 300),
    Placement(PRESETS["satoshi"], 400, 300, 340, flip=True),
))
for path in write_strip(Strip((talk, close, edge)), "out/comic/k2"):
    print(path)
