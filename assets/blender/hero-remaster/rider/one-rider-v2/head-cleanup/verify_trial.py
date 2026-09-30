"""Measure trial topology and freeze neutral-gray diagnostic evidence."""
import argparse, hashlib, json, shutil
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--trial', required=True); ap.add_argument('--evidence', required=True)
a = ap.parse_args(); trial = Path(a.trial); evidence = Path(a.evidence)
evidence.mkdir(parents=True, exist_ok=True)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p = np.load(trial / 'head.npz'); f = p['faces']; v = p['vertices']
edges, counts = np.unique(np.sort(np.concatenate((f[:, [0, 1]], f[:, [1, 2]],
                                                f[:, [2, 0]])), axis=1),
                         axis=0, return_counts=True)
boundary = edges[counts == 1]
degree = np.bincount(boundary.ravel(), minlength=len(v))
area = np.linalg.norm(np.cross(v[f[:, 1]]-v[f[:, 0]],
                              v[f[:, 2]]-v[f[:, 0]]), axis=1)
report = dict(status='UNACCEPTED first corrective trial; parent judgment pending',
              vertices=len(v), faces=len(f), boundaryEdges=len(boundary),
              boundaryVertices=int(np.sum(degree > 0)),
              boundaryDegreeExactlyTwo=bool(np.all(degree[degree > 0] == 2)),
              boundaryNativeYRange=[float(v[boundary.ravel(), 1].min()),
                                    float(v[boundary.ravel(), 1].max())],
              nonmanifoldEdges=int(np.sum(counts > 2)),
              nearZeroAreaFaces=int(np.sum(area < 1e-12)),
              sourceSHA256=json.loads((trial / 'construction.json').read_text())['sourceSHA256'],
              outputSHA256={name: sha(trial / name)
                            for name in ['head.glb', 'head.npz', 'head.blend']},
              visibleDefects=['Curly fringe and nape remnants below provisional contour.',
                              'Radial FDG discontinuities create beard pits/spikes.',
                              'Ear projection compresses undercuts.',
                              'Scalp is a plain smooth mass, no short-hair texture yet.'],
              limitations=['Topology counts do not establish anatomical quality.',
                           'Single base boundary is intentional, awaiting parent body join.',
                           'No texture bake, neck integration, rig or motion pass.'])
(evidence / 'verification.json').write_text(json.dumps(report, indent=2)+'\n')
for name in ['construction.json', 'gray/manifest.json']:
    shutil.copyfile(trial / name, evidence / Path(name).name)
canvas = Image.new('RGB', (1024, 1600), '#202326'); draw = ImageDraw.Draw(canvas)
for i, yaw in enumerate([0, 45, 90, 180]):
    source = trial / 'gray' / f'{i:04d}.png'
    shutil.copyfile(source, evidence / f'{i:04d}.png')
    x, y = (i % 2)*512, (i//2)*800
    draw.text((x+8, y+8), f'UNACCEPTED trial 1 / yaw {yaw}', fill='white')
    canvas.paste(Image.open(source).convert('RGB'), (x, y+32))
canvas.save(evidence / 'gray-four-views.jpg', quality=92)
print(json.dumps(report))
