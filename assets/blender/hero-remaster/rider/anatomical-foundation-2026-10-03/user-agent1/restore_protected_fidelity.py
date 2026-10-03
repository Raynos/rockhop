"""Restore exact protected normals/specular factors without geometry changes."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
import numpy as np
ap = argparse.ArgumentParser(description=__doc__)
for n in ['source', 'donor', 'out', 'evidence']:
    ap.add_argument('--' + n, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, donor, out, evidence = [Path(getattr(a, n)).resolve() for n in ['source', 'donor', 'out', 'evidence']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest(); pins = {str(p): sha(p) for p in [source, donor]}
assert pins[str(donor)] == 'b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
out.mkdir(parents=True, exist_ok=True); evidence.mkdir(parents=True, exist_ok=True)
if (out / 'rider.blend').exists():
    raise RuntimeError('Frozen fidelity derivative exists')
bpy.ops.wm.open_mainfile(filepath=str(source))
raw = donor.read_bytes(); length = int.from_bytes(raw[12:16], 'little'); doc = json.loads(raw[20:20+length]); binary = raw[28+length:]
def acc(i):
    a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]; c = {'SCALAR': 1, 'VEC3': 3}[a['type']]; dt = np.dtype({5126: '<f4', 5123: '<u2', 5125: '<u4'}[a['componentType']])
    return np.ndarray((a['count'], c), dtype=dt, buffer=binary, offset=v.get('byteOffset', 0) + a.get('byteOffset', 0), strides=(v.get('byteStride', c*dt.itemsize), dt.itemsize)).copy()
rows = []
for pi, name in [(0, 'Protected textured head above hidden neck interface'), (1, 'Protected coherent cheek patch')]:
    p = doc['meshes'][1]['primitives'][pi]; pos, normal = [acc(p['attributes'][n]) for n in ['POSITION', 'NORMAL']]; faces = acc(p['indices']).reshape(-1, 3)
    valid = pos[:, 1] >= 1.525; used = np.unique(faces[np.all(valid[faces], axis=1)])
    o = bpy.data.objects[name]; expected = np.column_stack([pos[used, 0]-.65, -pos[used, 2], pos[used, 1]])
    observed = np.array([v.co[:] for v in o.data.vertices]); error = float(np.max(np.abs(observed-expected)))
    assert len(used) == len(o.data.vertices) and error < 1e-7
    target = np.column_stack([normal[used, 0], -normal[used, 2], normal[used, 1]])
    o.data.normals_split_custom_set_from_vertices(target.tolist()); o.data.update()
    rows.append({'name': name, 'sourceMesh': 1, 'primitive': pi, 'vertices': len(used), 'maximumUnchangedPositionErrorM': error,
        'sourceUsedIDsSHA256': hashlib.sha256(used.astype('<u4').tobytes()).hexdigest(),
        'sourceNormalNativeFloat32SHA256': hashlib.sha256(target.astype('<f4').tobytes()).hexdigest()})
materials = []
for index in [1, 2, 3, 4]:
    m = bpy.data.materials.get(f'Appearance exact donor material {index}')
    if m is None:
        continue
    factor = doc['materials'][index].get('extensions', {}).get('KHR_materials_specular', {}).get('specularFactor', 1.)
    bs = m.node_tree.nodes['Principled BSDF']; bs.inputs['Specular IOR Level'].default_value = factor * .5
    materials.append({'name': m.name, 'sourceMaterial': index, 'expectedKHRSpecularFactor': factor, 'BlenderSpecularIORLevel': factor*.5})
for m in bpy.data.materials:
    if m.name.startswith('Transferred approved ') and m.use_nodes:
        m.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = .125
        materials.append({'name': m.name, 'sourceMaterial': 0, 'expectedKHRSpecularFactor': .25, 'BlenderSpecularIORLevel': .125})
root = bpy.data.objects['Foundation file frame, game x0.65']; rig = bpy.data.objects['Independent anatomical foundation rig']
root['rockhopAppearanceCandidate'] = 'unaccepted appearance03 protected shading fidelity'
for o in bpy.data.objects:
    o.select_set(False)
for o in [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render]+[root, rig]:
    o.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.wm.save_as_mainfile(filepath=str(out/'rider.blend'), compress=True)
bpy.ops.export_scene.gltf(filepath=str(out/'rider.glb'), export_format='GLB', use_selection=True, export_yup=True,
    export_animations=False, export_attributes=True, export_extras=True, export_morph=True)
controller = json.loads((source.parent/'corrective-driver.json').read_text()); controller.update(status='UNACCEPTED appearance03 source-shading fidelity, unchanged local corrective controller',
    candidateMasterSHA256=sha(out/'rider.blend'), candidateGLBSHA256=sha(out/'rider.glb'), parentAppearanceMasterSHA256=sha(source))
(out/'corrective-driver.json').write_text(json.dumps(controller, indent=2)+'\n')
assert pins == {str(p): sha(p) for p in [source, donor]}
report = {'status': 'UNACCEPTED protected normal/specular fidelity derivative; export verification pending', 'pins': pins,
    'masterSHA256': sha(out/'rider.blend'), 'GLBSHA256': sha(out/'rider.glb'), 'recipeSHA256': sha(__file__),
    'protectedNormalRestoration': rows, 'materialFactorRestoration': materials,
    'limits': ['Only protected head/cheek custom normal vectors and source specular scalar fidelity change from02, with metadata derivative label.',
        'All geometry/UV/images, own bind, boot02 registration and liked clothing correctives retained.',
        'Actual engine material flattening differs from source PBR; source fidelity is not a new Garage/art highlight verdict.',
        'Root01 hood flap/mottled texture/knee/hem defects remain. Hood ownership/attachment and coherent material construction follow next.',
        'No accepted milestones or normal-player promotion.']}
(evidence/'fidelity.json').write_text(json.dumps(report, indent=2)+'\n'); print('PROTECTED_FIDELITY_RESTORED', report['GLBSHA256'], flush=True)
