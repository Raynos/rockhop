"""Replace fragmented V5 LOD body topology with a welded V6 full-body reduction.

Authored LOD contact and head meshes are retained separately by graft_lod_body.
A weld requires equal coordinates AND bone weights; loop UVs are retained.
Both measured full wrist cut contours are protected from simplification.
"""
import bpy,bmesh,json,sys,argparse,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--seams',required=True);ap.add_argument('--out',required=True);ap.add_argument('--tris',type=int,default=5950);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(Path(a.input).resolve()))
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');arm.animation_data.action=None
for tr in arm.animation_data.nla_tracks:tr.mute=True
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
body=bpy.data.objects['Street_remaster_neural_full_body'];before=len(body.data.polygons)
# Merge only geometric duplicates whose complete skin weights agree. UV values
# live per loop in BMesh, so joining positions does not erase texture seams.
bm=bmesh.new();bm.from_mesh(body.data);deform=bm.verts.layers.deform.active;seen={};target={}
def key(p):return tuple(float(v) for v in p)
for v in bm.verts:
 ws=tuple(sorted((i,float(w)) for i,w in v[deform].items() if w>1e-7))
 k=(key(v.co),ws)
 if k in seen:target[v]=seen[k]
 else:seen[k]=v
bmesh.ops.weld_verts(bm,targetmap=target);bm.to_mesh(body.data);bm.free()
seams=json.loads(Path(a.seams).read_text());positions=[]
for side in seams['seams']:
 for join in side['joins']:
  if join['join']=='body':positions.extend(pair['restPosition'] for pair in join['orderedPairs'])
# Recover exact endpoint coordinates to survive Blender's conversion ulps.
blenderPositions=[Vector((p[0],-p[2],p[1])) for p in positions]
protected=[]
for v in body.data.vertices:
 for p in blenderPositions:
  if (v.co-p).length<.00001:v.co=p;protected.append(v.index);break
assert len(protected)==81,('all81 original body endpoints',len(protected))
# Keep the endpoint ring and its immediate neighbor band at full resolution.
group=body.vertex_groups.new(name='Retain actual wrist cut contours')
for v in body.data.vertices:
 distance=min((v.co-p).length for p in blenderPositions)
 if distance<.022:group.add([v.index],1,'REPLACE')
bpy.context.view_layer.objects.active=body;bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
for old in list(body.modifiers):body.modifiers.remove(old)
mod=body.modifiers.new('Clean body phone reduction; protected wrist cycles','DECIMATE');mod.ratio=a.tris/len(body.data.polygons);mod.vertex_group=group.name;mod.vertex_group_factor=1000;mod.invert_vertex_group=True
bpy.ops.object.modifier_apply(modifier=mod.name)
print('ENDPOINT ERRORS',sorted(min((v.co-p).length for v in body.data.vertices) for p in blenderPositions)[-12:])
for p in blenderPositions:assert any((v.co-p).length<.000001 for v in body.data.vertices),('protected wrist endpoint lost',list(p))
mod=body.modifiers.new('Original nineteen bone rig','ARMATURE');mod.object=arm
# The new lower-resolution body shares the original phone texture budget.
for img in bpy.data.images:
 if img.size[0]>1024 or img.size[1]>1024:img.scale(1024,1024)
for v in body.data.vertices:
 ws=sorted([(g.group,g.weight) for g in v.groups if body.vertex_groups[g.group].name in arm.data.bones and g.weight>1e-7],key=lambda t:-t[1])[:4];s=sum(w for _,w in ws)
 for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
 for i,w in ws:body.vertex_groups[i].add([v.index],w/s,'REPLACE')
for f in body.data.polygons:f.use_smooth=True
arm.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(Path(a.out).resolve()),export_format='GLB',use_selection=True,export_yup=True,export_skins=True,export_animations=False,export_leaf_bone=False,export_influence_nb=4,export_all_influences=False,export_def_bones=False)
report={'source':a.input,'sourceSHA256':hashlib.sha256(Path(a.input).read_bytes()).hexdigest(),'trianglesBefore':before,'trianglesAfter':len(body.data.polygons),'weldedDuplicateVertices':len(target),'protectedWristBoundaryVertices':len(protected),'bodyOutsideWristChanged':True,'scopeException':'V5 LOD had no closed forearm-winding topology. Parent authorized a clean full-derived body simplification; authored LOD palms/fingers/shoes/head remain exact in separate source meshes.','skinAwareWeld':True,'loopUVsPreserved':True,'textureMaxPixels':1024}
Path(a.out).with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
