"""Unrun six actual poses, rest contacts and true z-buffer construction views.

Run only after parent grant under the original96/CPU2/300s guard. This is
geometry evidence, never source-PBR or moving-art acceptance.
"""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
R = runpy.run_path(str(HERE/'refit.py'))
ROOT, OUT = R['ROOT'], R['OUT']
CONTACT = ROOT/'assets/blender/rider-rebuild/selected-hoodie-joints77/posed_contact15.py'
CONTACT_SHA = 'fc543e997f60be4b7591990b370bb54b91dfd5093a15fe2f5486fc42d2f804e0'


def depth_view(p, f, q, g, roles, path, label):
    # Import bundled NumPy before the matching cp313 Pillow site; never cp314.
    sys.path.append('/opt/homebrew/lib/python3.13/site-packages')
    from PIL import Image, ImageDraw
    points = np.concatenate((p, q)); faces = np.concatenate((f, g+len(p)))
    eye = np.asarray([1., -.65, .1]); eye /= np.linalg.norm(eye)
    right = np.cross(eye, [0., 0., 1.]); right /= np.linalg.norm(right); up = np.cross(right, eye)
    projection = points@np.stack((right, up, eye), axis=1)
    low, high = projection[:len(p), :2].min(0), projection[:len(p), :2].max(0)
    scale = min(660/(high[0]-low[0]), 720/(high[1]-low[1]))
    xy = (projection[:, :2]-(low+high)/2)*[scale, -scale]+[360, 420]
    zbuffer = np.full((800, 720), -np.inf); pixels = np.full((800, 720, 3), [16, 21, 28], np.uint8)
    normal = np.cross(points[faces[:, 1]]-points[faces[:, 0]], points[faces[:, 2]]-points[faces[:, 0]])
    length = np.linalg.norm(normal, axis=1); visible = np.flatnonzero((length > 1e-14)&(normal@eye > 0))
    colors = np.full((len(faces), 3), [147., 167., 185.])
    colors[:len(f)] = np.where((roles == 'selected_retained')[:, None], [174., 137., 50.], [205., 164., 69.])
    light = .3+.7*np.maximum(0., (normal@eye)/np.maximum(length, 1e-30)); colors = (colors*light[:, None]).astype(np.uint8)
    for fi in visible:
        triangle = faces[fi]; uv = xy[triangle]
        lo = np.maximum(np.floor(uv.min(0)).astype(int), [0, 0]); hi = np.minimum(np.ceil(uv.max(0)).astype(int), [719, 799])
        if np.any(hi < lo): continue
        x, y = np.meshgrid(np.arange(lo[0], hi[0]+1)+.5, np.arange(lo[1], hi[1]+1)+.5)
        v, w = uv[1]-uv[0], uv[2]-uv[0]; det = v[0]*w[1]-v[1]*w[0]
        if abs(det) < 1e-12: continue
        dx, dy = x-uv[0, 0], y-uv[0, 1]
        beta, gamma = (dx*w[1]-dy*w[0])/det, (v[0]*dy-v[1]*dx)/det
        alpha = 1-beta-gamma; z = alpha*projection[triangle[0], 2]+beta*projection[triangle[1], 2]+gamma*projection[triangle[2], 2]
        window = zbuffer[lo[1]:hi[1]+1, lo[0]:hi[0]+1]
        mask = (alpha >= 0)&(beta >= 0)&(gamma >= 0)&(z > window)
        window[mask] = z[mask]; pixels[lo[1]:hi[1]+1, lo[0]:hi[0]+1][mask] = colors[fi]
    image = Image.fromarray(pixels); draw = ImageDraw.Draw(image)
    draw.text((12, 12), label+' | per-pixel depth | unaccepted geometry', fill='white'); image.save(path)


def main(receipt_path, output):
    controller = int(os.environ['ROCKHOP_GENERATION_CONTROLLER_PID']); assert controller == os.getppid()
    assert sys.version_info[:2] == (3, 13) and np.__version__ == '2.3.4'
    assert os.environ['OPENBLAS_NUM_THREADS'] == os.environ['OMP_NUM_THREADS'] == '2'
    assert hashlib.sha256(CONTACT.read_bytes()).hexdigest() == CONTACT_SHA
    C = runpy.run_path(str(CONTACT)); A = runpy.run_path(str(R['checked']('author')))
    receipt = R['verify'](receipt_path); a = np.load(ROOT/receipt['receiver']['path'])
    _, _, body, b, _, _ = R['inputs']()
    game = json.loads(C['checked']('game').read_text())
    f, _, polygon = A['triangulate'](a); g = b['triangles']
    pose = C['frozen_function']('viewsBase', 'pose'); strict = C['frozen_function']('crossing', 'strict_cross')
    names = game['boneNames']; rest = {row['name']: row for row in game['nativeRest']['bones']}
    assert all(row[4] == rest[row[0]]['matrix'] and row[1] == rest[row[0]]['parent'] for row in body['rest'])
    inverse = np.linalg.inv(np.asarray([rest[name]['matrix'] for name in names]))
    output = Path(output).resolve(); assert output.is_relative_to(OUT) and not output.exists(); output.mkdir(parents=True)
    cases = [('rest', 0, np.broadcast_to(np.eye(4), (75, 4, 4)))]
    cases += [(action['bike'], frame, np.asarray(action['nativeWorldMatrices'][frame-1])@inverse)
              for action in game['actions'] for frame in (121, 129, 193)]
    rows = []
    for bike, frame, matrices in cases:
        p = pose(a['positions'], a['namedFields'], a['groupNames'], names, matrices)
        q = pose(b['positions'], b['normalizedNamedFields'], b['groupNames'], names, matrices)
        pairs, sb, sg, invalid, magnitudes, tested = C['measure'](p, f, q, g, strict)
        artifact = output/f'{bike}-{frame}-contacts.npz'
        np.savez_compressed(artifact, garmentPosed=p, bodyPosed=q, garmentTriangles=f, bodyTriangles=g,
            garmentPolygonIds=polygon, crossingTrianglePairs=pairs, garmentSignedBodyPlaneM=sb, bodySignedGarmentPlaneM=sg)
        row = {'bike': bike, 'frame': frame, 'arrays': R['pin'](artifact), 'strictCrossingPairs': len(pairs),
            'pairsByGarmentRole': dict(Counter(a['faceRoles'][polygon[pairs[:, 0]]].tolist())),
            'testedBroadphasePairs': tested, 'degenerateTriangleIds': [v.tolist() for v in invalid]}
        if bike == 'pro' and frame in (121, 193):
            image = output/f'{bike}-{frame}-depth.png'
            depth_view(p, f, q, g, a['faceRoles'][polygon], image, f'Pro actual {frame}'); row['depthView'] = R['pin'](image)
        rows.append(row); print(json.dumps({k:row[k] for k in ('bike', 'frame', 'strictCrossingPairs')}), flush=True)
    result = {'status':'LOCAL17_REST_AND_SIX_ACTUAL_POSES_UNACCEPTED', 'acceptedArt':False,
        'recipe':R['pin'](__file__), 'receiverReceipt':R['pin'](receipt_path), 'bodyGuide':receipt['localRestBodyBinding']['bodyGuide'],
        'gameplayMatrices':C['pin'](C['checked']('game')), 'rows':rows,
        'limits':'Full71 CPU skinning and finite triangle crossing evidence only. Depth images have no source PBR. All482/native/export parity and played master review remain open.'}
    (output/'posed-contact.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 2; main(*args)
