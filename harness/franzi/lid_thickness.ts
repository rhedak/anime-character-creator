// Harness only: our eyes alone (no hair, no head) on white, as SVG, for lid_thickness.py.
import { writeFileSync } from "node:fs";
import { adultEyes } from "../../ts/src/body-adult-eyes.ts";
import { onHead } from "../../ts/src/body-adult-parts.ts";
import { skeletonFor } from "../../ts/src/body.ts";
import { FRANZI } from "./franzi.ts";

const sk = onHead(skeletonFor(FRANZI));
writeFileSync(process.argv[2] ?? "out/franzi/eyes-only.svg", `<svg xmlns="http://www.w3.org/2000/svg" width="${sk.canvas_w}" height="${sk.canvas_h}" viewBox="0 0 ${sk.canvas_w} ${sk.canvas_h}"><rect width="100%" height="100%" fill="#ffd0b5"/>${adultEyes(sk, FRANZI)}</svg>`);
