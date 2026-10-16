import sys,json,pickle;sys.path.insert(0,'/workspace/franzi/analysis')
from measure import *
OUT='/workspace/franzi/analysis/'
D=json.load(open(OUT+'measurements.json'))
keys=list(SRC);M={k:measure(k)[1] for k in keys}
# ---- leg widths below crotch
print('LEG WIDTH per leg (px, and /H_head) below crotch')
for k in ['ref1','ref2','ref3','ref4']:
    d=D[k];cr=d['crotch_y'];cx=d['cx'];H=d['H'];res=[]
    for f in [0.1,0.2,0.3,0.4,0.5,0.6,0.7]:
        y=int(cr+f*H)
        if y>=M[k].shape[0]-3: res.append(None);continue
        r=[t for t in runs(M[k][y]) if t[1]-t[0]>25]
        # legs = two runs near centre
        r=sorted(r,key=lambda t:abs((t[0]+t[1])/2-cx))[:2]
        res.append(round(np.mean([b-a+1 for a,b in r])/H,3))
    print(k,res)
# ref4 legs full profile
k='ref4';d=D[k];m=M[k];cx=d['cx'];H=d['H']
prof=[]
for y in range(d['crotch_y']+5,d['fg_bottom']-5,20):
    r=[t for t in runs(m[y]) if t[1]-t[0]>12]
    prof.append((y,[b-a+1 for a,b in r]))
print('ref4 leg widths by y',prof[::3])
fb=d['fg_bottom'];print('ref4 total height',fb-d['head_top'],'heads',(fb-d['head_top'])/H,'crotch from top heads',(d['crotch_y']-d['head_top'])/H,'leg len heads',(fb-d['crotch_y'])/H,'legs/total',(fb-d['crotch_y'])/(fb-d['head_top']))
# knee/ankle width min
ys=range(d['crotch_y']+int(0.8*H),fb-int(0.45*H))
lw=[(np.mean([b-a+1 for a,b in sorted([t for t in runs(m[y]) if t[1]-t[0]>12],key=lambda t:(t[0]+t[1])/2)[:2]]),y) for y in ys]
print('ref4 thigh widest',max(lw[:int(0.5*H)]),'min shank',min(lw[int(H):]))
