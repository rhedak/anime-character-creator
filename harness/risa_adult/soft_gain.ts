// Stage 6 of docs/risa-polish-plan.md: Risa in the soft finish at other clump strengths than her cut's `lockGain`, for the owner to judge by eye before it is set. The cut is a module constant,
// so its gain is changed in place for this process only.
//
//   node harness/risa_adult/soft_gain.ts OUT.svg GAIN ['{"outfit":{"coat_color":null}}']     '{"_preset":null}' for the bikini

import { writeFileSync } from "node:fs";
import { adultCutOf } from "../../ts/src/body-adult-cuts.ts";
import { renderCharacter } from "../../ts/src/render.ts";
import { withOverrides } from "./risa.ts";

const [out, gain, json] = process.argv.slice(2);
if (out === undefined || gain === undefined) {
  process.stderr.write("usage: node harness/risa_adult/soft_gain.ts OUT.svg GAIN [OVERRIDES_JSON]\n");
  process.exit(2);
}
// the uniform by default; `"_preset": null` takes the bikini base of risa.ts instead
const { _preset, ...rest } = json === undefined ? { _preset: "risa" } : { _preset: "risa", ...JSON.parse(json) };
const { p, sk } = withOverrides(JSON.stringify({ ...(_preset === null ? {} : { _preset }), finish: "soft", ...rest }));
(adultCutOf(p) as { lockGain: number }).lockGain = Number(gain);
writeFileSync(out, renderCharacter(p, sk, null, false));
