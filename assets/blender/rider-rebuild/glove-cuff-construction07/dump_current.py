"""Parent-serialized inspection of the actual selected cuff; no scene writes.

blender -b -t 2 --python-exit-code 1 --python dump_current.py -- FRESH_OUT
Loads the pinned master and writes only arrays/JSON below FRESH_OUT. It never
evaluates modifiers, binds, alters geometry, saves a native, or renders.
"""
import hashlib
import json
import runpy
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sections = runpy.run_path(str(HERE/'sections.py'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024*1024):
            h.update(block)
    return h.hexdigest()


def pin(row):
    path = ROOT/row['path']
    assert sha(path) == row['sha256'], ('Changed input', row)
    return path


def positions(obj):
    points = np.empty((len(obj.data.vertices), 3), dtype=np.float32)
    obj.data.vertices.foreach_get('co', points.ravel())
    matrix = np.asarray(obj.matrix_world, dtype=float)
    world = np.sum(points[:, None, :]*matrix[None, :3, :3], axis=2)+matrix[:3, 3]
    return points, world, matrix


def triangles(obj):
    obj.data.calc_loop_triangles()
    faces = np.empty((len(obj.data.loop_triangles), 3), dtype=np.int32)
    obj.data.loop_triangles.foreach_get('vertices', faces.ravel())
    return faces


def crop(obj, origin, axis, scope, material_mask=None):
    points, world, matrix = positions(obj)
    faces = triangles(obj)
    if material_mask is None:
        axial = np.sum((world-origin)*axis, axis=1)
        radial = np.linalg.norm(world-origin-axial[:, None]*axis, axis=1)
        keep = ((axial >= scope['nativeAxialRangeM'][0])
                & (axial <= scope['nativeAxialRangeM'][1])
                & (radial <= scope['nativeRadialRangeM']))
    else:
        assert len(material_mask) == len(points)
        keep = material_mask
    face_ids = np.flatnonzero(np.any(keep[faces], axis=1))
    ids = np.unique(faces[face_ids])
    remap = np.full(len(points), -1, dtype=np.int32)
    remap[ids] = np.arange(len(ids))
    data = {'nativeVertexIds': ids, 'nativeTriangleIds': face_ids,
            'localXYZ': points[ids], 'worldXYZ': world[ids],
            'faces': remap[faces[face_ids]], 'matrixWorld': matrix}
    if obj.data.uv_layers.active:
        uv = np.empty((len(obj.data.uv_layers.active.data), 2), dtype=np.float32)
        obj.data.uv_layers.active.data.foreach_get('uv', uv.ravel())
        corner_ids = np.asarray([obj.data.loop_triangles[int(i)].loops
                                 for i in face_ids], dtype=np.int32)
        data['actualCornerUV'] = uv[corner_ids]
    data['actualMaterialIndices'] = np.asarray([
        obj.data.polygons[obj.data.loop_triangles[int(i)].polygon_index].material_index
        for i in face_ids], dtype=np.int32)
    # Preserve all current authored group contributions for inspected vertices;
    # do not silently reduce them to FOUR or reconstruct fields from proximity.
    offsets, groups, weights = [0], [], []
    for vertex_id in ids:
        for item in obj.data.vertices[int(vertex_id)].groups:
            groups.append(item.group)
            weights.append(item.weight)
        offsets.append(len(groups))
    data.update(groupNames=np.asarray([g.name for g in obj.vertex_groups]),
                groupOffsets=np.asarray(offsets, dtype=np.int64),
                groupIndices=np.asarray(groups, dtype=np.int32),
                groupWeights=np.asarray(weights, dtype=np.float32))
    return data


def main():
    args = sys.argv[sys.argv.index('--')+1:]
    assert len(args) == 1
    out = Path(args[0]).resolve()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/glove-cuff-construction07')
    assert not out.exists(), 'Fresh inspection output required'
    control = json.loads((HERE/'input.json').read_text())
    for key in ('master', 'sourceGLB', 'placement', 'sourceGuide', 'denseSelected'):
        pin(control[key])
    for key in ('priorCuffGuides', 'priorAnatomicalOffsets'):
        for row in control[key].values():
            pin(row)
    source = np.load(pin(control['sourceGuide']))
    dense = np.load(pin(control['denseSelected']))
    bpy.ops.wm.open_mainfile(filepath=str(pin(control['master'])))
    rig = bpy.data.objects['RiderSkeleton']
    assert len(rig.data.bones) == 75
    assert all(b.matrix_basis.is_identity for b in rig.pose.bones), 'Rest inspection only'
    out.mkdir(parents=True)
    report = {'acceptedArt': False, 'operation': control['operation'],
              'master': control['master'], 'sourceGLB': control['sourceGLB'],
              'recipeSHA256': sha(__file__), 'sectionRecipeSHA256': sha(HERE/'sections.py'),
              'inputSHA256': sha(HERE/'input.json'), 'hands': {},
              'nativeSaved': False, 'modifiersEvaluated': False,
              'newBindings': 0, 'scope': control['scope'], 'limits': control['limits']}
    for side in ('L', 'R'):
        guide = bpy.data.objects[control['sourceObjects']['guides'][side]]
        points, world, matrix = positions(guide)
        previous = np.load(pin(control['priorCuffGuides'][side]))
        anatomical = np.load(pin(control['priorAnatomicalOffsets'][side]))
        assert np.array_equal(points, previous['corrected'].astype(np.float32))
        assert not guide.modifiers
        faces = triangles(guide)
        assert np.array_equal(faces, previous['faces'])
        wrist = np.asarray(rig.matrix_world@rig.data.bones['DEF-hand.'+side].head_local)
        elbow = np.asarray(rig.matrix_world@rig.data.bones['DEF-forearm.'+side].head_local)
        axis = elbow-wrist
        axis /= np.linalg.norm(axis)
        data = {'originalSourceXYZ': source['vertices'], 'currentLocalXYZ': points,
                'currentWorldXYZ': world, 'faces': faces, 'matrixWorld': matrix,
                'wristWorld': wrist, 'forearmAxisWorld': axis,
                'sourceUV': source['uv'], 'oldLipAnchors': control['oldLipAnchors'],
                'priorAnatomicalEditedGuideIds': np.flatnonzero(
                    np.linalg.norm(anatomical['offsets'], axis=1) > 0)}
        descriptions = []
        for section_id, ordinate in enumerate(control['diagnosticSourceYSlices']):
            loops = sections['section_loops'](source['vertices'], world, faces, ordinate)
            descriptions.append({'sourceY': ordinate, 'loopCount': len(loops),
                                 'pointCounts': [len(row['sourceEdges']) for row in loops],
                                 'sourceAreas': [row['sourcePlaneSignedArea'] for row in loops]})
            for loop_id, loop in enumerate(loops):
                for name, value in loop.items():
                    data[f'section{section_id}_loop{loop_id}_{name}'] = np.asarray(value)
        guide_path = out/f'guide-{side}.npz'
        np.savez_compressed(guide_path, **data)
        arrays = []
        dense_obj = bpy.data.objects[control['sourceObjects']['fullFields'][side]]
        assert len(dense_obj.data.vertices) == len(dense['vertices'])
        targets = [('dense-cuff', dense_obj, dense['vertices'][:, 1]
                    < control['anatomicalSourceYBoundary']),
                   ('sleeve', bpy.data.objects['RiderHoodie'], None),
                   ('wearer', bpy.data.objects['RiderBody__FullAnatomyReference'], None)]
        for label, obj, selection in targets:
            path = out/f'{label}-{side}.npz'
            payload = crop(obj, wrist, axis, control['scope'], selection)
            assert len(payload['nativeVertexIds']) > 0, ('Empty inspection crop', label, side)
            np.savez_compressed(path, **payload)
            materials = []
            for material in obj.data.materials:
                textures = []
                if material and material.use_nodes:
                    for node in material.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image:
                            image = node.image
                            textures.append({'name': image.name, 'size': list(image.size),
                                             'colorspace': image.colorspace_settings.name,
                                             'packedSHA256': hashlib.sha256(image.packed_file.data).hexdigest()
                                             if image.packed_file else None})
                materials.append({'name': material.name if material else None,
                                  'textures': textures})
            arrays.append({'object': obj.name, 'role': label,
                           'path': str(path.relative_to(ROOT)), 'sha256': sha(path),
                           'vertices': len(payload['nativeVertexIds']),
                           'triangles': len(payload['nativeTriangleIds']),
                           'materials': materials})
        report['hands'][side] = {'guideObject': guide.name,
                                 'guideArrays': {'path': str(guide_path.relative_to(ROOT)),
                                                 'sha256': sha(guide_path)},
                                 'topology': sections['topology'](world, faces),
                                 'sections': descriptions, 'localSurfaces': arrays}
    (out/'inspection.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'inspection': str((out/'inspection.json').relative_to(ROOT)),
                      'nativeSaved': False, 'hands': report['hands']}), flush=True)


if __name__ == '__main__':
    main()
