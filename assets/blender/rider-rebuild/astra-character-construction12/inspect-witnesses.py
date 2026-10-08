"""Sparse actual06 crossing diagnosis; read only, parent bounded CPU2 lease."""
import ast
import hashlib
import json
import runpy
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
ACTUAL = ROOT/'harness/out/rider-rebuild/astra-character-construction12/authored06'
NATIVE_SHA = '3cacd79bea5e4043b250ea3d2016e0c99807fc4b70a3d3c0d28cbb530a94cd88'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1048576):
            h.update(block)
    return h.hexdigest()


def pin(row):
    path = ROOT/row['path']
    assert sha(path) == row['sha256'], row['path']
    return path


def load_objects(path, names):
    with bpy.data.libraries.load(str(path), link=False) as (available, loaded):
        assert all(name in available.objects for name in names)
        loaded.objects = names
    return dict(zip(names, loaded.objects))


def world(obj, ids):
    local = np.array([obj.data.vertices[int(i)].co[:] for i in ids], dtype=float)
    matrix = np.asarray(obj.matrix_world, dtype=float)
    return np.sum(local[:, None, :]*matrix[None, :3, :3], axis=2)+matrix[:3, 3]


def triangle(points):
    edges = np.roll(points, -1, axis=0)-points
    normal = np.cross(edges[0], -edges[2]); length = np.linalg.norm(normal)
    return {'worldXYZ': points.tolist(), 'edgeLengthsM': np.linalg.norm(edges, axis=1).tolist(),
            'areaM2': float(length/2), 'unitNormal': (normal/length).tolist() if length else None}


def main():
    args = sys.argv[sys.argv.index('--')+1:]
    assert len(args) == 1
    out = Path(args[0]).resolve()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/astra-character-construction12') and not out.exists()
    config = json.loads((HERE/'input.json').read_text())
    prior = json.loads(pin(config['priorInputs']).read_text())
    native = ACTUAL/'UNACCEPTED-complete-selected-rider.blend'
    assert sha(native) == NATIVE_SHA
    report = json.loads((ACTUAL/'construction.json').read_text())
    assert report['native']['sha256'] == NATIVE_SHA
    names = ['RiderHoodie', 'RiderBody', 'ActualSelectedGlove.L', 'ActualSelectedGlove.R']
    actual = load_objects(native, names)
    baseline = load_objects(pin(prior['master']), names)
    assert sha(HERE/'input.json') == report['inputSHA256']
    helper_path = pin({'path': 'assets/blender/rider-rebuild/astra-character-construction12/inspect-source.py',
                       'sha256': 'f1f7c17b346d69bd5ac47252869464452c8d7918411890b5b4984bd2b9b38c69'})
    helper = runpy.run_path(str(helper_path))
    source, source_faces = helper['read_source'](pin(prior['originalHoodie']))
    source_glove = np.load(pin(prior['originalGloveDense']))['vertices']
    controls = json.loads(pin(prior['hoodieSourceFrames']).read_text())
    source_world = source*np.asarray(controls['sourceDisplayAffine']['scale'])+np.asarray(controls['sourceDisplayAffine']['translation'])
    source_sorted = np.sort(source_faces, axis=1)
    ancestry = {name: np.load(pin(report['objects'][name]['ancestry'])) for name in names if name != 'RiderBody'}
    module = ast.parse(pin(config['intersectionHelper']).read_text())
    namespace = {'np': np}
    exec(compile(ast.Module(body=[node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'strict_cross'], type_ignores=[]), 'pinned-strict-cross', 'exec'), namespace)
    strict_cross = namespace['strict_cross']
    result = {'acceptedArt': False, 'native': report['native'], 'baseline': prior['master'],
              'recipeSHA256': sha(Path(__file__)), 'constructionSHA256': sha(ACTUAL/'construction.json'),
              'method': 'Only the saved first crossing pairs and reported degenerate witness; no fit, geometry edit, broadphase or new crossing search.', 'hands': {}}
    for side in ('L', 'R'):
        guide = np.load(pin(prior['guideArrays'][side]))
        wrist = guide['wristWorld'].astype(float); axis = guide['forearmAxisWorld'].astype(float); axis /= np.linalg.norm(axis)
        bone = next(b for b in controls['authoringBones'] if b['name'] == 'AUTHOR_Forearm.'+side)
        head = np.asarray(bone['sourceHead']); vector = np.asarray(bone['sourceTail'])-head
        source_axis = vector/np.linalg.norm(vector)
        scalar = np.sum((source_world-head)*source_axis, axis=1)
        radial = np.linalg.norm(source_world-head-scalar[:, None]*source_axis, axis=1)
        selected = ((source_world[:, 0] > 0) if side == 'L' else (source_world[:, 0] < 0)) & (scalar > .4*np.linalg.norm(vector)) & (radial < .15)
        lower, cut = scalar[selected].min(), report['hands'][side]['sleeve']['sourceCutAxialM']
        def details(name, ids):
            ids = np.asarray(ids, dtype=int)
            ap, bp = world(actual[name], ids), world(baseline[name], ids)
            axial = np.sum((ap-wrist)*axis, axis=1)
            radius = np.linalg.norm(ap-wrist-axial[:, None]*axis, axis=1)
            row = {'object': name, 'nativeVertexIds': ids.tolist(), 'actual': triangle(ap), 'baseline': triangle(bp),
                   'exactlyUnchangedWorld': bool(np.array_equal(ap, bp)), 'actualAxialM': axial.tolist(), 'actualRadialM': radius.tolist(),
                   'actualOwnSide': ((ap[:, 0] > 0) if side == 'L' else (ap[:, 0] < 0)).tolist()}
            if name in ancestry:
                anc = ancestry[name]
                row.update(vertexRoles=anc['authoredVertexRoles'][ids].tolist(), sourceVertexIds=anc['vertexSourceIds'][ids].tolist(),
                           parentSourceIds=anc['vertexParentSourceIds'][ids].tolist(), parentCoefficients=anc['vertexParentCoefficients'][ids].tolist())
            if name == 'RiderHoodie':
                station = .031+(cut-scalar[ids])/(cut-lower)*(.18-.031)
                blend = np.clip((.18-station)/(.18-.13), 0, 1); alpha = blend*blend*(3-2*blend)
                row.update(originalSource=triangle(source_world[ids]), sourceFaceIds=np.flatnonzero(np.all(source_sorted == np.sort(ids), axis=1)).tolist(),
                           selected=selected[ids].tolist(), sourceAxialM=scalar[ids].tolist(), sourceRadialM=radial[ids].tolist(),
                           proposedAxialM=station.tolist(), blendAlpha=alpha.tolist())
            elif name.startswith('ActualSelectedGlove.'):
                row['originalSource'] = triangle(source_glove[ids])
            return row, ap, bp
        rows = {}
        for name, gate in report['hands'][side]['geometry'].items():
            row = {'gateResult': gate}
            if 'firstTriangleVertexIds' in gate:
                pair_names = {'sleeveSelf': ('RiderHoodie', 'RiderHoodie'),
                    'gloveSleeve': ('ActualSelectedGlove.'+side, 'RiderHoodie'),
                    'sleeveVisibleWearer': ('RiderHoodie', 'RiderBody'),
                    'gloveVisibleWearer': ('ActualSelectedGlove.'+side, 'RiderBody'),
                    'gloveSelf': ('ActualSelectedGlove.'+side, 'ActualSelectedGlove.'+side)}[name]
                first, ap, bp = details(pair_names[0], gate['firstTriangleVertexIds'])
                second, aq, bq = details(pair_names[1], gate['secondTriangleVertexIds'])
                row.update(first=first, second=second, actualCross=bool(strict_cross(ap, aq)), baselineCross=bool(strict_cross(bp, bq)))
                if name == 'sleeveSelf':
                    row['originalSourceCross'] = bool(strict_cross(np.asarray(first['originalSource']['worldXYZ']), np.asarray(second['originalSource']['worldXYZ'])))
                assert row['actualCross'], ('Saved witness does not reproduce', side, name)
            row['degenerateWitnesses'] = []
            for degenerate in gate['degenerateDiagnostics']:
                object_name = 'RiderHoodie' if name != 'gloveSelf' else 'ActualSelectedGlove.'+side
                entry, _, _ = details(object_name, degenerate['nativeVertexIds'])
                row['degenerateWitnesses'].append(entry)
            rows[name] = row
        result['hands'][side] = rows
    out.mkdir(parents=True)
    path = out/'witnesses.json'; path.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'output': str(path.relative_to(ROOT)), 'sha256': sha(path)}), flush=True)


if __name__ == '__main__':
    main()
