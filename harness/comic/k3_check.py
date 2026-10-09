"""K3 look: beat A's real text on two panels, with the figures that speak it.

    ./harness/run.sh harness/comic/k3_check.py

Writes out/comic/k3.svg and .png.
"""

import sys

sys.path.insert(0, "src")

from anime_character_creator import PRESETS
from anime_character_creator.comic import Panel, Placement, Strip, write_strip
from anime_character_creator.comic.bubbles import bubble_svg, caption_svg

W = 752
wall = '<rect width="752" height="100%" fill="#cfc6b4" />'
floor = '<rect y="250" width="752" height="200" fill="#a8946f" />'

# A2: a caption over the morning window.
cap, _ = caption_svg("It had been very close to a year.", 18, 18, 330)
a2 = Panel(W, 200, backdrop='<rect width="752" height="200" fill="#b9c2c4" />', overlay=cap)

# A3: Chiyo speaks, Satoshi at the edge.
chiyo = Placement(PRESETS["chiyo"], 540, 400, 360)
hx, hy, hr = chiyo.head()
b = bubble_svg("There you are, Satoshi. Off wandering again.", 230, 110, 230, tail_to=(hx - hr * 1.5, hy - hr * 0.6))
a3 = Panel(W, 420, backdrop=wall + floor.replace('y="250"', 'y="330"'), placements=(chiyo,), overlay=b)

# A4: two lines, two speakers, facing each other.
sat = Placement(PRESETS["satoshi"], 220, 470, 320)
chi = Placement(PRESETS["chiyo"], 540, 470, 320, flip=True)
sx, sy, sr = sat.head()
cx, cy, cr = chi.head()
b1 = bubble_svg("It's hardly busy this time of day anyway.", 200, 62, 250, tail_to=(sx + sr * 0.2, sy - sr * 1.2))
b2 = bubble_svg("That's not an answer, and you know it isn't one.", 560, 62, 250, tail_to=(cx - sr * 0.1, cy - cr * 1.2))
a4 = Panel(W, 490, backdrop=wall + floor.replace('y="250"', 'y="400"'), placements=(sat, chi), overlay=b1 + b2)

for path in write_strip(Strip((a2, a3, a4)), "out/comic/k3"):
    print(path)
