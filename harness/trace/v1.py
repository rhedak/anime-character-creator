"""Trace 1: the silhouette only, as tips and notches with curved edges.

Marks are (bearing, radius) in head-radius units, read off the profile in
contour.py. Bearing 0 is straight up, positive clockwise, which is the
convention `_arc` and the tousle crown already use.
"""
import math, sys
sys.path.insert(0, "out/trace")
from trace import on_ref, strip

def polar(deg, r):
    a = math.radians(deg)
    return (math.sin(a) * r, -math.cos(a) * r)

def chain(marks, bow=1.0):
    segs = []
    for (d0, r0), (d1, r1) in zip(marks, marks[1:]):
        segs.append((polar((d0 + d1) / 2, (r0 + r1) / 2 * bow), polar(d1, r1)))
    return polar(*marks[0]), segs

def mirror(start, segs):
    f = lambda q: (-q[0], q[1])
    return f(start), [(f(c), f(e)) for c, e in segs]

# Tips and notches, crown first then down the character's left side.
MARKS = [
    (0, 1.30),    # crown spike, dead centre in the canon
    (18, 1.17),
    (33, 1.30),
    (52, 1.17),
    (68, 1.26),
    (74, 1.07),
    (90, 1.15),
    (98, 0.99),
    (114, 1.17),
    (120, 0.96),
    (132, 1.18),
    (138, 1.02),
    (146, 1.12),
]

right = chain(MARKS)
strip([on_ref([(right, (255, 0, 255)), (mirror(*right), (255, 0, 255))], dash=0)],
      "out/trace/v1.png")
