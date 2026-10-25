"""manifest/full.json: a case's first hash is a prefix of the sha256 of its document. Where the document carries metadata its link is given the field (LINK), so the new prefix is that of the old
document (from the old tree, which stagesold.ts checked against the manifest) with its links fixed. Text substitution of the entry, so the file's formatting is untouched. Run from ts/."""
import hashlib, json, os, sys
sys.path.insert(0, "../harness/ts_port/golden-updates-line-style")
import linefix as E

def utf8(text):
    """What the corpus hashes (test/corpus.ts, surrogatePass): UTF-8 with a lone surrogate encoded as three bytes, as Python's surrogatepass does."""
    return text.encode("utf-8", "surrogatepass")


f = "../harness/ts_port/manifest/full.json"
raw = open(f).read()
old = json.load(open(os.environ["TMPDIR"] + "/stagesold.json"))
n = 0
for id_, o in old.items():
    doc = o["doc"]
    assert hashlib.sha256(utf8(doc)).hexdigest().startswith(o["old"])
    new_doc = E.fix_links(doc)
    if new_doc == doc:  # a document whose metadata carries no character link: unchanged
        continue
    new = hashlib.sha256(utf8(new_doc)).hexdigest()[: len(o["old"])]
    key = f'"{id_}":["{o["old"]}"'
    assert raw.count(key) == 1, id_
    raw = raw.replace(key, f'"{id_}":["{new}"')
    n += 1
json.loads(raw)
open(f, "w").write(raw)
print("manifest/full.json updated:", n, "documents with metadata")
