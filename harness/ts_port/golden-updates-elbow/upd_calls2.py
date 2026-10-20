"""The three recorded functions whose RESULTS carry a character: character_url and encode_params (a link: LINK), and params_to_dict (a dict as recorded pairs, in registry order: the two fields go after
the left_arm_out pair). Text substitution, formatting untouched. Run from ts/ after upd_calls.py."""
import json, re, sys
sys.path.insert(0, "../harness/ts_port/golden-updates-elbow")
import elbowfix as E

D = "../harness/ts_port/fixtures/calls/"

# character_url: every url in the file with a link
f = D + "character_url.json"
raw = open(f).read()
new = E.fix_links(raw)
assert new != raw
json.loads(new); open(f, "w").write(new)
print("character_url.json:", len(re.findall(r"\?c=", raw)), "links")

# encode_params: "result":"s:CODE"
f = D + "encode_params.json"
raw = open(f).read()
RES = re.compile(r'("result":"s:)([A-Za-z0-9_\-]+)(")')
new, n = RES.subn(lambda m: m.group(1) + E.link_code(m.group(2)) + m.group(3), raw)
assert n >= 1
json.loads(new); open(f, "w").write(new)
print("encode_params.json:", n, "results")

# params_to_dict: pairs
f = D + "params_to_dict.json"
raw = open(f).read()
PAIR = re.compile(r'(\["s:left_arm_out",(?:"[fi]:[^"]*")\])(,)')
new, n = PAIR.subn(lambda m: m.group(1) + ',["s:right_elbow","f:0000000000000000"],["s:left_elbow","f:0000000000000000"],', raw)
assert n >= 1 and raw.count('"s:left_arm_out"') == n
json.loads(new); open(f, "w").write(new)
print("params_to_dict.json:", n, "dicts")
