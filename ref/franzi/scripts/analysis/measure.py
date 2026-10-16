import sys,json;sys.path.insert(0,'/workspace/franzi/analysis')
from common import *
from scipy import ndimage as ndi
offs=json.load(open('/workspace/franzi/analysis/seg_offsets.json'))
def fgmask(k):
    im=load(k)
    m=(im.max(2)>14).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    n,l,st,_=cv2.connectedComponentsWithStats(m)
    keep=[i for i in range(1,n) if st[i,4]>0.01*m.size]
    m=np.isin(l,keep)
    m=ndi.binary_closing(m,np.ones((5,5)))
    m=ndi.binary_fill_holes(m)
    return m
def runs(row):
    d=np.diff(np.concatenate([[0],row.astype(np.int8),[0]]))
    s=np.nonzero(d==1)[0];e=np.nonzero(d==-1)[0]
    return [(a,b-1) for a,b in zip(s,e) if b-a>=4]
def iris(k,m):
    im=load(k);hsv=cv2.cvtColor(im,cv2.COLOR_RGB2HSV)
    ys,xs=np.nonzero(m);top=ys.min()
    sel=(hsv[...,0]>=14)&(hsv[...,0]<=32)&(hsv[...,1]>110)&(hsv[...,2]>110)
    sel[:top]=0; sel[top+int(0.6*(1.2*(m.shape[0]<1600)*600+ (m.shape[0]>1600)*450)):]=0
    sel=ndi.binary_opening(sel,np.ones((3,3)))
    l,n=ndi.label(sel)
    if n==0: return None
    sz=ndi.sum(sel,l,range(1,n+1));cm=np.array(ndi.center_of_mass(sel,l,range(1,n+1)))
    idx=np.argsort(sz)[::-1][:2]
    pts=sorted([(cm[i][1],cm[i][0],sz[i]) for i in idx])
    return pts
def measure(k,verbose=False):
    m=fgmask(k);H,W=m.shape
    ys,xs=np.nonzero(m);top=ys.min()
    ir=iris(k,m)
    (lx,ly,_),(rx,ry,_)=ir
    eyeline=(ly+ry)/2;ipd=rx-lx;cx=(lx+rx)/2
    # chin via skin width
    im=load(k);hsv=cv2.cvtColor(im,cv2.COLOR_RGB2HSV)
    sk=((hsv[...,0]<25)|(hsv[...,0]>170))&(hsv[...,1]>25)&(hsv[...,1]<175)&(hsv[...,2]>140)
    sk=ndi.binary_opening(sk,np.ones((3,3)))
    wid=[]
    for y in range(int(eyeline),int(eyeline+ipd*3.2)):
        r=np.nonzero(sk[y,int(cx-ipd*1.6):int(cx+ipd*1.6)])[0]
        wid.append(len(r))
    wid=np.array(wid);wid_s=ndi.uniform_filter1d(wid.astype(float),5)
    y0=int(eyeline)
    # neck plateau: min of smoothed width in window below mouth
    i_min=np.argmin(wid_s[int(ipd*0.8):int(ipd*2.6)])+int(ipd*0.8)
    neck=wid_s[i_min]
    # chin = first row after eye line+0.6ipd where width <= neck*1.12
    cand=[i for i in range(int(ipd*0.6),len(wid_s)) if wid_s[i]<=neck*1.12]
    chin=y0+cand[0]
    Hh=chin-top
    # row widths
    rw=m.sum(1)
    # shoulder: first row after chin where total width > 2.3*neck
    sh=None
    for y in range(chin,H):
        if rw[y]>2.3*neck: sh=y;break
    out=dict(k=k,size=(W,H),head_top=int(top),eyeline=float(eyeline),ipd=float(ipd),chin=int(chin),head_h=int(Hh),neck_w=float(neck),shoulder_y=sh,
             fg_bottom=int(ys.max()),fg_x=(int(xs.min()),int(xs.max())),pupilL=(float(lx),float(ly)),pupilR=(float(rx),float(ry)),cx=float(cx))
    # head width: widest of fg between top and chin excluding ponytail? use skin+hair row width at eye line
    r=runs(m[int(eyeline)]);out['head_w_eyerow']=max(b-a for a,b in r) if r else None
    out['skin_face_w_eyerow']=int(sk[int(eyeline),int(cx-ipd*2):int(cx+ipd*2)].sum())
    # hair width (head only rows top..chin) widest run
    hw=[(m[y]).sum() for y in range(top,chin)]
    out['head_w_max']=int(max(hw))
    # row analysis
    prof={}
    for off in [0.0,0.25,0.5,0.75,1.0,1.5,2.0]:
        y=int(chin+off*Hh)
        if y<H:
            prof[off]=dict(y=y,total=int(rw[y]),runs=[(int(a),int(b)) for a,b in runs(m[y])])
    out['prof']=prof
    return out,m
if __name__=='__main__':
    for k in SRC:
        o,_=measure(k)
        print(k,{a:b for a,b in o.items() if a!='prof'})
        for off,p in o['prof'].items(): print('  +%.2fH'%off,p['y'],p['total'],p['runs'])
