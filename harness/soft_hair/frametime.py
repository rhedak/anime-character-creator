"""Chrome cost of the soft finish's clumps: the page swaps a character's SVG the way the companion app
swaps frames (an `innerHTML` replace, then a frame), with and without the clumps, and reports the
time per swap. `docs/soft-hair-plan.md` section 7 sets this budget: the clumps must not cost more than
a few milliseconds over the soft finish without them.

    ./harness/run.sh harness/soft_hair/frametime.py risa [satoko ...]

Needs Google Chrome (headless). Writes `out/soft/frametime.html`, runs it and prints the medians.
Two numbers per case: `sync` is parse, style and layout in the swap itself, `frame` is the swap to the
second animation frame after it (a 60 Hz clock, so it moves in steps of about 16.7 ms).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, "src")
from anime_character_creator import HAIRSTYLES, PRESETS, render_character  # noqa: E402

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PAGE = """<!doctype html><meta charset="utf-8"><title>frametime</title>
<style>body{margin:0;background:#2b1a55}#stage{width:400px;height:500px;filter:drop-shadow(0 6px 10px rgba(0,0,0,.5))}
#stage svg{width:400px;height:500px;display:block}</style>
<div id="stage"></div><pre id="out">running</pre>
<script>
const CASES = %s, SWAPS = 120;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const raf2 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
const med = a => { const s = [...a].sort((x, y) => x - y); return s[Math.floor(s.length / 2)]; };
const p95 = a => { const s = [...a].sort((x, y) => x - y); return s[Math.floor(s.length * 0.95)]; };
(async () => {
  const el = document.getElementById('stage'), res = {};
  for (let round = 0; round < 2; round++) {
    for (const [name, svgs] of Object.entries(CASES)) {
      const sync = [], frame = [];
      for (let i = 0; i < SWAPS; i++) {
        const t0 = performance.now();
        el.innerHTML = svgs[i %% svgs.length];
        el.getBoundingClientRect();
        const t1 = performance.now();
        await raf2();
        sync.push(t1 - t0); frame.push(performance.now() - t0);
        await sleep(40);
      }
      if (round === 1) res[name] = {sync_med: +med(sync).toFixed(2), sync_p95: +p95(sync).toFixed(2), frame_med: +med(frame).toFixed(1), frame_p95: +p95(frame).toFixed(1)};
    }
  }
  document.getElementById('out').textContent = 'RESULT ' + JSON.stringify(res);
})();
</script>"""


def svgs(name: str, locks: bool) -> list[str]:
    p = replace(PRESETS[name], finish="soft")
    style = HAIRSTYLES[p.hairstyle]
    if not locks:
        HAIRSTYLES[p.hairstyle] = replace(style, locks=None)
    try:
        # five frames the way an emotion has them: the mouth in four shapes and a blink
        frames = []
        for mouth in (0.0, 0.3, 0.6, 1.0, 0.0):
            face = replace(p.face, mouth_open=mouth) if hasattr(p.face, "mouth_open") else p.face
            frames.append(render_character(replace(p, face=face)))
        return frames
    finally:
        HAIRSTYLES[p.hairstyle] = style


def main() -> None:
    names = sys.argv[1:] or ["risa"]
    cases = {}
    for n in names:
        cases[f"{n} soft"] = svgs(n, False)
        cases[f"{n} soft+clumps"] = svgs(n, True)
    out = Path("out/soft")
    out.mkdir(parents=True, exist_ok=True)
    page = out / "frametime.html"
    page.write_text(PAGE % json.dumps(cases))
    profile = Path(tempfile.mkdtemp(prefix="frametime-"))
    run = subprocess.run(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--no-first-run",
            f"--user-data-dir={profile}",
            "--timeout=45000",
            "--dump-dom",
            page.resolve().as_uri(),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    m = re.search(r"RESULT (\{.*\})", run.stdout)
    if not m:
        print("no result; stdout tail:", run.stdout[-300:], "stderr tail:", run.stderr[-300:])
        return
    for k, v in json.loads(m.group(1)).items():
        print(
            f"{k:22s} sync median {v['sync_med']:6.2f} ms (p95 {v['sync_p95']:6.2f})   frame median {v['frame_med']:5.1f} ms (p95 {v['frame_p95']:5.1f})"
        )


if __name__ == "__main__":
    main()
