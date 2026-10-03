"""Correct the outsole/plantar interface in a new immutable footwear successor."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
ap = argparse.ArgumentParser(description=__doc__)
for n in ['source', 'construction', 'out', 'evidence']:
    ap.add_argument('--' + n, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:]); source, construction, out, evidence = [Path(getattr(a, n)).resolve() for n in ['source', 'construction', 'out', 'evidence']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest(); pins = {str(p): sha(p) for p in [source, construction]}
out.mkdir(parents=True, exist_ok=True); evidence.mkdir(parents=True, exist_ok=True)
if (out/'rider.blend').exists():
    raise RuntimeError('Frozen outsole successor exists')
bpy.ops.wm.open_mainfile(filepath=str(source)); rig = bpy.data.objects['Independent anatomical foundation rig']; root = bpy.data.objects['Foundation file frame, game x0.65']
boots = bpy.data.objects['Complete worn boot volume on own canonical feet']; mesh = boots.data; parent = json.loads(construction.read_text()); changes = []
for foot in parent['feet']:
    start, stop = foot['soleVertexRange']; half = (stop-start)//2
    # The old upper floor is10mm below the plantar minimum. Place the sole
    # top8mm above that floor:2mm below the bare foot, leaving12mm thickness.
    target = foot['soleBottomNativeZ'] + .012
    for i in range(start+half, stop):
        old = mesh.vertices[i].co.z; mesh.vertices[i].co.z = target; changes.append({'vertexID': i, 'beforeNativeZ': old, 'afterNativeZ': target, 'side': foot['side']})
assert len(changes) == 64
mesh.update(); root['rockhopAppearanceCandidate'] = 'unaccepted appearance08 complete footwear outsole below plantar surface'
for o in bpy.data.objects:
    o.select_set(False)
for o in [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render] + [root, rig]:
    o.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.wm.save_as_mainfile(filepath=str(out/'rider.blend'), compress=True)
bpy.ops.export_scene.gltf(filepath=str(out/'rider.glb'), export_format='GLB', use_selection=True, export_yup=True,
    export_animations=False, export_attributes=True, export_extras=True, export_morph=True)
controller = json.loads((source.parent/'source-normals-controller.json').read_text())
controller.update(status='UNACCEPTED08 complete footwear, sole/body interface corrected; moving wearable and live response pending',
    candidateMasterSHA256=sha(out/'rider.blend'), candidateGLBSHA256=sha(out/'rider.glb'), parentAppearanceMasterSHA256=sha(source),
    parentAppearanceGLBSHA256=sha(source.parent/'rider-source-normals.glb'))
(out/'corrective-driver.json').write_text(json.dumps(controller, indent=2)+'\n')
assert pins == {str(p): sha(p) for p in [source, construction]}
report = {'status': 'UNACCEPTED new outsole-interface successor; rest whole-footwear verification follows', 'pins': pins,
    'recipeSHA256': sha(__file__), 'masterSHA256': sha(out/'rider.blend'), 'quantizedGLBSHA256': sha(out/'rider.glb'),
    'changes': changes, 'newSoleThicknessM': .012, 'newRestSoleTopBelowPlantarMinimumM': .002,
    'limits': ['Only64 existing outsole top vertex heights change; upper/sole topology, UV/weights/materials and protected rider source fields remain fixed.',
        'New12mm sole replaces faulty18mm slab whose top intruded4mm into the foot;07 remains immutable and rejected at rest outsole interface.',
        'No moving foot/ankle wear, collision response, art/device or player acceptance; independent rest and export checks required.']}
(evidence/'construction.json').write_text(json.dumps(report, indent=2)+'\n'); print('OUTSOLE_INTERFACE_READY', report['masterSHA256'], flush=True)
