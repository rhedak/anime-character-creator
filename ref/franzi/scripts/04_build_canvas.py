"""Assemble the common-canvas package.
Canvas 1312x2440. base/ref1-3 (1312x1504) are pasted unscaled at (0,0).
ref4 (1008x1792) is scaled by S4 and pasted at (DX4,DY4) (fit by 03_scale_search.py: head silhouette IoU 0.986).
Segments are placed at their source offset (seg_offsets_full.json) on a source-size canvas, then pushed through the
exact same resize+paste as their image, so each layer registers pixel-exactly."""
import json,os,numpy as np
from PIL import Image
P='/workspace/franzi-refs-pkg/';S='/workspace/franzi/';O=P+'work/orig/'
CW,CH=1312,2440;S4=1.365;DX4,DY4=-34,-6
offs=json.load(open(P+'scripts/seg_offsets_full.json'))
IMG={'00-base-dirndl':('franzi-neutral',None),'01-swimsuit':('ref-1-swimsuit','ref1'),'02-blouse':('ref-2-blouse','ref2'),
     '03-bodice':('ref-3-bodice','ref3'),'04-bikini-fullbody':('ref-4-bikini','ref4')}
SEGDIR={'ref1':'ref-1-swimsuit-segments/','ref2':'ref-2-blouse-segments/','ref3':'ref-3-bodice-segments/','ref4':'ref-4-bikini-segments/'}
def to_canvas(im,scaled):
    """im: RGBA PIL at source size -> canvas RGBA (premultiplied Lanczos if scaled)."""
    if scaled:
        a=np.asarray(im).astype(np.float32);al=a[...,3:]/255.;pm=np.dstack([a[...,:3]*al,a[...,3:]])
        w,h=round(im.width*S4),round(im.height*S4)
        ch=[np.asarray(Image.fromarray(pm[...,i],'F').resize((w,h),Image.LANCZOS)) for i in range(4)]
        pm=np.dstack(ch);al=np.clip(pm[...,3:]/255.,0,1)
        rgb=np.where(al>1e-3,pm[...,:3]/np.maximum(al,1e-3),0)
        im=Image.fromarray(np.dstack([np.clip(rgb,0,255),np.clip(pm[...,3:],0,255)]).round().astype(np.uint8),'RGBA')
    c=Image.new('RGBA',(CW,CH),(0,0,0,0));c.paste(im,(DX4,DY4) if scaled else (0,0));return c
def clean(c):
    a=np.array(c);a[a[...,3]==0]=0;return Image.fromarray(a,'RGBA')
def save(c,path):
    os.makedirs(os.path.dirname(path),exist_ok=True);clean(c).save(path,optimize=True)
for name,(f,k) in IMG.items():
    im=Image.open(O+f+'.png');sc=(k=='ref4')
    save(to_canvas(im,sc),P+name+'.png')
    if k:
        n=0
        for key,v in offs.items():
            if not key.startswith(k+'/'):continue
            rel=key.split('/',1)[1];seg=Image.open(S+SEGDIR[k]+rel).convert('RGBA')
            full=Image.new('RGBA',im.size,(0,0,0,0));full.paste(seg,tuple(v['offset']))
            save(to_canvas(full,sc),P+'segments/'+name+'/'+rel);n+=1
        print(name,n,'segments')
    else: print(name)
os.makedirs(P+'originals',exist_ok=True)
for name,(f,k) in IMG.items():
    Image.open(O+f+'.png').save(P+'originals/'+name+'-unscaled.png',optimize=True)
json.dump({'canvas':[CW,CH],'ref4_scale':S4,'ref4_offset':[DX4,DY4],'others_offset':[0,0]},open(P+'canvas.json','w'),indent=1)
