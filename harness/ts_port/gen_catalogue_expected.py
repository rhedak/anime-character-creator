"""Python's own catalogue, as the expected side of `ts/test/catalogue.test.ts`.

    PY harness/ts_port/gen_catalogue_expected.py            writes ts/fixtures/catalogue-expected.json
    PY harness/ts_port/gen_catalogue_expected.py --print    prints the same JSON to stdout (a fresh run, for a live compare)

The file holds the text `to_json()` returns, its sha256 and length, the two starting-point lists the tests name
(`_cast_points`, `_base_points`), and the tuples of `character.py` that the TypeScript modules do not export
(`HAND_STYLES`, `GRIP_STYLES`), so the test can tell a stale copy from a current one.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import _bootstrap  # noqa: F401

import anime_character_creator.catalogue as C  # noqa: E402
import anime_character_creator.character as ch  # noqa: E402

_bootstrap.assert_package_location()

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "ts" / "fixtures" / "catalogue-expected.json"


def expected() -> dict[str, object]:
    text = C.to_json()
    committed = (ROOT / "ref-out" / "catalogue.json").read_text()
    assert text == committed, "ref-out/catalogue.json is stale; run ./refresh-catalogue.sh"
    return {
        "text": text,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "bytes": len(text.encode("utf-8")),
        "cast_points": [[s.id, s.label] for s in C._cast_points()],
        "base_points": [[s.id, s.label] for s in C._base_points()],
        "hand_styles": list(ch.HAND_STYLES),
        "grip_styles": list(ch.GRIP_STYLES),
        "outfit_fields_named": sorted(C._outfit_fields_named()),
    }


def main() -> None:
    out = json.dumps(expected(), indent=1, ensure_ascii=True) + "\n"
    if "--print" in sys.argv:
        sys.stdout.write(out)
    else:
        OUT.write_text(out)
        print(f"wrote {OUT} ({len(out)} bytes)", file=sys.stderr)


if __name__ == "__main__":
    main()
