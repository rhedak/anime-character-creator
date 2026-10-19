// Harness only: our eyes' aperture and lid outlines as JSON in canvas units, for harness/franzi/eye_outline.py.
//   node harness/franzi/eye_outline.ts OUT.json
import { writeFileSync } from "node:fs";
import { adultEyeOutlines } from "../../ts/src/body-adult-eyes.ts";
import { onHead } from "../../ts/src/body-adult-parts.ts";
import { skeletonFor } from "../../ts/src/body.ts";
import { FRANZI } from "./franzi.ts";

const sk = onHead(skeletonFor(FRANZI));
writeFileSync(process.argv[2] ?? "out/franzi/eye-outline.json", JSON.stringify({ head_cx: sk.head_cx, head_cy: sk.head_cy, head_r: sk.head_r, eyes: adultEyeOutlines(sk) }));
