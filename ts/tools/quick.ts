// A fast detector for the mutation gate: renders every K-th case of the full corpus and compares each whole document with
// Python's (sha256 prefix in the committed compact manifest). Exit 1 on the first difference or the first exception.
//   node tools/quick.ts K [offset]
import { renderStages } from "../src/render.ts";
import { loadFullCorpus, loadFullManifest, sha256 } from "../test/corpus.ts";

const k = Number(process.argv[2] ?? 7);
const offset = Number(process.argv[3] ?? 0);
const manifest = loadFullManifest();
const corpus = loadFullCorpus();
let checked = 0;
for (let i = offset; i < corpus.length; i += k) {
  const c = corpus[i]!;
  let doc: string | null | undefined;
  try {
    doc = renderStages(c.params, { id_prefix: c.kw.id_prefix ?? "", background: c.kw.background ?? null, metadata: c.kw.metadata ?? false }).stages.get("doc");
  } catch (e) {
    console.log(`DETECTED ${c.id}: threw ${String(e).slice(0, 80)}`);
    process.exit(1);
  }
  checked++;
  if (typeof doc !== "string" || !sha256(doc).startsWith(manifest.cases[c.id]![0])) {
    console.log(`DETECTED ${c.id}: document differs`);
    process.exit(1);
  }
}
console.log(`SURVIVED (${checked} cases)`);
