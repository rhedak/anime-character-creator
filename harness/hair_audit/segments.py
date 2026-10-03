"""Whether a reference's `segments/` are pixel-exact cuts of its composite, the
test `harness/trace_hair/locate.py` ran on `katherina_grok_real` (its hair:
mean colour difference 0.6, no pixel over 20), here for any reference folder.
An exact cut can give coordinates; a regenerated layer cannot (the trace
skill, step 1).

    ./harness/run.sh harness/hair_audit/segments.py ref-local/katherina_grok_nohat [NAME ...]

With no names, every `*.png` under `segments/`. Writes
`out/hair_audit/segments_<folder>.json`.
"""

import json
import pathlib
import sys

sys.path.insert(0, "harness/trace_hair")

import numpy as np
from PIL import Image

from locate import locate


def main() -> None:
    folder = pathlib.Path(sys.argv[1])
    names = sys.argv[2:]
    ref = np.asarray(Image.open(folder / f"{folder.name}.png").convert("RGB")).astype(float)
    paths = [folder / "segments" / f"{n}.png" for n in names] if names else sorted((folder / "segments").rglob("*.png"))
    out = {}
    for path in paths:
        s = np.asarray(Image.open(path).convert("RGBA")).astype(float)
        ox, oy, mean, frac = locate(ref, s)
        key = str(path.relative_to(folder / "segments").with_suffix(""))
        out[key] = {
            "at": [ox, oy],
            "size": [s.shape[1], s.shape[0]],
            "mean_diff": round(mean, 2),
            "frac_over_20": round(frac, 4),
        }
        print(key, out[key], "exact" if mean < 2 and frac < 0.01 else "NOT exact")
    json.dump(out, open(f"out/hair_audit/segments_{folder.name}.json", "w"), indent=1)


if __name__ == "__main__":
    main()
