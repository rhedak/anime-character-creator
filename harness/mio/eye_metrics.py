"""Our eye in her pixels (`docs/mio-plan.md`, M9 variant): the aperture's width and height, the
iris's diameter and the distance between the two eyes' centres, for a `FaceStyle`, so a
variant can be solved against what `measure_eyes.py` reads off hers.

    ./harness/run.sh harness/mio/eye_metrics.py
"""

from dataclasses import replace

from anime_character_creator import character
from anime_character_creator.presets import MIO

# Hers, in px of her composite (R = 140.25 px a head radius): `measure_eyes.py`, read off
# the two eye layers, which are true crops (offsets (518, 255) and (663, 257)).
HERS = {
    "aperture_w": 63.5,
    "aperture_h": 66.5,
    "iris_d": 48.5,
    "centre_distance": 137.0,
    "white_outer": 15.0,
}
R_PX = 140.25


def metrics(face_fields, params_fields=None):
    p = replace(MIO, face=replace(MIO.face, **face_fields), **(params_fields or {}))
    sk = character.skeleton_for(p)
    dx, ey, er, f = character._eye_placement(sk, p)
    k = R_PX / sk.head_r
    q = character._eye_quads(er, f)
    w = er * f.eye_width * character._EYE_ASPECT
    top, bot = er * f.eye_openness, er * f.eye_lower_lid
    iris_r = f.iris_size * min(er * f.eye_width, er * (f.eye_openness + f.eye_lower_lid) / 2)
    room = w - iris_r
    inset = getattr(f, "iris_inset", 0.0)
    return {
        "aperture_w": 2 * w * k,
        "aperture_h": (top + bot) * k,
        "iris_d": 2 * iris_r * k,
        "centre_distance": 2 * dx * k,
        "white_outer": (2 * w - 2 * iris_r) * k / 2 + inset * room * k * 0 + (room * (1 + inset)) * k - room * k,
        "eye_dx_px": dx * k,
    }


if __name__ == "__main__":
    print("hers   ", {k: round(v, 1) for k, v in HERS.items()})
    print("now    ", {k: round(v, 1) for k, v in metrics({}).items()})
