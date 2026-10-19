import { readFileSync, writeFileSync } from "node:fs";
const H = process.env.TMPDIR + "/head";
const { paramsJsonText } = await import(`${H}/src/urlstate.ts`);
const { PRESETS, EXPRESSIONS } = await import(`${H}/src/presets.ts`);
const { expressionAppliedTo } = await import(`${H}/src/model.ts`);
const { sha256 } = await import(`${H}/test/phase3.ts`);
const model = JSON.parse(readFileSync("fixtures/model.json", "utf8"));
const texts = model.expressions.map((c: any) => {
  const t = paramsJsonText(expressionAppliedTo(EXPRESSIONS[c.expression], PRESETS[c.preset]));
  if (sha256(t) !== c.params_sha256) throw new Error("old TS does not reproduce the golden");
  return t;
});
writeFileSync(process.env.TMPDIR + "/modelold.json", JSON.stringify(texts));
console.log("old expression texts reproduce the golden:", texts.length);
