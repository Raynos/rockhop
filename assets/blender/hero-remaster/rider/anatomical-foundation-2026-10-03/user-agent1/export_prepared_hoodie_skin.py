"""Export the exact prepared native after correcting an exporter option name."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,numpy as np
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','builder','out','evidence']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,builder,out,evidence=[Path(getattr(a,k)).resolve() for k in ['source','builder','out','evidence']]
out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,builder]}
assert pins[str(source)]=='d3f05ff00755c0fb9e4245465092333ace538098e86eb44e4ad057e4c68d8996'
assert not (out/'garment-rig-raw.glb').exists(),'Preserve frozen raw export'
bpy.ops.wm.open_mainfile(filepath=str(source));g=bpy.data.objects['Selected Hunyuan authored skin wearable, unaccepted'];rig=bpy.data.objects['Independent anatomical foundation rig']
body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];root=body.parent
names=[b.name for b in rig.data.bones];assert len(names)==51
weights=np.zeros((len(g.data.vertices),51),dtype=np.float32)
for vertex in g.data.vertices:
    for member in vertex.groups:
        name=g.vertex_groups[member.group].name;assert name in names;weights[vertex.index,names.index(name)]=member.weight
assert np.max(np.abs(weights.sum(1)-1))<1e-6 and np.max((weights>0).sum(1))<=8
assert g.parent==rig and any(m.type=='ARMATURE' and m.object==rig for m in g.modifiers)
for o in bpy.data.objects:o.select_set(False)
for o in [g,rig,root]:o.hide_set(False);o.select_set(True)
bpy.context.view_layer.objects.active=rig
properties=bpy.ops.export_scene.gltf.get_rna_type().properties
assert 'export_all_influences' in properties and 'export_influence_nb' in properties
bpy.ops.export_scene.gltf(filepath=str(out/'garment-rig-raw.glb'),export_format='GLB',use_selection=True,export_yup=True,
                          export_animations=False,export_morph=False,export_extras=True,export_all_influences=True,export_influence_nb=8)
g.data.calc_loop_triangles();assert len(g.data.loop_triangles)==11840
np.savez_compressed(out/'authored-skin.npz',nativeRestXYZ=np.array([list(v.co) for v in g.data.vertices]),weights=weights,
                    boneNames=np.array(names),triangles=np.array([tuple(t.vertices) for t in g.data.loop_triangles]))
assert pins=={p:sha(p) for p in pins}
report={'status':'UNACCEPTED preserved native garment skin exported with installed correct option; moving/parity/game pending',
        'pins':pins,'recipeSHA256':sha(__file__),'candidateSHA256':pins[str(source)],'rawExportSHA256':sha(out/'garment-rig-raw.glb'),'skinFieldSHA256':sha(out/'authored-skin.npz'),
        'nativeVertices':len(weights),'triangles':11840,'actualNativeMaximumInfluences':int((weights>0).sum(1).max()),'actualWeightSumMaxError':float(np.abs(weights.sum(1)-1).max()),
        'authoring':'Original1250pattern51deform-only field normalized and interpolated through exact sewn subdivision; collar inherits neckline, dropped hood blends attachment to chest across4rows; own8influence limit, source13rest/PBR immutable',
        'exportRepair':'First export used internal setting key export_all_vertex_influences; installed public operator is export_all_influences/export_influence_nb. Frozen prepared native untouched; failed builder retained.',
        'installedPrimarySource':'/Applications/Blender.app/Contents/Resources/5.2/scripts/addons_core/io_scene_gltf2/__init__.py:933',
        'limits':['Authored skin remains candidate: raw export cutoff/restbind/nativecontinuousposes/actual engine must be independently measured.',
                  'No frozen source13 geometry/PBR/head/body/51bind/control rewrite, Library duplicate or normal-player promotion. Root alone judges allM0-M5.']}
(evidence/'skin.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['actualNativeMaximumInfluences','actualWeightSumMaxError','candidateSHA256','rawExportSHA256']}),flush=True)
