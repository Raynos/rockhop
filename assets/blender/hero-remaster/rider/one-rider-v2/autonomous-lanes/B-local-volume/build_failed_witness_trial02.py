"""Freeze actual failed intrinsic-panel witness; this is not a reconstructed garment."""
import bpy,numpy as np,json,hashlib,resource
from pathlib import Path
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');RUN=R/'autonomous-lanes/B-local-volume/trial02'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
bp=R/'glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend';hp=R/'head-cleanup/mpfb-v8-palette/african/head.blend';before={str(p):sha(p) for p in [bp,hp]}
bpy.ops.wm.open_mainfile(filepath=str(bp));body=max((o for o in bpy.context.scene.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices));old=body.data;materials=list(old.materials);uvnames=[x.name for x in old.uv_layers];weights=[[(g.group,g.weight) for g in x.groups] for x in old.vertices];oldgroups=[x.name for x in body.vertex_groups]
d=np.load(RUN/'clipped-panel.npz');v=d['vertices'];f=d['faces'];uv=d['allTriangleUV'];mi=d['materialIndex'];orig=d['faceOrigin'];src=np.load(RUN/'body-source.npz');valid=orig>=0
assert np.array_equal(f[valid],src['faces'][orig[valid]]);assert np.array_equal(mi[valid],src['materialIndex'][orig[valid]]);assert np.array_equal(uv[:,valid],src['allTriangleUV'][:,orig[valid]])
mesh=bpy.data.meshes.new('FAILED THREE-CONTOUR volume preflight');mesh.from_pydata(v.tolist(),[],f.tolist());mesh.update()
for m in materials:mesh.materials.append(m)
for p,i in zip(mesh.polygons,mi):p.material_index=int(i);p.use_smooth=True
for k,name in enumerate(uvnames):
 u=mesh.uv_layers.new(name=name)
 for p,uvtri in zip(mesh.polygons,uv[k]):
  for li,uvco in zip(p.loop_indices,uvtri):u.data[li].uv=uvco
body.data=mesh;body.matrix_world.identity();body.name='UNACCEPTED B trial02 three-contour panel witness'
# Existing indexed source weights remain exact outside local panel. Intersections get linear weights.
# Blender mesh replacement cleared the object's vertex-group definitions.
# Recreate exact source group names and source-indexed weights without inventing mapping.
for name in oldgroups:body.vertex_groups.new(name=name)
for vi,ws in enumerate(weights):
 for gi,w in ws:body.vertex_groups[gi].add([vi],w,'REPLACE')
(RUN/'source-deform-raw.json').write_text(json.dumps({'sourceObjectGroupNames':oldgroups,'perVertexDeform':weights}))
# Derive split-edge positions only, no new rig or posing.
intersections={}
from mathutils.kdtree import KDTree
# No required deformation evidence: static failed witness only.
with bpy.data.libraries.load(str(hp),link=False) as (src,dst):dst.objects=list(src.objects)
heads=[]
for o in dst.objects:
 if o and o.type=='MESH':
  bpy.context.scene.collection.objects.link(o);o.scale=tuple(x*.42 for x in o.scale);o.location=o.location*.42;o.location.z+=1.59338;heads.append(o)
bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
for o in heads:o.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.wm.save_as_mainfile(filepath=str(RUN/'failed-witness.blend'))
bpy.ops.export_scene.gltf(filepath=str(RUN/'character.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=False,export_apply=False,export_texcoords=True,export_normals=True,export_materials='EXPORT')
assert before=={str(p):sha(p) for p in [bp,hp]}
report={'status':'FAILED PRE-VOLUME THREE-CONTOUR DIAGNOSTIC ONLY; no garment construction, no rig or bake','bodyMaterials':[m.name for m in body.data.materials],'bodyUVLayers':uvnames,'preservedFullTriangleCount':int(valid.sum()),'preservedFullTriangleIndexUVMaterialExact':True,'sourceRawDeformPreservedSeparately':len(weights),'sourceObjectGroupCount':len(oldgroups),'rigWeightsInWitness':'Original source-indexed vertex groups restored; new split edge weights unmeasured, failed static witness only','newSplitVertexWeights':'UNMEASURED; unrigged failed witness only','headMeshes':[o.name for o in heads],'nativeHeadScale':.42,'nativeHeadTranslation':[0,0,1.59338],'sources':before,'sourcesAfter':{str(p):sha(p) for p in [bp,hp]},'recipeSHA256':sha(__file__),'GLBSHA256':sha(RUN/'character.glb'),'peakRSSBytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(RUN/'witness-construction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
