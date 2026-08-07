"""How wide is each fringe lock near its tip, against the line that draws it?

The bound used to pick the silhouette's simplification was edge *length*, and
that is the wrong question for a fringe. A lock can have long edges and still be
a needle: what fills with ink is the gap between the two strokes running down
either side of it, and that gap closes as the lock tapers to its point.
"""
import sys
sys.path.insert(0, "out/trace")
sys.path.insert(0, "src")
from fringe import fit, profile, simplify
from anime_character_creator import character as C
from anime_character_creator.skeleton import BUILDS, build_skeleton

pts = [(u, v) for u, v in profile()]
start, segs = fit(pts, simplify(pts, 0.035))
anchors = [start] + [e for _, e in segs]
tips = [i for i in range(1, len(anchors) - 1)
        if anchors[i][1] > anchors[i - 1][1] and anchors[i][1] > anchors[i + 1][1]]
print(f"{len(tips)} lock tips")
for name in ("chibi", "realistic"):
    sk = build_skeleton(heads=BUILDS[name])
    sw = C._stroke_w(sk) / sk.head_r          # stroke in head radii
    solid = []
    for i in tips:
        tx, ty = anchors[i]
        for side in (i - 1, i + 1):
            nx, ny = anchors[side]
            depth = ty - ny                    # how far the lock hangs below the notch
            if depth <= 0:
                continue
            # width of the lock 2 stroke widths above its point, by similar triangles
            run = abs(tx - nx)
            w = 2 * run * min(1.0, 2 * sw / depth)
            solid.append(depth * max(0.0, 1 - w / (2 * sw)) if w < 2 * sw else 0.0)
    ink = [d for d in solid if d > 0]
    print(f"  {name:9s} stroke {sw:.3f} r;  {len(ink)} of {len(solid)} lock sides taper to"
          f" solid ink, worst needle {max(ink) if ink else 0:.3f} head radii long")
