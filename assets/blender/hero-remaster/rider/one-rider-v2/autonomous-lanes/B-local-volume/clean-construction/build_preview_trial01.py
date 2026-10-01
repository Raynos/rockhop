"""New wholehood neutral preview builder; preserve source material/UV/deform arrays."""
import bpy,numpy as np,json,hashlib,resource,math
from pathlib import Path
from mathutils import Vector,Euler
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/B-local-volume/clean-construction/trial01');cfg=json.loads((R/'settings.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();bp=Path(cfg['bodySource']);hp=Path(cfg['sizingSkinSource']);before={str(p):sha(p) for p in [bp,hp]}
bpy.ops.wm.open_mainfile(filepath=str(bp));body=max((o for o in bpy.context.scene.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices));old=body.data;mats=list(old.materials);uvnames=[u.name for u in old.uv_layers];weights=[[(g.group,g.weight) for g in x.groups] for x in old.vertices];groups=[g.name for g in body.vertex_groups];d=np.load(R/'new-wholehood.npz');src=np.load(R/'body-source.npz');v=d['vertices'];f=d['faces'];uv=d['allTriangleUV'];mi=d['materialIndex'];orig=d['faceOrigin'];valid=orig>=0
assert np.array_equal(f[valid],src['faces'][orig[valid]]);assert np.array_equal(uv[:,valid],src['allTriangleUV'][:,orig[valid]]);assert np.array_equal(mi[valid],src['materialIndex'][orig[valid]])
mesh=bpy.data.meshes.new('NEW wholehood four-panel neutral form');mesh.from_pydata(v.tolist(),[],f.tolist());mesh.update()
for m in mats:mesh.materials.append(m)
for name in ['NEW outer textile LEFT','NEW outer textile RIGHT','NEW lining textile LEFT','NEW lining textile RIGHT','NEW sewn rolled neck binding']:
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.42,.42,.42,1);p.inputs['Roughness'].default_value=.75;p.inputs['Metallic'].default_value=0;mesh.materials.append(m)
for p,k in zip(mesh.polygons,mi):p.material_index=int(k);p.use_smooth=True
for k,name in enumerate(uvnames):
 u=mesh.uv_layers.new(name=name)
 for p,triuv in zip(mesh.polygons,uv[k]):
  for li,co in zip(p.loop_indices,triuv):u.data[li].uv=co
u=mesh.uv_layers.new(name='CleanHoodPatternUV')
for p,triuv in zip(mesh.polygons,d['patternUV']):
 for li,co in zip(p.loop_indices,triuv):u.data[li].uv=co
body.data=mesh;body.matrix_world.identity();body.name='UNACCEPTED NEW complete four-panel hood neutral form'
for name in groups:body.vertex_groups.new(name=name)
for vi,ws in enumerate(weights):
 for gi,w in ws:body.vertex_groups[gi].add([vi],w,'REPLACE')
for svi,(a,b,t) in json.loads((R/'interpolated-source-weights.json').read_text()).items():
 wa=dict(weights[a]);wb=dict(weights[b]);vi=int(svi)
 for gi in set(wa)|set(wb):body.vertex_groups[gi].add([vi],wa.get(gi,0)*(1-t)+wb.get(gi,0)*t,'REPLACE')
# New garment has no invented weights. Parent's explicit 19-bone adapter remains pending.
with bpy.data.libraries.load(str(hp),link=False) as (sr,ds):ds.objects=list(sr.objects)
heads=[];adapter=cfg['skinAdapter']
for o in ds.objects:
 if o and o.type=='MESH':
  bpy.context.scene.collection.objects.link(o);o.scale=tuple(x*adapter['scale'] for x in o.scale);o.location=o.location*adapter['scale']+Vector(adapter['translation']);o.rotation_euler=Euler(tuple(math.radians(x) for x in adapter['rotationDegrees']),'XYZ');o.name='SIZING CONTROL ONLY '+o.name;heads.append(o)
bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
for o in heads:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.wm.save_as_mainfile(filepath=str(R/'new-wholehood-neutral-master.blend'));bpy.ops.export_scene.gltf(filepath=str(R/'geometry-preview.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=False,export_apply=False,export_texcoords=True,export_normals=True,export_materials='EXPORT')
assert before=={str(p):sha(p) for p in [bp,hp]};report={'status':'UNACCEPTED neutral geometry only; native size control not final WHITEidentity; no new material bake or rig approval','sourceSHA':before,'sourceSHAAfter':{str(p):sha(p) for p in [bp,hp]},'protectedTriangleUVMaterialExact':int(valid.sum()),'sourceOriginalMaterialSlots':[m.name for m in mats],'newMaterialSlots':[m.name for m in mesh.materials][2:],'UVLayers':[u.name for u in mesh.uv_layers],'sourceDeformNamesRestored':len(groups),'originalSourceWeightsRestored':len(weights),'interpolatedEdgeWeightsRestored':len(json.loads((R/'interpolated-source-weights.json').read_text())),'newGarmentWeights':'UNASSIGNED until explicit rig adaptation, staticonly','headAdapter':adapter,'finalSkinColor':'WHITE per human, fresh H21 source separately reviewed by parent; preview sizing control only','GLBSHA':sha(R/'geometry-preview.glb'),'recipeSHA':sha(__file__),'peakRSSBytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(R/'build-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
