import glob,os,json,numpy as np
from PIL import Image
P='/workspace/franzi-refs-pkg/'
names=['00-base-dirndl','01-swimsuit','02-blouse','03-bodice','04-bikini-fullbody']
im={n:np.array(Image.open(P+n+'.png')) for n in names}
def iou(a,b): return (a&b).sum()/max((a|b).sum(),1)
res={'alpha_iou':{},'head_iou(y<445)':{},'segments':{}}
for i,a in enumerate(names):
    for b in names[i+1:]:
        A=im[a][...,3]>127;B=im[b][...,3]>127
        h=np.zeros_like(A);h[:445]=1
        res['alpha_iou'][a+' vs '+b]=round(float(iou(A&(np.arange(A.shape[0])[:,None]<1500),B&(np.arange(A.shape[0])[:,None]<1500))),4)
        res['head_iou(y<445)'][a+' vs '+b]=round(float(iou(A&h,B&h)),4)
bad=[]
for n in names[1:]:
    I=im[n];Ia=I[...,3]>127;U=np.zeros(Ia.shape,bool);comp=np.zeros(I.shape,np.float32)
    rows=[]
    for f in sorted(glob.glob(P+'segments/'+n+'/**/*.png',recursive=True)):
        s=np.array(Image.open(f));assert s.shape==I.shape,f
        rel=os.path.relpath(f,P+'segments/'+n);sa=s[...,3]
        solid=sa>250
        if solid.sum()==0: res['segments'][n+'/'+rel]={'solid_px':0};continue
        d=np.abs(s[solid][:,:3].astype(int)-I[solid][:,:3].astype(int)).mean()
        ia=iou(sa>127,Ia&(sa>0)) if False else None
        res['segments'][n+'/'+rel]={'solid_px':int(solid.sum()),'mean_abs_rgb_diff_vs_image':round(float(d),2),'alpha_outside_image_px':int(((sa>127)&~Ia).sum())}
        if d>3: bad.append((n,rel,d))
        if 'woman' not in rel: U|=sa>127
    # composite: all non-woman segments over transparent, compare to image
    res['segments'][n+'/_union_cover_of_image_alpha']=round(float((U&Ia).sum()/Ia.sum()),4)
print(json.dumps(res,indent=1));print('FAILED layers (rgb diff>3):',bad)
json.dump(res,open(P+'verification.json','w'),indent=1)
