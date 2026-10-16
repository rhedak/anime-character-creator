import glob,numpy as np
from PIL import Image,ImageDraw
P='/workspace/franzi-refs-pkg/'
names=['00-base-dirndl','01-swimsuit','02-blouse','03-bodice','04-bikini-fullbody']
cols=[(220,30,30),(30,90,230),(20,170,60),(240,150,0),(150,30,200)]
def overlay(box):
    bg=np.ones((box[3]-box[1],box[2]-box[0],3),np.float32)*255
    for n,c in zip(names,cols):
        a=np.array(Image.open(P+n+'.png'))[box[1]:box[3],box[0]:box[2],3:]/255.*0.45
        bg=bg*(1-a)+np.array(c,np.float32)*a
    return Image.fromarray(bg.astype(np.uint8))
full=overlay((0,0,1312,2440));full=full.resize((656,1220),Image.LANCZOS)
head=overlay((250,40,1100,700))
d=ImageDraw.Draw(head)
canvas=Image.new('RGB',(656+850+20,1220),'white');canvas.paste(full,(0,0));canvas.paste(head,(676,0))
d=ImageDraw.Draw(canvas)
for i,(n,c) in enumerate(zip(names,cols)): d.rectangle((690,680+i*30,710,700+i*30),fill=c);d.text((720,684+i*30),n,fill=(0,0,0))
d.text((690,660),'overlay: each image 45% opacity in its own colour; head crop 1:1 (x250-1100,y40-700)',fill=(0,0,0))
canvas.save(P+'overlay-check.png',optimize=True)
# preview sheet on grey
sheet=Image.new('RGB',(5*(656+10)+10,1220+20),(128,128,128))
for i,n in enumerate(names):
    im=Image.open(P+n+'.png').resize((656,1220),Image.LANCZOS);sheet.paste(im,(10+i*666,10),im)
sheet.save(P+'preview-sheet.png',optimize=True)
# segment composite check: all non-woman segments over magenta vs image over magenta, plus diff
tiles=[]
for n in names[1:]:
    I=Image.open(P+n+'.png');C=Image.new('RGBA',I.size,(0,0,0,0))
    for f in sorted(glob.glob(P+'segments/'+n+'/**/*.png',recursive=True)):
        if f.endswith('woman.png'):continue
        C.alpha_composite(Image.open(f))
    m=Image.new('RGBA',I.size,(255,0,255,255));a=m.copy();a.alpha_composite(I);b=m.copy();b.alpha_composite(C)
    d=np.abs(np.array(a).astype(int)-np.array(b).astype(int)).sum(2)
    print(n,'pixels where segments-composite differs from image (within segment coverage only):',int(((d>12)&(np.array(C)[...,3]>250)).sum()))
    tiles.append(b.convert('RGB').resize((328,610)))
s=Image.new('RGB',(328*4,610),'grey')
for i,t in enumerate(tiles): s.paste(t,(i*328,0))
s.save(P+'segments-composite-check.png',optimize=True)
