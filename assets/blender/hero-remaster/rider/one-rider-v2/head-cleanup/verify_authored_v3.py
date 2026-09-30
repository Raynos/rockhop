"""Freeze actual authored-cage feasibility, errors and visible failed shape."""
import argparse,hashlib,json,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--runtime',required=True);ap.add_argument('--evidence',required=True)
a=ap.parse_args();runtime=Path(a.runtime);evidence=Path(a.evidence)
evidence.mkdir(parents=True,exist_ok=True);fitted=runtime/'fitted'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=np.load(fitted/'head.npz');v,f=p['vertices'],p['faces']
e,c=np.unique(np.sort(np.concatenate((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]])),axis=1),axis=0,return_counts=True)
boundary=e[c==1];degree=np.bincount(boundary.ravel(),minlength=len(v))
area=np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)
construction=json.loads((fitted/'construction.json').read_text())
report=dict(status='UNACCEPTED authored feasibility; visible anatomy fails; no bake',
    topology=dict(vertices=len(v),faces=len(f),boundaryEdges=len(boundary),
        boundaryDegreeExactlyTwo=bool(np.all(degree[degree>0]==2)),
        boundaryNativeYRange=[float(v[boundary.ravel(),1].min()),float(v[boundary.ravel(),1].max())],
        nonmanifoldEdges=int(np.sum(c>2)),nearZeroAreaFaces=int(np.sum(area<1e-12))),
    sourcesUnchanged=construction['sources']==construction['sourcesAfter'],
    initialSourceGuide=construction['initialSourceGuide'],boundedDenseFit=construction['boundedDenseFit'],
    outputSHA256={name:sha(fitted/name) for name in ['head.npz','head.glb','head.blend','fit-samples.npz']},
    visibleDefects=['Severe face-to-temple transitions and cheek seams.',
        'Nostril spikes and residual forehead/beard irregularities.',
        'Simplified displaced ears do not preserve source folded anatomy convincingly.',
        'Faceted jaw/neck transitions and generic crown proportions.'],
    limit='Numerically small accepted-sample error does not measure rejected or authored regions.',
    noFurtherGeometryCorrection=True,noTextures=True,noNeckFit=True)
(evidence/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
shutil.copyfile(runtime/'constrained-layout/layout.json',evidence/'constrained-layout.json')
shutil.copyfile(fitted/'construction.json',evidence/'construction.json')
for mode in ['gray','closeups']:
    target=evidence/mode;target.mkdir(exist_ok=True)
    shutil.copyfile(fitted/mode/'manifest.json',target/'manifest.json')
    width,height=(512,768) if mode=='gray' else (768,768)
    board=Image.new('RGB',(2*width,2*(height+32)),'#202326');d=ImageDraw.Draw(board)
    for i,yaw in enumerate([0,45,90,180]):
        path=fitted/mode/f'{i:04d}.png';shutil.copyfile(path,target/path.name)
        x,y=i%2*width,i//2*(height+32)
        d.text((x+8,y+8),f'UNACCEPTED authored feasibility / yaw {yaw}',fill='white')
        board.paste(Image.open(path).convert('RGB'),(x,y+32))
    board.save(target/'four-views.jpg',quality=92)
print(json.dumps(report))
