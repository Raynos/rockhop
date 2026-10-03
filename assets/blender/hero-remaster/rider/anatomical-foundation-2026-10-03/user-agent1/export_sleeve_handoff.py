"""Freeze valid-rest sleeve topology/anchors and consumed native collider settings."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
ap = argparse.ArgumentParser(description=__doc__)
for n in ['comparison', 'out']:
    ap.add_argument('--' + n, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:]); folder, out = [Path(getattr(a, n)).resolve() for n in ['comparison', 'out']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest(); setup = folder / 'comparison.blend'; pins = {'setup': sha(setup), 'comparison': sha(folder / 'comparison.json'), 'off': sha(folder / 'collision-off.json')}
out.mkdir(parents=True, exist_ok=True)
if (out / 'sleeve-rest.glb').exists():
    raise RuntimeError('Frozen sleeve handoff exists')
bpy.ops.wm.open_mainfile(filepath=str(setup))
pattern = bpy.data.objects['Eased sleeve same-pattern skinned control']; root = bpy.data.objects['Foundation file frame, game x0.65']; rig = bpy.data.objects['Independent anatomical foundation rig']
body = bpy.data.objects['Canonical anatomical body, baked adult hm08']; physics = bpy.data.objects['Same eased sleeve WITH body self cloth']
cloth = next(m for m in physics.modifiers if m.type == 'CLOTH'); settings, collisions = cloth.settings, cloth.collision_settings
for o in bpy.data.objects:
    o.select_set(False)
for o in [pattern, root, rig]:
    o.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(filepath=str(out / 'sleeve-rest.glb'), export_format='GLB', use_selection=True,
    export_yup=True, export_animations=False, export_attributes=True, export_extras=True)
mesh = pattern.data; mesh.calc_loop_triangles(); body.data.calc_loop_triangles()
weight = lambda o, v: [(o.vertex_groups[g.group].name, g.weight) for g in v.groups if g.weight > 0 and o.vertex_groups[g.group].name in rig.data.bones]
pins_group = pattern.vertex_groups['Proximal sewn ring pins']
constraints = []
for e in mesh.edges:
    i, j = e.vertices; constraints.append({'vertexIDs': [int(i), int(j)], 'restLengthM': (mesh.vertices[i].co - mesh.vertices[j].co).length})
arm_ids = set()
arm_faces = []
for ti, tri in enumerate(body.data.loop_triangles):
    average = sum(sum(w for n, w in weight(body, body.data.vertices[i]) if n in ['upperArm.L', 'forearm.L']) for i in tri.vertices) / 3
    if average > .5:
        arm_faces.append({'bodyTriangleID': ti, 'bodyVertexIDs': list(tri.vertices)}); arm_ids.update(tri.vertices)
descriptor = {'status': 'UNACCEPTED valid-rest sleeve engine handoff; native collision is not automatically exported',
    'pins': pins, 'sleeveRestGLBSHA256': sha(out / 'sleeve-rest.glb'), 'recipeSHA256': sha(__file__),
    'installedBlender': {'version': bpy.app.version_string, 'buildHash': bpy.app.build_hash.decode()},
    'axes': {'units': 'metres', 'native': '+X forward/+Z up/-Y left', 'glTF': '+X forward/+Y up/+Z left', 'nativeToGlTFCentered': '[x,z,-y]', 'rootFileX': .65, 'runtimeCenterOnceX': -.65},
    'pattern': {'name': pattern.name, 'verticesNativeM': [list(v.co) for v in mesh.vertices], 'triangleVertexIDs': [list(t.vertices) for t in mesh.loop_triangles],
        'weights': [weight(pattern, v) for v in mesh.vertices], 'sewnAnchorWeights': [next((g.weight for g in v.groups if g.group == pins_group.index), 0.) for v in mesh.vertices],
        'edgeRestConstraints': constraints, 'openBoundaryLoops': [list(range(24)), list(range(264, 288))], 'easeConstruction': '22mm prescribed radial ease beyond measured actual native arm triangle/plane cross-section; one fixed pattern'},
    'nativeConsumedColliders': {'body': {'object': body.name, 'fullNativeBodyTriangles': len(body.data.loop_triangles), 'modifierType': 'COLLISION',
        'outerThicknessM': body.collision.thickness_outer, 'innerThicknessM': body.collision.thickness_inner,
        'relevantArmTriangles': arm_faces, 'relevantArmVertices': [{'bodyVertexID': i, 'restNativeM': list(body.data.vertices[i].co), 'weights': weight(body, body.data.vertices[i])} for i in sorted(arm_ids)]},
        'cloth': {'useCollision': collisions.use_collision, 'useSelfCollision': collisions.use_self_collision, 'distanceMinM': collisions.distance_min,
            'selfDistanceMinM': collisions.self_distance_min, 'collisionQuality': collisions.collision_quality, 'quality': settings.quality, 'dynamicMesh': settings.use_dynamic_mesh,
            'pins': settings.vertex_group_mass, 'massPerVertexKg': settings.mass, 'tension': settings.tension_stiffness, 'compression': settings.compression_stiffness,
            'shear': settings.shear_stiffness, 'bending': settings.bending_stiffness},
        'installedRNADescriptions': {n: collisions.bl_rna.properties[n].description for n in ['use_collision', 'use_self_collision', 'distance_min', 'self_distance_min']}},
    'exportBehavior': 'GLB carries rest mesh/UV/weights/native51bind; Blender cloth/body collision response is NOT glTF runtime physics. Agent3 must explicitly implement bounded live response or demonstrate an exported deformation mechanism and its limits.',
    'liveEngineRequirement': 'Consume current live body colliders in garment response, including relevant self/inter-garment handling; paired collision-off/on actual game poses and measured mobile cost required. A few baked keys or intersection-only checker do not cover arbitrary poses.',
    'limits': ['Local sleeve patch, no whole hoodie/jeans/complete footwear acceptance.', 'Body/head/bind native source remains frozen; no donor/global optimizer.',
        'One garment local band has no other active garment partner; inter-garment response remains open for assembled clothes.', 'Native triangle collider differs from any bounded engine approximation, which must be independently validated.', 'No universal zero-clipping or actual engine/device pass.']}
(folder / 'engine-handoff.json').write_text(json.dumps(descriptor, indent=2) + '\n')
assert pins['setup'] == sha(setup)
print('SLEEVE_ENGINE_HANDOFF', descriptor['sleeveRestGLBSHA256'], len(arm_ids), len(arm_faces), flush=True)
