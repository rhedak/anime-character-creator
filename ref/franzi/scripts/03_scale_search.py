"""Pick ref4 scale/offset: compare ipd-derived value with a brute-force fit of the ref4 head silhouette
(hair+face region, y<chin) against the base/ref1-3 head silhouettes on the common canvas."""
import numpy as np,cv2,json
from PIL import Image
W='/workspace/franzi-refs-pkg/work/orig/'  # produced by 02_remove_bg.py (kept outside the package; same pixels as originals/)
def head(name,ymax):
    a=np.array(Image.open(W+name))[...,3]>127;a=a.copy();a[ymax:]=0;return a
ref=[head(n,445) for n in('franzi-neutral.png','ref-1-swimsuit.png','ref-2-blouse.png','ref-3-bodice.png')]
r4=np.array(Image.open(W+'ref-4-bikini.png'))[...,3]
D=json.load(open('/workspace/franzi/analysis/measurements.json'))
def iou(a,b): return (a&b).sum()/(a|b).sum()
s_ipd=np.mean([D[k]['ipd'] for k in('base','ref1','ref2','ref3')])/D['ref4']['ipd']
def place(s,dx,dy):
    A=np.array([[s,0,dx],[0,s,dy]]);return cv2.warpAffine(r4,A,(1312,1504),flags=cv2.INTER_LINEAR)>127
best=[]
for s in np.arange(1.32,1.42,0.005):
    # eye-centre aligned to base
    dx=D['base']['cx']-s*D['ref4']['cx'];dy=D['base']['eyeline']-s*D['ref4']['eyeline']
    m=place(s,dx,dy);m[445:]=0
    best.append((np.mean([iou(m,r) for r in ref]),s,dx,dy))
for b in best: print('eye-aligned s=%.3f  meanIoU head-silhouette=%.4f dx=%.1f dy=%.1f'%(b[1],b[0],b[2],b[3]))
print('ipd scale',s_ipd)
# free fit
bf=(0,)
for s in np.arange(1.32,1.42,0.005):
  for dx in range(-40,0,2):
    for dy in range(-12,13,2):
      m=place(s,dx,dy);m[445:]=0;v=np.mean([iou(m,r) for r in ref])
      if v>bf[0]:bf=(v,s,dx,dy)
print('free fit',bf)
