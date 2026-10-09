"""K7 look: the new expressions on three characters, as head crops.

    ./harness/run.sh harness/comic/k7_check.py

Writes out/comic/k7.svg and .png. Satoshi, Chiyo and the cart driver, each shown
neutral, startled, exasperated, alert and smiling.
"""

import sys

sys.path.insert(0, "src")

from anime_character_creator import EXPRESSIONS, PRESETS
from anime_character_creator.comic import Panel, Placement, Strip, write_strip
from anime_character_creator.supporting import SUPPORTING

moods = [None, "startled", "exasperated", "alert", "smile"]
cast = [PRESETS["satoshi"], PRESETS["chiyo"], SUPPORTING["driver"]]
H = 470
panels = []
for ch in cast:
    probe = Placement(ch, 0, 0, H)
    _, hy, _ = probe.head()
    feet = 100 - hy  # puts the head's centre 100 px down the panel
    figs = []
    for i, mood in enumerate(moods):
        c = EXPRESSIONS[mood].applied_to(ch) if mood else ch
        figs.append(Placement(c, 752 / len(moods) * (i + 0.5), feet, H))
    panels.append(Panel(752, 200, backdrop='<rect width="752" height="200" fill="#cfc6b4" />', placements=tuple(figs)))
for path in write_strip(Strip(tuple(panels)), "out/comic/k7"):
    print(path)
