"""Construct a frozen selected-donor retopology/PBR scaffold before fitting.

This is surface reconstruction, not a fitted/rigged garment qualification.
Keep the exact generated donor and canonical body/master untouched.
"""
import argparse,hashlib,json,sys,time
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree

ap=argparse.ArgumentParser(description=__doc__)
for name in ['donor','body','out','evidence']:ap.add_argument('--'+name,required=True)
ap.add_argument('--faces',type=int,default=6000)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
donor,bodyfile,out,evidence=[Path(getattr(a,n)).resolve() for n in ['donor','body','out','evidence']]
out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True)
assert not (out/'surface.blend').exists(),'Frozen output exists'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
pins={str(p):sha(p) for p in [donor,bodyfile]}
assert pins[str(donor)]=='800d7a9717757b90b296a78c605cddb698c68d399a96e403aa381103e77d2eba'
assert pins[str(bodyfile)]=='61bef706b9c9919c80ec671d229893a42440c6902785ebc572716f6840430421'
bpy.ops.wm.open_mainfile(filepath=str(bodyfile))
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(donor))
high=next(o for o in set(bpy.data.objects)-before if o.type=='MESH')
high.name='Exact selected Hunyuan high-poly PBR donor, display frame only'
high.hide_render=True
surface=high.copy();surface.data=high.data.copy();bpy.context.collection.objects.link(surface)
surface.name='Selected hoodie reconstructed surface, openings and fit pending'
surface.hide_render=False
for o in bpy.context.selected_objects:o.select_set(False)
surface.select_set(True);bpy.context.view_layer.objects.active=surface
# Work in imported display coordinates (X,-Z,Y), uncalibrated donor units.
# Weld UV-split duplicates only on the derivative; untouched donor supplies bake UVs.
bm=bmesh.new();bm.from_mesh(surface.data)
before_cleanup={'vertices':len(bm.verts),'faces':len(bm.faces)}
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
unused=set(bm.verts);components=[]
while unused:
 seed=unused.pop();found={seed};stack=[seed]
 while stack:
  v=stack.pop()
  for edge in v.link_edges:
   other=edge.other_vert(v)
   if other in unused:unused.remove(other);found.add(other);stack.append(other)
 components.append(found)
components.sort(key=len,reverse=True)
removed=[{'vertices':len(c),'faces':len({f for v in c for f in v.link_faces})} for c in components[1:]]
bmesh.ops.delete(bm,geom=[v for c in components[1:] for v in c],context='VERTS')
degenerate=[f for f in bm.faces if f.calc_area()<1e-15]
if degenerate:bmesh.ops.delete(bm,geom=degenerate,context='FACES_ONLY')
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.verts.index_update();bm.edges.index_update();bm.faces.index_update()
bad_edges=[{'edge':e.index,'vertices':[v.index for v in e.verts],
 'positionsDisplayDonorUnits':[list(v.co) for v in e.verts],
 'linkedFaces':[f.index for f in e.link_faces],'boundary':e.is_boundary,'manifold':e.is_manifold}
 for e in bm.edges if not e.is_manifold]
preflight={'status':'UNACCEPTED reconstruction input; topology preflight only',
 'pins':pins,'recipeSHA256':sha(__file__),'donorGeometry':before_cleanup,
 'weldDistanceDonorUnits':1e-7,'derivativeRemovedComponents':removed,
 'derivativeRemovedDegenerateFaces':len(degenerate),'verticesAfterCleanup':len(bm.verts),
 'facesAfterCleanup':len(bm.faces),'boundaryEdges':sum(e.is_boundary for e in bm.edges),
 'nonManifoldEdges':len(bad_edges),'nonManifoldVertices':sum(not v.is_manifold for v in bm.verts),
 'nonContiguousEdges':sum(e.is_manifold and not e.is_contiguous for e in bm.edges),
 'eulerCharacteristic':len(bm.verts)-len(bm.edges)+len(bm.faces),
 'witnesses':bad_edges,'limits':['Derivative cleanup only; source donor/body unchanged.',
 'No physical registration, openings, rig, UV bake or wearable acceptance.']}
(evidence/'preflight.json').write_text(json.dumps(preflight,indent=2)+'\n')
bm.to_mesh(surface.data);bm.free()
clean_vertices=[v.co.copy() for v in surface.data.vertices]
surface.data.calc_loop_triangles();clean_triangles=[tuple(t.vertices) for t in surface.data.loop_triangles]
tree=BVHTree.FromPolygons(clean_vertices,clean_triangles,all_triangles=True)
started=time.monotonic()
print('QUADRIFLOW_START',len(clean_vertices),len(clean_triangles),a.faces,flush=True)
result=bpy.ops.object.quadriflow_remesh(target_faces=a.faces,use_mesh_symmetry=False,
 use_preserve_sharp=True,use_preserve_boundary=True,smooth_normals=True,seed=42)
if result!={'FINISHED'}:
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'rejected-input.blend'),compress=True)
 assert pins=={p:sha(p) for p in pins}
 (evidence/'rejection.json').write_text(json.dumps({'status':'REJECTED QuadriFlow input/operator consistency; cause unresolved',
  'operatorResult':sorted(result),'inputSHA256':sha(out/'rejected-input.blend'),
  'preflightSHA256':sha(evidence/'preflight.json'),'elapsedSeconds':time.monotonic()-started,
  'sourcePreserved':True,'accepted':False,'reason':'Operator reports manifold/consistent-normal requirement despite explicit BMesh checks; no output or identified root cause claimed.'},indent=2)+'\n')
assert result=={'FINISHED'},result
duration=time.monotonic()-started
preprojection=[];distances=[]
for v in surface.data.vertices:
 nearest,normal,index,distance=tree.find_nearest(v.co)
 assert nearest is not None
 preprojection.append(float(distance));v.co=nearest
surface.data.update();surface.data.calc_loop_triangles()
for f in surface.data.polygons:f.use_smooth=True
# New UV atlas is explicitly baked from the exact selected high-poly donor.
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.1519173,island_margin=.018,area_weight=.25)
bpy.ops.object.mode_set(mode='OBJECT')
source_material=high.data.materials[0]
surface.data.materials.clear()
material=bpy.data.materials.new('Selected Hunyuan mustard PBR, reconstructed UV bake')
material.use_nodes=True;surface.data.materials.append(material)
shader=material.node_tree.nodes.get('Principled BSDF');target_node=material.node_tree.nodes.new('ShaderNodeTexImage')
nodes=source_material.node_tree.nodes;links=source_material.node_tree.links
principled=nodes.get('Principled BSDF');output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
emission=nodes.new('ShaderNodeEmission');old_link=list(output.inputs['Surface'].links)[0]
old_from=old_link.from_socket;links.remove(old_link);links.new(emission.outputs[0],output.inputs['Surface'])
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1;scene.cycles.device='CPU'
scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.02
scene.render.bake.max_ray_distance=.06;scene.render.bake.margin=12
high.hide_render=False;high.hide_set(False)
for o in bpy.data.objects:o.select_set(False)
high.select_set(True);surface.select_set(True);bpy.context.view_layer.objects.active=surface
material.node_tree.nodes.active=target_node
textures={}
for label,socket,data in [('base-color','Base Color',False),('roughness','Roughness',True),('metallic','Metallic',True)]:
 image=bpy.data.images.new('Selected donor baked '+label,width=2048,height=2048,alpha=False,is_data=data)
 target_node.image=image
 for link in list(emission.inputs[0].links):links.remove(link)
 source_input=principled.inputs[socket]
 if source_input.links:links.new(source_input.links[0].from_socket,emission.inputs[0])
 else:emission.inputs[0].default_value=(source_input.default_value,)*3+(1,) if data else source_input.default_value
 print('BAKE_START',label,flush=True);bpy.ops.object.bake(type='EMIT')
 path=out/(label+'.png');image.filepath_raw=str(path);image.file_format='PNG';image.save()
 textures[label]={'path':str(path),'SHA256':sha(path),'pixels':[2048,2048],'colorSpace':image.colorspace_settings.name}
 tex=material.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
 material.node_tree.links.new(tex.outputs['Color'],shader.inputs[socket])
links.new(old_from,output.inputs['Surface']);nodes.remove(emission)
high.hide_render=True;high.hide_set(True)
for o in bpy.data.objects:o.select_set(False)
surface.select_set(True);bpy.context.view_layer.objects.active=surface
# Store the display scaffold away from the body. Physical registration/openings
# are the next construction step; no guessed metre transform is claimed here.
surface.location=(3,0,1)
surface['selectedDonorSHA256']=pins[str(donor)]
surface['wearableAccepted']=False
surface['constructionStage']='Reconstructed surface/PBR; body registration/openings/inner clearance pending'
surface.data.calc_loop_triangles()
bm=bmesh.new();bm.from_mesh(surface.data)
topology={'vertices':len(bm.verts),'polygons':len(bm.faces),'triangles':len(surface.data.loop_triangles),
 'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges)}
bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(out/'surface.blend'),compress=True)
assert pins=={p:sha(p) for p in pins}
report={'status':'UNACCEPTED selected-donor reconstructed surface/PBR; not fitted or rigged',
 'pins':pins,'recipeSHA256':sha(__file__),'masterSHA256':sha(out/'surface.blend'),
 'donorGeometry':before_cleanup,'derivativeRemovedComponents':removed,'derivativeRemovedDegenerateFaces':len(degenerate),
 'surface':topology,'quadriflowTargetFaces':a.faces,'quadriflowElapsedSeconds':duration,
 'maximumReprojectionDistanceDonorUnits':max(preprojection),'textures':textures,
 'axes':'Exact glTF XYZ imports as Blender X,-Z,Y; display-only scaffold is translated3,0,1, no metre/body fitting claim',
 'limits':['New atlas/PBR is selected-to-active emission bake from exact source, no new plain-shirt texture.',
 'Openings, wearer cavity, physical units/pose registration and inner clearance are pending; triangle count is not wearable acceptance.',
 'Exact high-poly source and body/head/51bind/control sources are unchanged. Root alone judges moving evidence; no player promotion.']}
(evidence/'construction.json').write_text(json.dumps(report,indent=2)+'\n')
print('RECONSTRUCTED_SELECTED_HOODIE',json.dumps(topology),flush=True)
