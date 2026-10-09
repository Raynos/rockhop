"""Whole anatomical hoodie/body construction views at recorded game endpoints.

Every displayed triangle uses its full stored fields and actual game matrices.
These are CPU geometry diagrams, never PBR footage or finite-contact evidence.
The original41 glove guide has no fields, so unposed gloves are not substituted.
"""
import json
from pathlib import Path
import runpy
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
A = runpy.run_path(str(HERE/'author.py'))
ROOT, pin, checked = (A[k] for k in ('ROOT', 'pin', 'checked'))
GAME = {'path': 'harness/out/rider-rebuild/selected-authoring-motion11/gameplay-converted02/measured-gameplay-native-world.json',
        'sha256': 'f3e0444768655bf72500a9245745a559586a7717b3f6cb6b600b6e9d1d05c153'}
KEYS = ((121, 'forward endpoint'), (193, 'backward endpoint'))
EYES = ((-1., -.6, .15), (1., -.6, .15))


def pose(points, fields, groups, names, matrices):
    result = np.zeros_like(points, dtype=np.float64)
    assert np.isfinite(fields).all() and fields.min() >= 0
    assert np.max(abs(fields.sum(1)-1)) < 3e-7
    for index, name in enumerate(groups):
        weights = fields[:, index]
        if np.max(weights) > 0:
            matrix = matrices[names.index(str(name))]
            result += (points@matrix[:3, :3].T+matrix[:3, 3])*weights[:, None]
    return result


def main(receipt_path, output):
    receipt_path, output = Path(receipt_path).resolve(), Path(output).resolve()
    assert output.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-hoodie-joints77') and not output.exists()
    receipt = json.loads(receipt_path.read_text())
    binding = receipt['wholeAnatomicalFieldBinding']
    R = runpy.run_path(str(checked(binding['recipe'])))
    assert binding['recipe'] == pin(HERE/'whole_anatomical_fields.py')
    R['verify'](receipt_path)
    a = np.load(checked(receipt['receiver']))
    body_receipt = json.loads(checked(binding['bodyGuide']).read_text())
    b = np.load(checked(body_receipt['arrays']))
    garment_faces, _, face_ids = A['triangulate'](a)
    body_faces = b['triangles']
    # Keep the complete garment and the actual body above its lower edge,
    # including both hands/head. This is a viewing crop, not hidden body edits.
    lower = float(a['positions'][:, 2].min())-.05
    body_faces = body_faces[b['positions'][body_faces, 2].max(1) >= lower]
    faces = np.concatenate((garment_faces, body_faces+len(a['positions'])))
    colors = np.empty((len(faces), 3), np.float64)
    colors[:len(garment_faces)] = np.where((a['faceRoles'][face_ids] == 'selected_retained')[:, None],
                                         [174., 137., 50.], [205., 164., 69.])
    colors[len(garment_faces):] = [147., 167., 185.]
    visible_ids = np.unique(faces)
    game = json.loads(checked(GAME).read_text())
    names = game['boneNames']; rest = {bone['name']: bone for bone in game['nativeRest']['bones']}
    inverse = np.linalg.inv(np.asarray([rest[name]['matrix'] for name in names]))
    output.mkdir(parents=True)
    images = []
    for action in game['actions']:
        points = []
        for key, _ in KEYS:
            matrices = np.asarray(action['nativeWorldMatrices'][key-1])@inverse
            points.append(np.concatenate((pose(a['positions'], a['namedFields'], a['groupNames'], names, matrices),
                                          pose(b['positions'], b['normalizedNamedFields'], b['groupNames'], names, matrices))))
        image = Image.new('RGB', (1600, 1120), '#10151c'); draw = ImageDraw.Draw(image)
        for row, eye in enumerate(EYES):
            view = A['unit'](np.asarray(eye)); right = A['unit'](np.cross(view, [0, 0, 1])); up = np.cross(right, view)
            projected = [np.stack((p@right, p@up, p@view), axis=1) for p in points]
            bounds = np.concatenate([p[visible_ids, :2] for p in projected])
            low, high = bounds.min(0), bounds.max(0); middle = (low+high)/2
            scale = min(740/(high[0]-low[0]), 445/(high[1]-low[1]))
            for column, (p, projection, (key, label)) in enumerate(zip(points, projected, KEYS)):
                xy = (projection[:, :2]-middle)*[scale, -scale]+[column*800+400, row*560+315]
                normals = np.cross(p[faces[:, 1]]-p[faces[:, 0]], p[faces[:, 2]]-p[faces[:, 0]])
                lengths = np.linalg.norm(normals, axis=1)
                normals /= np.maximum(lengths[:, None], 1e-30)
                front = np.flatnonzero((lengths > 0)&(normals@view >= 0))
                order = front[np.argsort(projection[faces[front], 2].mean(1))]
                light = .3+.7*np.maximum(0, normals@A['unit'](view+np.asarray([-.3, 0, .7])))
                shades = np.clip(colors*light[:, None], 0, 255).astype(np.uint8)
                for index in order:
                    polygon = [tuple(v) for v in xy[faces[index]]]
                    draw.polygon(polygon, fill=tuple(shades[index]))
                draw.text((column*800+18, row*560+16), f'{action["bike"]} actual {key} | {label} | view {row+1}', fill='white')
                draw.text((column*800+18, row*560+36), 'Whole hoodie/full body fields; CPU geometry only; glove contact pending', fill='#abb6c3')
                draw.text((column*800+18, row*560+54), 'Selected retained panel: ochre | authored joint: gold | actual body: blue-gray', fill='#abb6c3')
        path = output/f'{action["bike"]}-actual-endpoints.png'; image.save(path); images.append(pin(path))
    report = {'status': 'WHOLE_ANATOMICAL_HOODIE_CPU_ENDPOINT_VIEWS_UNACCEPTED', 'acceptedArt': False,
              'recipe': pin(__file__), 'receiverReceipt': pin(receipt_path), 'bodyGuide': binding['bodyGuide'],
              'gameplayMatrices': GAME, 'keys': [key for key, _ in KEYS], 'viewDirections': EYES,
              'images': images, 'garmentTriangles': len(garment_faces), 'displayedBodyTriangles': len(body_faces),
              'limits': 'CPU linear skinning with all fields. Painter depth order; colors identify geometry only. No source PBR, glove fields, native parity, finite contact, or moving art acceptance.'}
    (output/'views.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'status': report['status'], 'images': images}), flush=True)


if __name__ == '__main__': main(*sys.argv[1:])
