"""Actual CC0 native eye-weight-supported anatomy, not synthetic lid rings."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
ADDON=Path('/Users/raynos/Library/Application Support/Blender/5.1/extensions/user_default/mpfb/data')
BASE=ADDON/'3dobjs/base.obj';WEIGHTS=ADDON/'rigs/standard/weights.default.json'
OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/anatomical-eye-donor01')
PRIVATE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/anatomical-eye-donor01')
OUT.mkdir(parents=True,exist_ok=True);PRIVATE.mkdir(parents=True,exist_ok=True)
raw=BASE.read_bytes();wr=WEIGHTS.read_bytes();v=[];uv=[];polys=[];puv=[];groups=[];group=''
for line in raw.decode().splitlines():
    p=line.split()
    if not p:continue
    if p[0]=='v':v.append([float(x) for x in p[1:4]])
    elif p[0]=='vt':uv.append([float(x) for x in p[1:3]])
    elif p[0]=='g':group=' '.join(p[1:])
    elif p[0]=='f':
        polys.append([int(x.split('/')[0])-1 for x in p[1:]])
        puv.append([int(x.split('/')[1])-1 for x in p[1:]]);groups.append(group)
v=np.array(v);uv=np.array(uv);polys=np.array(polys);puv=np.array(puv);groups=np.array(groups)
body=np.flatnonzero(groups=='body');data=json.loads(wr)
np.savez_compressed(PRIVATE/'native-source.npz',positions=v,uv=uv,quads=polys[body],quadUVIndices=puv[body],sourceFaceIDs=body)

def topology(selected):
    counter=Counter(tuple(sorted((int(a),int(b)))) for fi in selected for a,b in zip(polys[fi],np.roll(polys[fi],-1)))
    boundary=np.array([edge for edge,n in counter.items() if n==1],dtype=int).reshape(-1,2)
    adjacency=coo_matrix((np.ones(len(boundary)),(boundary[:,0],boundary[:,1])),shape=(len(v),len(v))).tocsr()
    _,labels=connected_components(adjacency,directed=False)
    loops=[]
    for label in np.unique(labels[np.unique(boundary)]):
        edges=boundary[labels[boundary[:,0]]==label];ids=np.unique(edges);degrees=Counter(edges.ravel())
        loops.append({'vertices':len(ids),'vertexIDs':ids.tolist(),'degrees':dict(Counter(degrees.values())),
            'boundsRaw':[v[ids].min(0).tolist(),v[ids].max(0).tolist()],'meanRaw':v[ids].mean(0).tolist()})
    return {'boundaryLoops':loops,'nonmanifoldEdges':int(sum(n>2 for n in counter.values()))}

eyes=[]
for side in ['L','R']:
    native_groups=['eye.'+side,'oculi01.'+side,'oculi02.'+side,'orbicularis03.'+side,'orbicularis04.'+side]
    eyeweights=np.zeros(len(v));support=[]
    for name in native_groups:
        for i,w in data['weights'][name]:eyeweights[i]=max(w,eyeweights[i]);support.append((i,w))
    joint=np.unique(polys[groups=='joint-'+side.lower()+'-eye']);center=v[joint].mean(0)
    patches=[]
    for threshold in [0,.01,.1,.25,.5,.75,.9]:
        selected=body[(eyeweights[polys[body]]>threshold).all(1)]
        ids=np.unique(polys[selected]);patches.append({'minimumNativeEyeWeight':threshold,'quads':len(selected),
            'vertices':len(ids),'sourceFaceIDs':selected.tolist(),'topology':topology(selected),
            'boundsRaw':[v[ids].min(0).tolist(),v[ids].max(0).tolist()] if len(ids) else None})
    centers=v[polys[body]].mean(1)
    selected=body[(abs(centers[:,0]-center[0])<.30)&(abs(centers[:,1]-center[1])<.20)&(centers[:,2]>.8)]
    np.savez_compressed(PRIVATE/f'native-{side}-eye-support.npz',positions=v,uv=uv,
        quads=polys[selected],quadUVIndices=puv[selected],sourceFaceIDs=selected,eyeJointCenter=center,eyeWeights=eyeweights)
    # This is CPU topology projection, not Blender or game rendering.
    image=Image.new('RGB',(1200,900),(28,28,28));draw=ImageDraw.Draw(image)
    xlo,xhi=center[0]-.30,center[0]+.30;ylo,yhi=center[1]-.20,center[1]+.23
    def screen(p):return ((p[0]-xlo)/(xhi-xlo)*1199,(yhi-p[1])/(yhi-ylo)*899)
    # Wire actual native quads; brightness shows forward depth. IDs at centres
    # make source selection independently reviewable and reproducible.
    for fi in sorted(selected,key=lambda i:v[polys[i],2].mean()):
        point=v[polys[fi]];shade=int(np.clip((point[:,2].mean()-center[2])/.25*130+115,35,240))
        xy=[screen(p) for p in point]
        draw.polygon(xy,fill=(shade,shade,shade),outline=(40,150,190))
        mean=np.mean(xy,axis=0);draw.text(tuple(mean),str(fi),fill=(255,180,75))
    for i in np.unique(polys[selected]):draw.ellipse((screen(v[i])[0]-2,screen(v[i])[1]-2,screen(v[i])[0]+2,screen(v[i])[1]+2),fill=(220,220,220))
    image.save(OUT/f'native-{side}-wire.png')
    eyes.append({'side':side,'jointCenterRaw':center.tolist(),'nativeAnatomicalWeightGroups':native_groups,'nativeWeightSupportVertices':int((eyeweights>0).sum()),'patches':patches})
report={'status':'Read-only actual native orbital topology investigation; no fitted graft or visual acceptance',
    'source':str(BASE),'sourceSHA256':hashlib.sha256(raw).hexdigest(),'sourceHeader':raw.decode().splitlines()[:16],
    'nativeWeightsSource':str(WEIGHTS),'nativeWeightsSHA256':hashlib.sha256(wr).hexdigest(),
    'nativeWeightsLicense':data.get('license'),'bodyQuads':len(body),'wholeBodyTopology':topology(body),'eyes':eyes,
    'limits':['Raw hm08 Basis anatomy; no new macro pose or identity claim.',
        'Eye-weight support selects native artists orbital topology but is not yet a surgical cut.',
        'Native original positions/quad indices/UVs preserved privately; no GPU/Blender rendering, source rider editing or model generation.']}
assert BASE.read_bytes()==raw and WEIGHTS.read_bytes()==wr
(OUT/'native-anatomy-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('wholebody',report['wholeBodyTopology'])
for eye in eyes:
    print(eye['side'],eye['jointCenterRaw'])
    for patch in eye['patches']:print(patch['minimumNativeEyeWeight'],patch['quads'],patch['vertices'],[(x['vertices'],x['degrees'],x['boundsRaw']) for x in patch['topology']['boundaryLoops']])
