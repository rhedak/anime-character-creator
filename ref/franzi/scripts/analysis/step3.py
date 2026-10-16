import sys,json;sys.path.insert(0,'/workspace/franzi/analysis')
from measure import *
from PIL import ImageDraw
OUT='/workspace/franzi/analysis/'
D=json.load(open(OUT+'measurements.json'))
keys=list(SRC);M={k:measure(k)[1] for k in keys}
# canvas: base coords. Align k->target by ipd scale & eye-centre translation
def eyec(d): return np.array([d['cx'],d['eyeline']])
def warp(k,tgt,scale=None,shape=None,anchor='eyes'):
    s=D[tgt]['ipd']/D[k]['ipd'] if scale is None else scale
    A=np.array([[s,0,0],[0,s,0]],float)
    ck=eyec(D[k]);ct=eyec(D[tgt])
    A[:,2]=ct-s*ck
    shp=shape or M[tgt].shape
    w=cv2.warpAffine(M[k].astype(np.uint8),A,(shp[1],shp[0]),flags=cv2.INTER_NEAREST)
    return w>0,s
def iou(a,b): 
    u=(a|b).sum();return (a&b).sum()/u if u else np.nan
def region(tgt,y0,y1):
    r=np.zeros(M[tgt].shape,bool);r[max(0,int(y0)):int(y1)]=True;return r
def col_overlay(a,b,fn,title,lines=()):
    h,w=a.shape;im=np.zeros((h,w,3),np.uint8)
    im[a&~b]=(255,60,60);im[b&~a]=(60,160,255);im[a&b]=(235,235,235)
    I=Image.fromarray(im);dr=ImageDraw.Draw(I)
    for y,c,t in lines: dr.line([(0,y),(w,y)],fill=c,width=1);dr.text((5,y-12),t,fill=c)
    dr.text((10,10),title,fill=(255,255,0))
    I.save(OUT+fn)
pairs=[('base','ref1'),('base','ref2'),('base','ref3'),('ref1','ref2'),('ref1','ref3'),('ref2','ref3'),('ref3','ref4'),('ref1','ref4'),('ref2','ref4'),('base','ref4')]
res={}
rows=[]
for a,b in pairs:
    # target canvas = a's canvas (a is reference, scaled b into it)
    tgt=a
    wb,s=warp(b,tgt)
    ma=M[a]
    Ha=D[a]['H'];top=D[a]['head_top'];ch=D[a]['chin']
    # regions in a's coords
    regs={'head(top..chin)':region(a,top,ch),'head+shoulders+torso(top..chin+2.0H)':region(a,top,ch+2.0*Ha),'shoulders+torso(chin..chin+2.0H)':region(a,ch,ch+2.0*Ha),'bust..waist(chin+0.3H..chin+1.5H)':region(a,ch+0.3*Ha,ch+1.5*Ha)}
    # cap region to rows both visible
    r={n:round(float(iou(ma&rg,wb&rg)),3) for n,rg in regs.items()}
    # edge divergence per band: mean |left edge diff| and right edge diff over rows, in px of a-scale and %H
    bands={'head':(top,ch),'shoulder':(ch,ch+0.6*Ha),'bust':(ch+0.6*Ha,ch+1.2*Ha),'waist':(ch+1.2*Ha,ch+1.8*Ha),'hip/thigh':(ch+1.8*Ha,ch+2.5*Ha)}
    dv={}
    for n,(y0,y1) in bands.items():
        L=[];R=[];W=[]
        for y in range(int(y0),min(int(y1),ma.shape[0]-2)):
            xa=np.nonzero(ma[y])[0];xb=np.nonzero(wb[y])[0]
            if len(xa) and len(xb):
                L.append(xb.min()-xa.min());R.append(xb.max()-xa.max());W.append(len(xb)-len(xa))
        dv[n]=(round(float(np.mean(L)),1),round(float(np.mean(R)),1),round(float(np.mean(W)),1)) if L else None
    res[a+'|'+b]=dict(scale=round(s,4),iou=r,edge_dx=dv)
    print(a,'<-',b,'scale %.4f'%s,r);print('   edge shift (L,R,widthdiff px of '+a+' scale; + = '+b+' more right/wider):',dv)
    col_overlay(ma,wb,'overlay-%s-%s.png'%(a,b),'red=%s  blue=%s (scaled x%.3f, eyes aligned)  white=overlap'%(a,b,s),
        [(top,(255,255,0),'head top'),(D[a]['eyeline'],(0,255,0),'eye line'),(ch,(255,0,255),'chin'),(ch+0.6*Ha,(120,120,120),'+0.6H'),(ch+1.2*Ha,(120,120,120),'+1.2H'),(ch+1.8*Ha,(120,120,120),'+1.8H')])
json.dump(res,open(OUT+'iou_results.json','w'),indent=1)
# ref3 vs ref4: alternate alignment by head height, and optimised search
a,b='ref3','ref4'
for name,s in [('ipd',D[a]['ipd']/D[b]['ipd']),('head-height',D[a]['H']/D[b]['H']),('chin-to-crotch (torso)',(D[a]['crotch_y']-D[a]['chin'])/(D[b]['crotch_y']-D[b]['chin'])),('shoulder-span(bare, ref1)',None)]:
    if s is None: continue
    wb,_=warp(b,a,scale=s);Ha=D[a]['H'];ch=D[a]['chin'];top=D[a]['head_top']
    rg=region(a,top,ch+2.0*Ha)
    print('ref3<-ref4 align',name,'s=%.3f'%s,'IoU head+torso %.3f'%iou(M[a]&rg,wb&rg))
# best scale search for ref3 vs ref4 head+torso, translation by eye centre
best=[]
for s in np.arange(1.2,1.5,0.01):
    wb,_=warp('ref4','ref3',scale=s);rg=region('ref3',D['ref3']['head_top'],D['ref3']['chin']+2*D['ref3']['H'])
    best.append((iou(M['ref3']&rg,wb&rg),s))
print('best scale ref4->ref3',max(best))
# unified contact: all five normalised to base eye-scale side-by-side silhouettes with landmark lines
W=0;ims=[]
for k in keys:
    s=D['base']['ipd']/D[k]['ipd'];wk,_=warp(k,'base',shape=(int(M[k].shape[0]*s*1.0)+400,int(1312)))
    wk=wk[:max(1504,0)] if False else wk
    ims.append(wk)
canvas_h=max(i.shape[0] for i in ims)
sheet=np.zeros((canvas_h,1312*len(ims)//2+0,3),np.uint8)
