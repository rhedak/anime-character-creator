"""Find the (x,y) offset of every Grok segment PNG inside its source JPG by
masked template matching (SQDIFF on opaque pixels). Writes seg_offsets_full.json.
Starts from analysis/seg_offsets.json (missing entries e.g. gold buttons are searched)."""
import sys,json,glob,os,numpy as np,cv2
from PIL import Image
S='/workspace/franzi/'
SRC={'ref1':S+'ref-1-swimsuit.jpg','ref2':S+'ref-2-blouse.jpg','ref3':S+'ref-3-bodice.jpg','ref4':S+'ref-4-bikini.jpg'}
SEG={'ref1':S+'ref-1-swimsuit-segments/','ref2':S+'ref-2-blouse-segments/','ref3':S+'ref-3-bodice-segments/','ref4':S+'ref-4-bikini-segments/'}
old=json.load(open(S+'analysis/seg_offsets.json'))
out={}
for k in SRC:
    src=np.array(Image.open(SRC[k]).convert('RGB')).astype(np.float32)
    for f in sorted(glob.glob(SEG[k]+'**/*.png',recursive=True)):
        rel=os.path.relpath(f,SEG[k])
        if rel=='black-background.png': continue
        a=np.array(Image.open(f)); al=(a[...,3]>200).astype(np.float32)
        if al.sum()==0: al=(a[...,3]>0).astype(np.float32)
        r=cv2.matchTemplate(src,a[...,:3].astype(np.float32),cv2.TM_SQDIFF,mask=np.dstack([al]*3))
        mn,_,loc,_=cv2.minMaxLoc(r)
        rms=float(np.sqrt(mn/(al.sum()*3+1)))
        o=old.get(k+'/'+rel)
        out[k+'/'+rel]={'offset':list(loc),'rms':round(rms,2),'prev':o[0] if o else None,'agrees_with_prev':(o is None) or list(loc)==o[0]}
        print(k,rel,loc,round(rms,2),out[k+'/'+rel]['agrees_with_prev'])
json.dump(out,open('/workspace/franzi-refs-pkg/scripts/seg_offsets_full.json','w'),indent=1)
