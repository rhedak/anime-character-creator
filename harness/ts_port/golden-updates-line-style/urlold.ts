// Old (HEAD) outputs for the urlstate golden: the texts the hashes in fixtures/urlstate.json are of.
import { readFileSync, writeFileSync } from "node:fs";
const H = process.env.TMPDIR + "/head";
const { encodeParams, characterUrl, decodeParams, paramsJsonText } = await import(`${H}/src/urlstate.ts`);
const { outcomeOf, paramsFromDiff, sha256 } = await import(`${H}/test/phase3.ts`);
const fx = JSON.parse(readFileSync("fixtures/urlstate.json", "utf8"));
const TOOL_URL = "https://rhedak.github.io/anime-character-creator/";
const enc = fx.encode.map((c: any) => {
  const p = paramsFromDiff(c.diff);
  const e = encodeParams(p);
  if (sha256(e) !== c.encoded_sha256) throw new Error(`old TS does not reproduce the golden: ${c.label}`);
  const url = characterUrl(p, TOOL_URL);
  if (sha256(url) !== c.url_sha256) throw new Error(`old url: ${c.label}`);
  return { params: paramsJsonText(p), encoded: e, url };
});
const mal = fx.malformed.map((c: any) => {
  const o = outcomeOf(() => decodeParams(c.input));
  if (o.ok_sha256 === undefined) return null;
  const p = decodeParams(c.input);
  return { text: paramsJsonText(p), sha: o.ok_sha256 };
});
writeFileSync(process.env.TMPDIR + "/urlold.json", JSON.stringify({ enc, mal }));
console.log("old outputs reproduce the golden:", enc.length, "encode entries,", mal.filter(Boolean).length, "malformed ok");
