"""Author garment skin from exact sewn topology and explicit dropped-hood rig.

Own51bind/body/head remain immutable. This skin is a measured candidate,
not inherited appearance/weight acceptance or a nearest-body sweep.
"""
import argparse,collections,hashlib,heapq,json,math,sys
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Matrix
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','seed-recipe','field','out','evidence']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,seed_recipe,field_path,out,evidence=[Path(getattr(a,k.replace('-','_'))).resolve() for k in ['source','seed-recipe','field','out','evidence']]
out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True)
assert not (out/'rigged.blend').exists(),'Preserve frozen candidate'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={str(p):sha(p) for p in [source,seed_recipe,field_path]}
assert pins[str(source)]=='6ef79e38e3dc86b635977ba17a2f2f6100721715b002c4e831b8bcce90ed4e93'
bpy.ops.wm.open_mainfile(filepath=str(source))
body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];rig=bpy.data.objects['Independent anatomical foundation rig'];root=body.parent
pattern=bpy.data.objects['Separate fitted sweatshirt control, hood not constructed'];original=bpy.data.objects['Selected Hunyuan underarm fitted wearable, unrigged']
bone_names=[bone.name for bone in rig.data.bones];assert len(bone_names)==51
cage_records={}
def add_cage_weights(g,original_neck,collar,attachment,rings):
    cage=[]
    for vertex in pattern.data.vertices:
        w={pattern.vertex_groups[m.group].name:float(m.weight) for m in vertex.groups if m.weight>0 and pattern.vertex_groups[m.group].name in bone_names}
        total=sum(w.values());assert total>0,vertex.index;cage.append({n:v/total for n,v in w.items()})
    for i,old in zip(collar,original_neck):assert i==len(cage);cage.append(cage[old].copy())
    for row,ring in enumerate(rings[1:],start=1):
        mix=min(1.,row/4.)
        for col,i in enumerate(ring):
            assert i==len(cage);weights={n:(1-mix)*w for n,w in cage[attachment[col]].items()};weights['chest']=weights.get('chest',0)+mix
            cage.append({n:w for n,w in weights.items() if w>0})
    assert len(cage)==len(g.data.vertices)
    groups={n:g.vertex_groups.new(name=n) for n in bone_names}
    for i,weights in enumerate(cage):
        for n,w in weights.items():groups[n].add([i],float(w),'REPLACE')
    cage_records.update({'vertices':len(cage),'originalPatternVertices':1250,'collarInheritedVertices':len(collar),
                         'hoodRows':len(rings)-1,'hoodColumns':len(attachment),'hoodBlendRowsToChest':4,
                         'basis':'Normalized actual51deform-only original structural pattern field; exact subdivision ancestry, no nearest-body search'})
# Reconstruct only the frozen seed geometry/weight interpolation, never its
# file save or diagnosis. Source13positions remain authoritative and unchanged.
code=seed_recipe.read_text();code=code[code.index('original = np.array'):code.index('def tree(o):')]
needle="sub = garment.modifiers.new";assert code.count(needle)==1
code=code.replace(needle,'add_cage_weights(garment, original_neck, collar, attachment, rings)\n'+needle)
ns={'bpy':bpy,'bmesh':bmesh,'np':np,'collections':collections,'heapq':heapq,'math':math,'body':body,'rig':rig,'pattern':pattern,'add_cage_weights':add_cage_weights}
exec(compile(code,str(seed_recipe),'exec'),ns);replay=ns['garment']
field=np.load(field_path);replayXYZ=np.array([list(v.co) for v in replay.data.vertices]);assert np.array_equal(replayXYZ,field['seedXYZ'])
assert [list(f.vertices) for f in replay.data.polygons]==[list(f.vertices) for f in original.data.polygons]
garment=original.copy();garment.data=original.data.copy();garment.name='Selected Hunyuan authored skin wearable, unaccepted';bpy.context.collection.objects.link(garment)
groups={n:garment.vertex_groups.new(name=n) for n in bone_names};dense=np.zeros((len(garment.data.vertices),51),dtype=np.float32)
max_dropped=0.;pre_limit_max=0
for i,vertex in enumerate(replay.data.vertices):
    weights={replay.vertex_groups[m.group].name:float(m.weight) for m in vertex.groups if m.weight>1e-12};pre_limit_max=max(pre_limit_max,len(weights))
    ordered=sorted(weights.items(),key=lambda r:(-r[1],bone_names.index(r[0])));max_dropped=max(max_dropped,sum(w for n,w in ordered[8:]))
    selected=ordered[:8];total=sum(w for n,w in selected);assert total>0
    for n,w in selected:groups[n].add([i],w/total,'REPLACE')
    # Capture actual Blender Float32 memberships rather than stale elements.
    for member in garment.data.vertices[i].groups:
        name=garment.vertex_groups[member.group].name;dense[i,bone_names.index(name)]=member.weight
    assert abs(float(dense[i].sum())-1)<1e-6
scratch_mesh=replay.data;bpy.data.objects.remove(replay,do_unlink=True);bpy.data.meshes.remove(scratch_mesh)
world=garment.matrix_world.copy();garment.parent=rig;garment.matrix_parent_inverse=Matrix.Identity(4);garment.matrix_world=world
skin=garment.modifiers.new('Authored sewn garment own51bind skin','ARMATURE');skin.object=rig;skin.use_deform_preserve_volume=False
garment['rockhopRiderSkinConditioned']=1;garment['accepted']=False;garment['constructionStage']='Source13exactrest/selectedPBR with topology-authored normalized8-influence51bind skin; native continuous poses/export/engine qualification pending'
original.hide_render=True;original.hide_set(True);garment.hide_render=False;garment.hide_set(False)
assert np.array_equal(np.array([list(v.co) for v in garment.data.vertices]),np.array([list(v.co) for v in original.data.vertices]))
bpy.ops.wm.save_as_mainfile(filepath=str(out/'rigged.blend'),compress=True)
for o in bpy.data.objects:o.select_set(False)
for o in [garment,rig,root]:o.hide_set(False);o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(out/'garment-rig-raw.glb'),export_format='GLB',use_selection=True,export_yup=True,
                          export_animations=False,export_morph=False,export_extras=True,export_all_influences=True,export_influence_nb=8)
assert pins=={p:sha(p) for p in pins}
garment.data.calc_loop_triangles()
assert len(garment.data.loop_triangles)==11840
np.savez_compressed(out/'authored-skin.npz',nativeRestXYZ=np.array([list(v.co) for v in garment.data.vertices]),weights=dense,
                    boneNames=np.array(bone_names),seedXYZ=field['seedXYZ'],triangles=np.array([tuple(t.vertices) for t in garment.data.loop_triangles]))
report={'status':'UNACCEPTED topology-authored selected garment own51bind skin, native moving/export/engine pending',
        'pins':pins,'recipeSHA256':sha(__file__),'candidateSHA256':sha(out/'rigged.blend'),'rawExportSHA256':sha(out/'garment-rig-raw.glb'),
        'skinFieldSHA256':sha(out/'authored-skin.npz'),'garmentObject':garment.name,'rigObject':rig.name,
        'cage':cage_records,'subdivisionCoordinatesAndPolygonCyclesExact':True,'source13RestPositionsExact':True,
        'nativeMaximumInfluencesBeforeLimit':pre_limit_max,'nativeInfluenceLimit':8,'maximumRemovedWeightMass':max_dropped,
        'actualNativeWeightSumMaxError':float(np.max(np.abs(dense.sum(1)-1))),
        'axes':'Native source13rest metres/unchanged+.65file frame; same51bone order/parents/rest. glTF +Xforward/+Yup/+Zleft and runtime-.65 once.',
        'limits':['This is authored weight candidate, not accepted old template weights: all actual source skin/pose results must be measured.',
                  'Raw Blender export can drop sub0.0001 weights; independent actual exported-weight/parity audit and faithful derivative required before admission.',
                  'Native continuous wearing/body/self/coverage, actual game/collision, played likeness and iOS remain open. Root alone judges allM0-M5; no normal-player/Library promotion.']}
(evidence/'skin.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['nativeMaximumInfluencesBeforeLimit','maximumRemovedWeightMass','actualNativeWeightSumMaxError','candidateSHA256','rawExportSHA256']}),flush=True)
