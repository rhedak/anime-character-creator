"""K6 look: the supporting cast beside Satoshi and Chiyo, so scale and register can be judged.

    ./harness/run.sh harness/comic/k6_check.py
"""

import sys

sys.path.insert(0, "src")

from anime_character_creator import PRESETS
from anime_character_creator.comic import Panel, Placement, Strip, write_strip
from anime_character_creator.supporting import SUPPORTING

names = [("satoshi", PRESETS["satoshi"]), ("chiyo", PRESETS["chiyo"])] + list(SUPPORTING.items())
step = 752 / len(names)
bg = '<rect width="752" height="100%" fill="#cfc6b4" /><rect y="400" width="752" height="100" fill="#a8946f" />'
panel = Panel(752, 470, backdrop=bg, placements=tuple(
    Placement(p, step * (i + 0.5), 450, 400) for i, (_, p) in enumerate(names)))
for path in write_strip(Strip((panel,)), "out/comic/k6"):
    print(path)
