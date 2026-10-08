"""One exact failed boot construction, saved before transfer diagnostics.

Parent-only bounded Blender job: -- INPUT NEW_OUT. Frozen25/31 are untouched;
this saves a rejected mesh, never a qualified production geometry report.
"""
import importlib.util
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fan_math as M


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def groups(obj, vertex):
    return {obj.vertex_groups[g.group].name: g.weight for g in obj.data.vertices[vertex].groups}


def face(obj, points, faces, index, corner_vertex=None):
    tri = obj.data.loop_triangles[index]; ids = faces[index].tolist(); loops = list(tri.loops)
    polygon = obj.data.polygons[tri.polygon_index]
    corner = ids.index(corner_vertex) if corner_vertex is not None else 0
    corners = obj.data.corner_normals
    return {'faceId': index, 'polygonId': tri.polygon_index, 'vertexIds': ids,
        'pointsLocal': points[faces[index]].tolist(), **M.triangle(points[faces[index]].tolist(), corner),
        'materialId': tri.material_index, 'smooth': polygon.use_smooth,
        'vertexNormals': [list(obj.data.vertices[i].normal) for i in ids],
        'cornerNormals': [list(corners[i].vector) for i in loops] if len(corners) else None,
        'cornerUV': {layer.name: [list(layer.data[i].uv) for i in loops] for layer in obj.data.uv_layers},
        'namedWeights': [groups(obj, i) for i in ids],
        'sourceAncestryVertexIds': [int(obj.data.attributes['ProductionOriginalVertex'].data[i].value) for i in ids]
            if obj.data.attributes.get('ProductionOriginalVertex') else None}


def main():
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 2
    input_path = Path(args[0]).resolve(); out = Path(args[1]).resolve()
    manifest = json.loads(input_path.read_text())
    engine = load(ROOT/manifest['pins']['productionAuthor']['path'], 'diagnostic34_frozen25')
    for row in manifest['pins'].values(): engine.pin(row)
    family_policy = json.loads(engine.pin(manifest['pins']['familyPolicy']).read_text())
    for row in family_policy['pins'].values(): engine.pin(row)
    family = load(engine.pin(manifest['pins']['familyAuthor']), 'diagnostic34_frozen31')
    config = json.loads(engine.pin(manifest['pins']['productionInput']).read_text())
    assert manifest['sourceObject'] == 'ActualSelectedBoot.L' and manifest['vertexId'] == 14
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-production-diagnostic34') and not out.exists()
    bpy.ops.wm.open_mainfile(filepath=str(engine.pin(config['sourceMaster'])))
    rig = bpy.data.objects[config['rig']]; assert len(rig.data.bones) == 75
    sources = {n: bpy.data.objects[n] for n, row in config['objects'].items() if row['family'] == 'boots'}
    before = family.W.retained(sources, rig)
    isolation = family.isolate([*sources.values(), rig])
    assert before == family.W.retained(sources, rig)
    rig.animation_data_clear()
    for bone in rig.pose.bones: bone.matrix_basis.identity()
    for source in sources.values():
        if source.data.shape_keys:
            for key in source.data.shape_keys.key_blocks: key.value = 0
        source.hide_set(False)
    bpy.context.view_layer.update(); out.mkdir(parents=True)
    source = sources[manifest['sourceObject']]; source_spec = config['objects'][source.name]
    target, simplification = engine.simplify(source, rig, source_spec, 'full', config)
    vertex_id = manifest['vertexId']; initial_normal = list(target.data.vertices[vertex_id].normal)
    target['qualificationState'] = 'REJECTED_DIAGNOSTIC_ONLY_BEFORE_TRANSFER'
    native = out/'REJECTED-bootL-before-transfer.blend'
    # Save the actual rejected constructor output before BVH/fan/field work.
    bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=False)
    report = {'status': 'REJECTED_TARGET_SAVED_BEFORE_TRANSFER_DIAGNOSTICS', 'acceptedArt': False,
        'sourcePins': manifest['pins'], 'sourceMaster': config['sourceMaster'],
        'recipeSHA256': engine.sha(__file__), 'inputSHA256': engine.sha(input_path),
        'native': {'path': str(native.relative_to(ROOT)), 'sha256': engine.sha(native)},
        'isolation': isolation, 'simplification': simplification,
        'vertexId': vertex_id, 'normalImmediatelyAfterSimplify': initial_normal,
        'surfaceBoundM': source_spec['maximumSurfaceErrorM'], 'minimumNormalDot': config['transfer']['minimumNormalDot'],
        'reverseSurfaceDetailAndFOURQualifiers': 'NOT RUN; all original bounds remain unchanged',
        'limits': 'One rejected left boot at the original8k allocation. Neighborhood queries measure ambiguity only; no reassignment or production acceptance.'}
    write = lambda: (out/'diagnostic.json').write_text(json.dumps(report, indent=2)+'\n')
    write()
    sp = engine.points(source); sf = engine.triangles(source)
    tp = engine.points(target); tf = engine.triangles(target)
    bvh = engine.tree(sp, sf); limit = source_spec['maximumSurfaceErrorM']
    source_normals = np.cross(sp[sf[:, 1]]-sp[sf[:, 0]], sp[sf[:, 2]]-sp[sf[:, 0]])
    source_normals /= np.maximum(np.linalg.norm(source_normals, axis=1)[:, None], 1e-30)
    names = [g.name for g in source.vertex_groups if g.name in rig.data.bones]
    sw = engine.skin_rows(source, names); tw = engine.skin_rows(target, names)
    prefix = []
    for i in range(vertex_id+1):
        near = bvh.find_nearest(Vector(tp[i]), limit)
        if near[0] is None:
            prefix.append({'vertexId': i, 'nearest': None}); break
        source_face = int(near[2]); coeff = engine.barycentric(np.asarray(near[0]), sp[sf[source_face]])
        normal = np.asarray(target.data.vertices[i].normal)
        prefix.append({'vertexId': i, 'sourceFaceId': source_face, 'distanceM': float(near[3]),
            'sourceFaceNormalDotTargetVertexNormal': float(source_normals[source_face] @ normal),
            'skinWeightL1': float(np.abs(coeff @ sw[sf[source_face]]-tw[i]).sum()),
            'sourceCoefficients': coeff.tolist()})
    report['exactFrozenTransferPrefix'] = prefix; write()
    assert len(prefix) == vertex_id+1 and prefix[-1].get('nearest', True) is not None
    nearest_id = prefix[-1]['sourceFaceId']; nearest = face(source, sp, sf, nearest_id)
    ancestry = int(target.data.attributes['ProductionOriginalVertex'].data[vertex_id].value)
    target_fan_ids = np.flatnonzero(np.any(tf == vertex_id, axis=1))
    target_fan = [face(target, tp, tf, int(i), vertex_id) for i in target_fan_ids]
    ancestry_fan = [face(source, sp, sf, int(i), ancestry) for i in np.flatnonzero(np.any(sf == ancestry, axis=1))]
    source_face_neighbors = [face(source, sp, sf, int(i)) for i in np.flatnonzero(np.any(np.isin(sf, sf[nearest_id]), axis=1))]
    local = sorted(bvh.find_nearest_range(Vector(tp[vertex_id]), limit), key=lambda row: (row[3], row[2]))
    local_rows = []
    for near in local:
        row = face(source, sp, sf, int(near[2]))
        row.update(distanceM=float(near[3]), nearestPointLocal=list(near[0]),
                   normalDotTargetVertex=M.dot(row['normal'], initial_normal))
        local_rows.append(row)
    bpy.context.view_layer.update(); target.data.update()
    after_normal = list(target.data.vertices[vertex_id].normal)
    averages = M.fan(target_fan)
    coefficients = np.asarray(prefix[-1]['sourceCoefficients'])
    interpolated_source_normals = {'vertex': M.unit((coefficients @ np.asarray(nearest['vertexNormals'])).tolist())}
    if nearest['cornerNormals']:
        interpolated_source_normals['corner'] = M.unit((coefficients @ np.asarray(nearest['cornerNormals'])).tolist())
    report.update(targetPointLocal=tp[vertex_id].tolist(), sourceAncestryVertex=ancestry,
        sourceAncestryPointLocal=sp[ancestry].tolist(), ancestryIsCollapseProvenanceProof=False,
        sourceNearestFace=nearest, sourceNearestFaceIncidentNeighborhood=source_face_neighbors,
        targetIncidentFan=target_fan, sourceAncestryIncidentFan=ancestry_fan,
        allSourceFacesWithinUnchangedSurfaceBound=local_rows, targetIndependentGeometricFanNormals=averages,
        interpolatedSourceNormals=interpolated_source_normals,
        interpolatedSourceNormalDotStoredTarget={kind: M.dot(value, initial_normal) for kind, value in interpolated_source_normals.items()},
        targetFaceNormalDotsNearestSource=[{'faceId': row['faceId'], 'dot': M.dot(row['normal'], nearest['normal'])} for row in target_fan],
        targetNormalAfterNonGeometricUpdate=after_normal,
        independentFanDeltaFromStored={kind: float(np.linalg.norm(np.asarray(value)-initial_normal)) for kind, value in averages.items()},
        targetIncidentEdges=[{'vertexIds': list(e.vertices), 'edgeId': e.index,
            'sharp': bool(target.data.attributes['sharp_edge'].data[e.index].value) if target.data.attributes.get('sharp_edge') else False}
            for e in target.data.edges if vertex_id in e.vertices],
        normalDomains={'source': source.data.normals_domain, 'target': target.data.normals_domain},
        customNormals={'source': source.data.has_custom_normals, 'target': target.data.has_custom_normals},
        sourceIdentityAfterConstruction=(before == family.W.retained(sources, rig)))
    write()
    assert report['sourceIdentityAfterConstruction']
    assert abs(prefix[-1]['sourceFaceNormalDotTargetVertexNormal']-manifest['observedNormalDot']) < 1e-6, 'Frozen failure did not reproduce'
    report['status'] = 'REPRODUCED_REJECTED_BOOT_NORMAL_CASE'; write()
    print(json.dumps({'diagnostic': str(out/'diagnostic.json'), 'native': report['native'],
                      'normalDot': prefix[-1]['sourceFaceNormalDotTargetVertexNormal'], 'acceptedArt': False}), flush=True)


if __name__ == '__main__': main()
