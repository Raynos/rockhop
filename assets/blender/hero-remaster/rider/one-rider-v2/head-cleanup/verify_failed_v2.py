"""Freeze actual failed scalp-cut evidence; do not invent a dense-fit metric."""
import argparse, hashlib, json, shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--runtime',required=True);ap.add_argument('--evidence',required=True)
a=ap.parse_args();runtime=Path(a.runtime);evidence=Path(a.evidence)
evidence.mkdir(parents=True,exist_ok=True)
trial=runtime/'trial2-diagnostic';p=np.load(trial/'cut.npz')
v,f=p['vertices'],p['faces']
e,c=np.unique(np.sort(np.concatenate((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]])),axis=1),axis=0,return_counts=True)
area=np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
report=dict(status='FAILED corrective attempt2; method stopped; no accepted head',
            actualCutVertices=len(v),actualCutFaces=len(f),boundaryEdges=int(np.sum(c==1)),
            nonmanifoldEdges=int(np.sum(c>2)),nearZeroAreaFaces=int(np.sum(area<1e-12)),
            scaffoldGate='zero nonmanifold edges; 15 rear-scalp boundary edges before cut',
            stitchGate=json.loads((runtime/'trial2-head/failed-preflight.json').read_text()),
            denseDetailFit=dict(performed=False,errorMeasurement=None,
                reason='Stopped at scalp contour gate before subdivision or fitting'),
            sourceSHA256=dict(dense=sha('/Users/raynos/Documents/Codex/2026-09-30/task-2/comparison/bust/generation-v1/raw.npz'),
                reduced=sha('/Users/raynos/Documents/Codex/2026-09-30/task-2/comparison/bust/generation-v1/bust.glb')),
            outputSHA256={name:sha(trial/name) for name in ['cut.npz','cut.glb','cut.blend']},
            exportWarning='Blender exporter reports mesh invalid; diagnostic only',
            visibleDefects=['No scalp cap: 19 scalp contours prevent one clean sewn boundary.',
                'Fringe/temple/nape curl remnants remain visible.',
                'Beard irregularities remain, inherited from original scaffold.',
                'Two base contours prevent a single intended neck join.'],
            limits=['Neutral-gray diagnostics are the failed cut, not a complete corrected head.',
                    'No bake, new texture, fitted dense face, joined body, rig or moving proof.'])
(evidence/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
for relative in ['trial2-scaffold/scaffold-report.json','trial2-finalized/finalize-report.json',
                 'trial2-split/split-report.json','trial2-sewn/finalize-report.json',
                 'trial2-head/failed-preflight.json','trial2-diagnostic/diagnostic.json',
                 'trial2-diagnostic/gray/manifest.json']:
    path=runtime/relative;name=relative.replace('/','--')
    shutil.copyfile(path,evidence/name)
canvas=Image.new('RGB',(1024,1600),'#202326');draw=ImageDraw.Draw(canvas)
for i,yaw in enumerate([0,45,90,180]):
    path=trial/'gray'/f'{i:04d}.png';shutil.copyfile(path,evidence/path.name)
    x,y=i%2*512,i//2*800
    draw.text((x+8,y+8),f'FAILED trial 2 / cut only / yaw {yaw}',fill='white')
    canvas.paste(Image.open(path).convert('RGB'),(x,y+32))
canvas.save(evidence/'gray-four-views.jpg',quality=92)
print(json.dumps(report))
