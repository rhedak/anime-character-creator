import sys,json,glob,os;sys.path.insert(0,'/workspace/franzi/analysis')
from measure import *
OUT='/workspace/franzi/analysis/'
D=json.load(open(OUT+'measurements.json'));offs=json.load(open(OUT+'seg_offsets.json'))
def iou(a,b): return (a&b).sum()/(a|b).sum()
P={}
for k in SEG:
    m=fgmask(k);shape=m.shape
    print('==',k,'source',shape[::-1])
    for f in sorted(glob.glob(SEG[k]+'*.png')):
        n=os.path.basename(f);a=np.array(Image.open(f))
        key=k+'/'+n
        if key in offs:
            P[(k,n)=='x']=0
            pl=place(k,n,tuple(offs[key][0]),shape)
            print('  %-28s canvas %s  == source canvas? %s  offset %s  rms colour err vs source %.2f'%(n,a.shape[1::-1],a.shape[:2]==shape,tuple(offs[key][0]),offs[key][1]))
        else: print('  %-28s canvas %s (background layer, not placed) == source canvas? %s'%(n,a.shape[1::-1],a.shape[:2]==shape))
    # woman alpha vs fg
    if os.path.exists(SEG[k]+'woman.png'):
        wp=place(k,'woman.png',tuple(offs[k+'/woman.png'][0]),shape)
        print('  woman alpha vs fg(thr14) IoU %.4f ; alpha-only px %d ; fg-only px %d'%(iou(wp,m),(wp&~m).sum(),(m&~wp).sum()))
    # union of clothing+hair+eyes(+feet) vs fg
    u=np.zeros(shape,bool)
    for key,v in offs.items():
        if key.startswith(k+'/') and 'woman' not in key:
            u|=place(k,key.split('/',1)[1],tuple(v[0]),shape)
    print('  union(non-woman parts) covers %.1f%% of fg; (skin has no segment, so shortfall = bare skin)'%(100*(u&m).sum()/m.sum()))
# hair/eyes after scaling to common (ipd) frame relative to eye-centre
print('\nHAIR (alpha placed in source coords) vs eye centre, in ipd units; shapes IoU after ipd-scaling to ref3')
H={}
for k in SEG:
    n='black-hair.png';o=offs[k+'/'+n][0];a=np.array(Image.open(SEG[k]+n))[...,3]>10
    ys,xs=np.nonzero(a);d=D[k];ipd=d['ipd']
    print(k,'hair bbox x',o[0]+xs.min(),o[0]+xs.max(),'y',o[1]+ys.min(),o[1]+ys.max(),'| top above eyeline %.2f ipd, bottom(ponytail) %.2f ipd, left %.2f right %.2f ipd from eye-centre; area/ipd^2 %.2f'%((d['eyeline']-(o[1]+ys.min()))/ipd,((o[1]+ys.max())-d['eyeline'])/ipd,(o[0]+xs.min()-d['cx'])/ipd,(o[0]+xs.max()-d['cx'])/ipd,a.sum()/ipd**2))
    shp=D[k]['size'][::-1];full=np.zeros(shp,bool);full[o[1]:o[1]+a.shape[0],o[0]:o[0]+a.shape[1]]=a;H[k]=full
def al(k,t):
    s=D[t]['ipd']/D[k]['ipd'];A=np.array([[s,0,D[t]['cx']-s*D[k]['cx']],[0,s,D[t]['eyeline']-s*D[k]['eyeline']]])
    return cv2.warpAffine(H[k].astype(np.uint8),A,(D[t]['size'][0],D[t]['size'][1]),flags=cv2.INTER_NEAREST)>0
for a,b in [('ref1','ref2'),('ref1','ref3'),('ref2','ref3'),('ref3','ref4'),('ref1','ref4')]:
    print('hair IoU',a,b,round(float(iou(H[a],al(b,a))),3))
print('\nEYES: centroid of each small eye segment, relative to eye-centre, ipd units + size /ipd')
for k in SEG:
    out=[]
    for key,v in sorted(offs.items()):
        if key.startswith(k+'/') and 'eyes/' in key:
            a=np.array(Image.open(SEG[k]+key.split('/',1)[1]))[...,3]>10
            ys,xs=np.nonzero(a)
            if a.shape[1]>150: continue
            d=D[k];out.append((os.path.basename(key),round((v[0][0]+xs.mean()-d['cx'])/d['ipd'],3),round((v[0][1]+ys.mean()-d['eyeline'])/d['ipd'],3),round(a.shape[1]/d['ipd'],3),round(a.shape[0]/d['ipd'],3)))
    print(k,out)
