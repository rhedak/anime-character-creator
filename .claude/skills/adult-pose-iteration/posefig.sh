#!/bin/zsh
# posefig.sh OUT.png 'json' [viewBox]   renders the named poses side by side into one PNG (OUT is relative to $OUT_DIR, default out/posefig under the repo)
# e.g.  DRESS=1 .claude/skills/adult-pose-iteration/posefig.sh arms.png '{"r6":{"right_arm_out":6},"r90":{"right_arm_out":90},"cheer":{"right_arm_out":150,"left_arm_out":150}}'
# Needs `uv sync --project tools` once (cairosvg) and cairo on the library path.
HERE=${0:A:h}
R=${HERE:h:h:h}
OUT_DIR=${OUT_DIR:-$R/out/posefig}
export DYLD_FALLBACK_LIBRARY_PATH=${DYLD_FALLBACK_LIBRARY_PATH:-}:/opt/homebrew/lib:/usr/local/lib
D=$OUT_DIR/parts/$(basename $1 .png)
mkdir -p $D
node $HERE/posefig.ts $D "$2" $3 2>&1 | grep -v -i 'warning\|reparsing\|eliminate\|trace-warnings'
for f in $D/*.svg; do $R/tools/.venv/bin/python $R/harness/svg2png.py $f ${f%.svg}.png 2>&1 | tail -2; done
$R/tools/.venv/bin/python - <<PY
import json
from PIL import Image
names = list(json.loads('''$2''').keys())
ims = [Image.open("$D/" + n + ".png").convert("RGB") for n in names]
h = 900
ims = [i.resize((int(i.width * h / i.height), h)) for i in ims]
sheet = Image.new("RGB", (sum(i.width for i in ims), h))
x = 0
for i in ims:
    sheet.paste(i, (x, 0)); x += i.width
sheet.save("$OUT_DIR/$1")
print("$OUT_DIR/$1", sheet.size)
PY
