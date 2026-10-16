import numpy as np, cv2
from PIL import Image
S='/workspace/franzi/'
SRC={'base':'/workspace/franzi-neutral.jpg','ref1':S+'ref-1-swimsuit.jpg','ref2':S+'ref-2-blouse.jpg','ref3':S+'ref-3-bodice.jpg','ref4':S+'ref-4-bikini.jpg'}
SEG={'ref1':S+'ref-1-swimsuit-segments/','ref2':S+'ref-2-blouse-segments/','ref3':S+'ref-3-bodice-segments/','ref4':S+'ref-4-bikini-segments/'}
def load(k): return np.array(Image.open(SRC[k]).convert('RGB'))
def fg(k,thr=28):
    im=load(k).astype(int)
    m=(im.max(2)>thr).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    n,l,st,_=cv2.connectedComponentsWithStats(m)
    if n>1:
        keep=[i for i in range(1,n) if st[i,4]>0.01*m.size]
        m=np.isin(l,keep).astype(np.uint8)
    return m
def seg(k,f): return np.array(Image.open(SEG[k]+f))
def locate(k,f,scales=(1.0,)):
    src=cv2.cvtColor(load(k),cv2.COLOR_RGB2GRAY)
    a=seg(k,f); al=a[...,3:]/255.
    g=cv2.cvtColor((a[...,:3]*al).astype(np.uint8),cv2.COLOR_RGB2GRAY)
    best=None
    for s in scales:
        t=cv2.resize(g,None,fx=s,fy=s,interpolation=cv2.INTER_AREA) if s!=1 else g
        am=cv2.resize((al[...,0]>0.5).astype(np.float32),(t.shape[1],t.shape[0]))
        if t.shape[0]>src.shape[0] or t.shape[1]>src.shape[1]: continue
        r=cv2.matchTemplate(src,t,cv2.TM_CCORR_NORMED if False else cv2.TM_SQDIFF_NORMED,mask=cv2.merge([am]*1) if False else None)
        mn,_,loc,_=cv2.minMaxLoc(r)
        c=cv2.matchTemplate(src,t,cv2.TM_CCOEFF_NORMED);_,mx,_,l2=cv2.minMaxLoc(c)
        if best is None or mx>best[0]: best=(mx,s,l2)
    return best
def place(k,f,off,shape):
    a=seg(k,f)[...,3]>10
    out=np.zeros(shape,bool); x,y=off
    h,w=a.shape; 
    y0,x0=max(y,0),max(x,0); y1,x1=min(y+h,shape[0]),min(x+w,shape[1])
    out[y0:y1,x0:x1]=a[y0-y:y1-y,x0-x:x1-x]
    return out
def locate2(k,f):
    src=load(k).astype(np.float32)
    a=seg(k,f); al=(a[...,3]>200).astype(np.float32)
    t=a[...,:3].astype(np.float32)
    if t.shape[0]>src.shape[0] or t.shape[1]>src.shape[1]: return None
    m=np.dstack([al]*3)
    r=cv2.matchTemplate(src,t,cv2.TM_SQDIFF,mask=m)
    mn,_,loc,_=cv2.minMaxLoc(r)
    return loc, float(np.sqrt(mn/(al.sum()*3+1)))  # rms colour error
