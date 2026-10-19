import re, sys
# Raw-text rules that add the new outfit field `bodice_color` (null) to a golden file without reformatting it.
# R1: an Outfit as a dict: the field goes right after strap_color (the registry's order).
R1 = re.compile(r'("strap_color"(\s*):(\s*)(?:null|"(?:[^"\\]|\\.)*"))(,)(\s*)')
def r1(m):
    return f'{m.group(1)},{m.group(5)}"bodice_color"{m.group(2)}:{m.group(3)}null,{m.group(5)}'
# R2: the key-sorted compact JSON text of an outfit (inside a JSON string, so its quotes may be escaped): bodice_color sorts between blindfold_color and boot_color.
R2 = re.compile(r'(\\*)"blindfold_color\1":((?:null|\1"[^"\\]*\1")),(\1)"boot_color\1":')
def r2(m):
    q=m.group(1)
    return f'{q}"blindfold_color{q}":{m.group(2)},{q}"bodice_color{q}":null,{q}"boot_color{q}":'
def fix(raw):
    n1=len(R1.findall(raw)); n2=len(R2.findall(raw))
    raw=R1.sub(r1,raw); raw=R2.sub(r2,raw)
    return raw,n1,n2
if __name__=="__main__":
    for f in sys.argv[1:]:
        raw=open(f).read()
        if '"bodice_color"' in raw or 'bodice_color' in raw:
            print(f,"already has bodice_color, skipped"); continue
        new,n1,n2=fix(raw); open(f,"w").write(new); print(f,"dict form:",n1,"sorted text form:",n2)
