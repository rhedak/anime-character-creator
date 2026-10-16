import sys,json,os,glob;sys.path.insert(0,'/workspace/franzi/analysis')
from measure import *
from PIL import ImageDraw,ImageFont
OUT='/workspace/franzi/analysis/'
keys=list(SRC)
offs=json.load(open(OUT+'seg_offsets.json'))
def central_run(m,y,cx):
    r=runs(m[y]); 
    for a,b in r:
        if a<=cx<=b: return (a,b),r
    if not r: return None,r
    return min(r,key=lambda t:abs((t[0]+t[1])/2-cx)),r
M={};D={}
for k in keys:
    o,m=measure(k)
    # refine chin: first row with skin width <= 1.05*neck  (recompute)
    im=load(k);hsv=cv2.cvtColor(im,cv2.COLOR_RGB2HSV)
    sk=((hsv[...,0]<25)|(hsv[...,0]>170))&(hsv[...,1]>25)&(hsv[...,1]<175)&(hsv[...,2]>140)
    sk=ndi.binary_opening(sk,np.ones((3,3)))
    cx=o['cx'];ipd=o['ipd'];ey=int(o['eyeline']);top=o['head_top']
    wid=np.array([sk[y,int(cx-ipd*1.6):int(cx+ipd*1.6)].sum() for y in range(ey,int(ey+ipd*3.2))],float)
    ws=ndi.uniform_filter1d(wid,5)
    i0=int(ipd*0.8);i1=int(ipd*2.6);neck=ws[i0:i1].min()
    cand=[i for i in range(int(ipd*0.6),len(ws)) if ws[i]<=neck*1.05]
    chin=ey+cand[0];Hh=chin-top
    # neck base: first row after chin where skin width >1.5*neck
    nb=next((y for y in range(chin+5,chin+int(2.5*ipd)) if sk[y,int(cx-ipd*1.6):int(cx+ipd*1.6)].sum()>1.6*neck),None)
    rw=m.sum(1);H_=m.shape[0]
    bandmax=rw[chin:chin+int(1.5*Hh)].max()
    shy=next(y for y in range(chin,H_) if rw[y]>=0.9*bandmax)
    shw=int(rw[shy:shy+int(0.15*Hh)].max())
    # per-row central runs
    waist=None;hip=None;crotch=None;arm_bot=None
    rows=[]
    for y in range(chin+int(0.9*Hh),min(H_-2,chin+int(3.6*Hh))):
        c,r=central_run(m,y,cx)
        rows.append((y,len(r),(c[1]-c[0]+1) if c else 0,c,r))
    # waist: min central width among rows with >=3 runs, between +1.0H and crotch
    cr=next((y for y,n,w,c,r in rows if n>=2 and c and not (c[0]<=cx<=c[1])),None)  # centre not fg => legs split
    crotch=cr
    cand=[(w,y) for y,n,w,c,r in rows if n>=3 and (cr is None or y<cr-5) and y<chin+2.6*Hh]
    if k=='base': cand=[(w,y) for y,n,w,c,r in rows if n>=1 and y<chin+1.5*Hh]  # arms merged with dirndl
    if cand: waist=min(cand)
    if waist and cr:
        hc=[(w,y) for y,n,w,c,r in rows if waist[1]<y<cr-3 and n>=3]
        if hc: hip=max(hc)
    # arm bottom: last row where an arm-sized run is separate left of the torso run
    for y,n,w,c,r in rows[::-1]:
        if n>=3 and r[0][1]<c[0]-5 and (r[0][1]-r[0][0])<110: arm_bot=y;break
    ex=lambda v:None if v is None else (int(v[0]),int(v[1]))
    d=dict(size=o['size'],head_top=top,eyeline=round(o['eyeline'],1),chin=int(chin),H=int(Hh),ipd=round(ipd,1),cx=round(cx,1),
           head_w=int(o['head_w_max']),neck_w=round(float(neck),1),neck_base_y=nb,shoulder_y=int(shy),shoulder_span=shw,
           bust_total_w=int(rw[int(chin+0.8*Hh)]),waist_w_y=ex(waist),hip_w_y=ex(hip),crotch_y=crotch,arm_bottom_y=arm_bot,
           fg_bottom=o['fg_bottom'],fg_w=int(M and 0 or o['fg_x'][1]-o['fg_x'][0]+1))
    D[k]=d;M[k]=m
    print(k,d)
json.dump(D,open(OUT+'measurements.json','w'),indent=1,default=str)
np.save(OUT+'_dummy.npy',np.zeros(1))
import pickle;pickle.dump((D,),open(OUT+'_D.pkl','wb'))
# normalised table
rows=[]
for k in keys:
    d=D[k];H=d['H'];ipd=d['ipd']
    n=lambda v:None if v is None else round(v/H,3)
    rows.append(dict(img=k,size='%dx%d'%d['size'],head_top=d['head_top'],eye_y=d['eyeline'],chin_y=d['chin'],H_px=H,ipd_px=ipd,
      ipd_over_H=round(ipd/H,3),eye_to_chin_over_H=n(d['chin']-d['eyeline']),top_to_eye_over_H=n(d['eyeline']-d['head_top']),
      head_w_over_H=n(d['head_w']),neck_w_over_H=n(d['neck_w']),neckbase_below_chin_H=n(d['neck_base_y']-d['chin']) if d['neck_base_y'] else None,
      shoulder_y_below_chin_H=n(d['shoulder_y']-d['chin']),shoulder_span_over_H=n(d['shoulder_span']),bust_total_w_over_H=n(d['bust_total_w']),
      waist_w_over_H=n(d['waist_w_y'][0]) if d['waist_w_y'] else None,waist_y_below_chin_H=n(d['waist_w_y'][1]-d['chin']) if d['waist_w_y'] else None,
      hip_w_over_H=n(d['hip_w_y'][0]) if d['hip_w_y'] else None,hip_y_below_chin_H=n(d['hip_w_y'][1]-d['chin']) if d['hip_w_y'] else None,
      crotch_y_below_chin_H=n(d['crotch_y']-d['chin']) if d['crotch_y'] else None,
      arm_len_shoulder_to_hand_H=n(d['arm_bottom_y']-d['shoulder_y']) if d['arm_bottom_y'] else None))
import csv
with open(OUT+'measurements_normalised.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
for r in rows: print(r)
