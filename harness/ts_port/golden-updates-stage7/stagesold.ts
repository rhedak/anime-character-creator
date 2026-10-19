import { writeFileSync } from "node:fs";
const H = process.env.TMPDIR + "/head";
const { renderStages } = await import(`${H}/src/render.ts`);
const corp = await import(`${H}/test/corpus.ts`);
const manifest = corp.loadFullManifest();
const corpus = corp.loadFullCorpus();
const out: Record<string, { old: string; doc: string }> = {};
for (const c of corpus) {
  const kw = c.kw ?? {};
  if (!kw.metadata) continue;
  const { stages } = renderStages(c.params, { id_prefix: kw.id_prefix ?? "", background: kw.background ?? null, metadata: kw.metadata ?? false });
  const doc = stages.get("doc");
  if (typeof doc !== "string") continue;
  const want = manifest.cases[c.id]![0];
  if (!corp.sha256(doc).startsWith(want)) throw new Error("old TS does not reproduce the manifest: " + c.id);
  out[c.id] = { old: want, doc };
}
writeFileSync(process.env.TMPDIR + "/stagesold.json", JSON.stringify(out));
console.log("old documents with metadata reproduce the manifest:", Object.keys(out).length);
