// One-off (stage 7a): what the TypeScript says the new golden entries are, for the script that appends them to the fixtures.
import { writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { FRANZI } from "/Users/hanssen.henrik/git/self-study/anime-character-creator-dev/ts/src/presets.ts";
import { paramsJsonText } from "/Users/hanssen.henrik/git/self-study/anime-character-creator-dev/ts/src/urlstate.ts";
import { toJson } from "/Users/hanssen.henrik/git/self-study/anime-character-creator-dev/ts/src/catalogue.ts";
const text = toJson();
writeFileSync(process.argv[2]!, JSON.stringify({
  franzi: { dict: JSON.parse(JSON.stringify(FRANZI)), json: paramsJsonText(FRANZI) },
  catalogue: { text, sha256: createHash("sha256").update(text, "utf8").digest("hex"), bytes: Buffer.byteLength(text, "utf8") },
}));
