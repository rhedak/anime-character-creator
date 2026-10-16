"""Black-background removal -> transparent RGBA PNG (unscaled, original pixel grid).
Logic = /workspace/franzi/alpha.py (border-connected near-black flood fill, enclosed pure-black
gaps >=150px, 1px feather, decontaminate) PLUS: for refs 1-4 the foreground mask is unioned with
the Grok segment alphas (hair, clothes, eyes, feet, placed with seg_offsets_full.json) so black hair
edges / enclosed hair-black that the threshold would drop are kept.  Base has no segments, so its
hair is protected by borrowing the ref3 hair+woman mask region where it overlaps dark pixels (see HAIRFIX)."""
import sys,json,numpy as np,os
from PIL import Image
from scipy import ndimage as ndi
src=open(os.path.join(os.path.dirname(__file__),'alpha_original.py')).read()
exec(src.split("names=")[0])   # fgmask(), apply()
S='/workspace/franzi/';O='/workspace/franzi-refs-pkg/work/orig/'
os.makedirs(O,exist_ok=True)
offs=json.load(open(os.path.join(os.path.dirname(__file__),'seg_offsets_full.json')))
R={'ref1':'ref-1-swimsuit','ref2':'ref-2-blouse','ref3':'ref-3-bodice','ref4':'ref-4-bikini'}
def segunion(k,shape,skip=('black-background',)):
    U=np.zeros(shape,bool)
    for key,v in offs.items():
        if key.startswith(k+'/'):
            al=np.array(Image.open(S+R[k]+'-segments/'+key.split('/',1)[1]))[...,3]>10;x,y=v['offset']
            U[y:y+al.shape[0],x:x+al.shape[1]]|=al
    return U
def save(a,fg,name):
    out=apply(a,fg);Image.fromarray(out,'RGBA').save(O+name+'.png');return out
res={}
for k,n in R.items():
    a=np.array(Image.open(S+n+'.jpg').convert('RGB'));fg=fgmask(a)
    U=segunion(k,fg.shape)
    # segments union: only close small holes it creates
    fg2=fg|U
    fg2=ndi.binary_closing(fg2,np.ones((3,3)))|fg2
    res[k]=(a,fg2);print(k,'added px',(fg2&~fg).sum())
    save(a,fg2,n)
a=np.array(Image.open('/workspace/franzi-neutral.jpg').convert('RGB'));fg=fgmask(a)
# HAIRFIX for base: dark pixels (<=12) inside the union of ref hair masks (head is framed identically
# to ref1-3 within ~3px) that are not border-connected background = hair. Pure-black enclosed removal
# is therefore not applied inside the hair silhouette.
H=np.zeros(fg.shape,bool)
for k in('ref1','ref2','ref3'):
    key=k+'/black-hair.png';al=np.array(Image.open(S+R[k]+'-segments/black-hair.png'))[...,3]>10;x,y=offs[key]['offset']
    t=np.zeros(fg.shape,bool);t[y:y+al.shape[0],x:x+al.shape[1]]=al;H|=ndi.binary_erosion(t,iterations=2) if False else t
m=a.max(2);dark=m<=12;lab,_=ndi.label(dark)
bord=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])))-{0}
bgc=np.isin(lab,list(bord))
Hin=ndi.binary_erosion(H,iterations=3)
fgb=fg|(Hin&~bgc)
print('base hairfix added',(fgb&~fg).sum())
save(a,fgb,'franzi-neutral')
