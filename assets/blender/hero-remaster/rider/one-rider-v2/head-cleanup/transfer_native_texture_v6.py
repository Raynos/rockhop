"""ONE CPU donor attribute/UV transfer; geometry never moves.

Transfer source albedo/roughness/metallic onto retained native UVs through
an explicit texture-only coordinate adapter. Ears/back/neck use calibrated
skin fallback; scalp uses compact stubble color, never donor curly hair.
"""
import argparse,json,hashlib,time
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.ndimage import distance_transform_edt
from PIL import Image
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--data',required=True)
ap.add_argument('--donor',required=True);ap.add_argument('--out',required=True);ap.add_argument('--size',type=int,default=2048)
a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
if (out/'skin-basecolor.png').exists():raise RuntimeError('Frozen texture transfer exists')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
before={p:sha(p) for p in [a.data,a.donor]};start=time.monotonic()
d=np.load(a.data);v=d['vertices'];f=d['faces'];uv=d['triangleUV'];size=a.size
positions=np.zeros((size,size,3),np.float32);semantic=np.zeros((size,size,3),np.float32)
covered=np.zeros((size,size),bool);overlap=0
sem=np.stack([d['scalp'],d['ears'],d['lips']],axis=1)
for ids,triuv in zip(f,uv):
    p=triuv*size-.5
    lo=np.maximum(np.floor(p.min(0)).astype(int),0);hi=np.minimum(np.ceil(p.max(0)).astype(int),size-1)
    if np.any(lo>hi):continue
    denominator=(p[1,1]-p[2,1])*(p[0,0]-p[2,0])+(p[2,0]-p[1,0])*(p[0,1]-p[2,1])
    if abs(denominator)<1e-9:continue
    yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
    w0=((p[1,1]-p[2,1])*(xx-p[2,0])+(p[2,0]-p[1,0])*(yy-p[2,1]))/denominator
    w1=((p[2,1]-p[0,1])*(xx-p[2,0])+(p[0,0]-p[2,0])*(yy-p[2,1]))/denominator
    w2=1-w0-w1;inside=(w0>=-1e-6)&(w1>=-1e-6)&(w2>=-1e-6)
    if not inside.any():continue
    weights=np.stack([w0[inside],w1[inside],w2[inside]],axis=1)
    yi=yy[inside];xi=xx[inside];pts=weights@v[ids]
    overlap+=int(np.sum(covered[yi,xi]&(np.linalg.norm(positions[yi,xi]-pts,axis=1)>.002)))
    positions[yi,xi]=pts;semantic[yi,xi]=weights@sem[ids];covered[yi,xi]=True
q=positions[covered];groups=semantic[covered]
source=np.load(a.donor);sv=source['vertices'];attrs=np.clip(source['attrs'],0,1)
# Spatial bounds remove all crown curls. Only front face skin/detail can
# transfer; ears, back and neck are expressly excluded from donor sampling.
eligible=(np.abs(sv[:,0])<.18)&(sv[:,1]>-.18)&(sv[:,1]<.235)&(sv[:,2]>.10)
ids=np.flatnonzero(eligible);tree=cKDTree(sv[ids])
query=q.copy();query[:,0]*=.784
query[:,1]=np.interp(q[:,1],[-.35,-.205,-.080,.111,.250,.400],[-.28,-.140,-.083,.058,.215,.40])
query[:,2]*=1.0
distance,index=tree.query(query,k=1,workers=4);nearest=attrs[ids[index]]
front=(q[:,2]>.10)&(q[:,1]>-.23)&(q[:,1]<.265)&(groups[:,1]<.05)&(groups[:,0]<.05)
valid=front&(distance<.045)
# Calibrate fallback from verified donor cheek samples, excluding dark beard.
cheek=(np.abs(sv[ids,0])>.07)&(sv[ids,1]>.015)&(sv[ids,1]<.09)&(attrs[ids,0]>.4)
skin=np.median(attrs[ids[cheek],:3],axis=0)
rgb=np.broadcast_to(skin,(len(q),3)).copy();rough=np.full(len(q),.60,np.float32);metal=np.zeros(len(q),np.float32)
blend=np.clip((.045-distance)/.015,0,1)*valid
rgb=rgb*(1-blend[:,None])+nearest[:,:3]*blend[:,None]
rough=rough*(1-blend)+nearest[:,4]*blend;metal=np.clip(nearest[:,3]*blend,0,.02)
# Solid anatomical scalp coverage remains the same surface. Stubble is an
# albedo hypothesis; no displacement, curls, shell, or donor hair detail.
hair=np.clip((groups[:,0]-.1)/.7,0,1)
noise=np.sin(q[:,0]*2700+q[:,1]*2100)*np.sin(q[:,2]*3200-q[:,0]*1700)
hair_rgb=np.array([.055,.039,.028])[None,:]*(1+noise[:,None]*.18)
rgb=rgb*(1-hair[:,None])+hair_rgb*hair[:,None];rough=rough*(1-hair)+.82*hair
maps={}
for name,values in [('skin-basecolor',rgb),('skin-roughness',rough),('skin-metallic',metal)]:
    channels=3 if values.ndim==2 else 1
    image=np.zeros((size,size,channels),np.float32)
    image[covered]=values if channels==3 else values[:,None]
    # Native UV island padding prevents black seams without copying one
    # anatomical region onto another. Nearest covered texel, six pixels.
    gap,nearest_pixel=distance_transform_edt(~covered,return_indices=True)
    pad=(~covered)&(gap<=6);image[pad]=image[nearest_pixel[0,pad],nearest_pixel[1,pad]]
    if channels==1:image=image[:,:,0]
    Image.fromarray(np.uint8(np.clip(np.flipud(image),0,1)*255)).save(out/(name+'.png'))
    maps[name]=dict(path=str(out/(name+'.png')),sha256=sha(out/(name+'.png')))
def stats(x):return dict(count=len(x),maximum=float(np.max(x)) if len(x) else None,
    percentiles=np.percentile(x,[50,95,99]).tolist() if len(x) else [])
report=dict(status='UNACCEPTED CPU donor albedo/PBR attribute transfer; actual render review',
    sourceProof={p:dict(before=s,after=sha(p),unchanged=s==sha(p)) for p,s in before.items()},
    scriptSHA256=sha(__file__),nativeUVSize=size,coveredTexels=int(covered.sum()),
    UVPositionConflictTexels=overlap,paddingPixels=6,donorEligibleVertices=len(ids),
    frontEligibleTexels=int(front.sum()),acceptedDonorTexels=int(valid.sum()),
    acceptedFrontCoverage=float(valid.sum()/max(front.sum(),1)),
    donorDistanceNative=stats(distance[valid]),rejectedFrontDistanceNative=stats(distance[front&~valid]),
    scalpTexels=int(np.sum(hair>.5)),fallbackSkinRGB=skin.tolist(),
    textureOnlyAdapter=dict(xScale=.784,ySource=[-.35,-.205,-.080,.111,.250,.400],
        yDonor=[-.28,-.140,-.083,.058,.215,.40],zScale=1.0,
        explanation='Approximate front feature correspondence for TEXTURE sampling only; native approved geometry unchanged.'),
    maps=maps,wallSeconds=time.monotonic()-start,
    limits=['No shape snapping or vertex displacement; reference likeness remains approximate.',
        'Donor transfer covers only eligible front skin; ears/neck/back use calibrated skin fallback.',
        'Roughness/metallic transferred where donor accepted; no donor normal/displacement bake claimed.',
        'Compact stubble is albedo on continuous native scalp; hair texture is a hypothesis.',
        'Approximate texture-only adapter may misalign brows/lips; actual render judges it.'])
assert all(x['unchanged'] for x in report['sourceProof'].values())
(out/'transfer.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
