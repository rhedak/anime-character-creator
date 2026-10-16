import numpy as np,glob,os
from PIL import Image
from scipy import ndimage as ndi
S='/workspace/franzi-pack/';D='/workspace/franzi-pack-alpha/'
def fgmask(a,T=12,P=2,minarea=150):
    m=a.max(2)
    dark=m<=T
    lab,n=ndi.label(dark)
    border=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])))-{0}
    bg=np.isin(lab,list(border))
    # enclosed pure black regions
    pure=m<=P
    lab2,n2=ndi.label(pure)
    sz=ndi.sum(pure,lab2,range(1,n2+1))
    for i,s in enumerate(sz,1):
        if s>=minarea: bg|=(lab2==i)
    fg=~bg
    # drop specks of fg and fill small holes
    lf,nf=ndi.label(fg);s=ndi.sum(fg,lf,range(1,nf+1))
    fg=np.isin(lf,[i+1 for i,v in enumerate(s) if v>=30])
    return fg
def apply(a,fg):
    al=ndi.gaussian_filter(fg.astype(float),0.7)
    al=np.where(ndi.binary_erosion(fg,iterations=2),1,al)
    al=np.where(ndi.binary_dilation(fg,iterations=2),al,0)
    c=a.astype(float)/np.maximum(al,1e-3)[...,None]
    edge=al<1
    c=np.where(edge[...,None],np.clip(c,0,255),a)
    return np.dstack([c,al*255]).round().astype(np.uint8)
names=sorted(os.path.basename(f)[:-5] for f in glob.glob(S+'*.webp'))
base={}
for n in names:
    if '-' in n and n.split('-')[-1] in('blink','talk1','talk2','talk3'): continue
    a=np.array(Image.open(S+n+'.webp').convert('RGB'));base[n]=(a,fgmask(a))
for n in names:
    a=np.array(Image.open(S+n+'.webp').convert('RGB'))
    k=n.rsplit('-',1)[0]
    if n in base: fg=base[n][1];note=''
    else:
        own=fgmask(a);b=base[k][1]
        iou=(own&b).sum()/(own|b).sum()
        # reuse base mask (silhouette identical)
        fg=b if iou>0.99 else own
        note=f'iou={iou:.4f} {"reused" if iou>0.99 else "OWN"}'
    Image.fromarray(apply(a,fg),'RGBA').save(D+n+'.webp',lossless=True,exact=True)
    print(n,note,fg.mean().round(3))
