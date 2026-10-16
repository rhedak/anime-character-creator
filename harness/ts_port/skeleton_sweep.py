"""Skeleton fixtures over a parameter sweep: every body, several heights, frames, busts, belt shifts, face ages, with and
without a hat. Writes `ts/fixtures/skeleton-sweep.json`: a list of [body, height, frame, bust, waist_shift, face_age, hat_color, sha256[:20]] where the
hash is over compact, key-sorted `json.dumps(asdict(skeleton_for(p)))`, as in the stage manifest.

    PY harness/ts_port/skeleton_sweep.py
"""

from __future__ import annotations

import dataclasses
import hashlib
import itertools
import json
from pathlib import Path

import _bootstrap  # noqa: F401

from anime_character_creator import PRESETS  # noqa: E402
from anime_character_creator.character import BODY_TYPES, skeleton_for  # noqa: E402

_bootstrap.assert_package_location()
OUT = Path(__file__).resolve().parents[2] / "ts" / "fixtures" / "skeleton-sweep.json"


def main() -> None:
    base = PRESETS["satoko"]
    rows = []
    for body, height, frame, bust, shift, age, hat in itertools.product(
        sorted(BODY_TYPES), (0.7, 0.8, 0.95, 1.0, 1.15, 1.3, 1.6), (-1.5, -1.0, 0.0, 0.5, 1.0), (0.0, 0.3, 1.0), (-0.5, 0.0, 0.4), (0.0, 0.5, 1.0, 2.0), (None, "#112233")
    ):
        p = dataclasses.replace(
            base, body=body, height=height, frame=frame, bust=bust, waist_shift=shift, face_age=age, outfit=dataclasses.replace(base.outfit, hat_color=hat)
        )
        sk = dataclasses.asdict(skeleton_for(p))
        h = hashlib.sha256(json.dumps(sk, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        # [body, height, frame, bust, waist_shift, face_age, hat_color, first 20 hex digits of the sha256]
        rows.append([body, height, frame, bust, shift, age, hat, h[:20]])
    OUT.write_text(json.dumps(rows, separators=(",", ":")))
    print(OUT, OUT.stat().st_size, len(rows))


if __name__ == "__main__":
    main()
