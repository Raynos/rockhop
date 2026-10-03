"""Reconstruct selected donor exterior/PBR on sewn topology with real openings.

The structural pattern is only a cage. New garment silhouette, hood and texture
correspondences use the selected generated donor; static fitting is not collision.
"""
import argparse,hashlib,json,sys,math
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for name in ['source','registration-recipe','out','evidence']:ap.add_argument('--'+name,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,registration_recipe,out,evidence=[Path(getattr(a,n.replace('-','_'))).resolve() for n in ['source','registration-recipe','out','evidence']]
out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True)
assert not (out/'sewn.blend').exists(),'Frozen candidate exists'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
pins={str(p):sha(p) for p in [source,registration_recipe]}
assert pins[str(source)]=='b644e21722cc71f51713fd12c5122702d4d527d10bd118fc7088a5f854b2a643'
bpy.ops.wm.open_mainfile(filepath=str(source))
body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];rig=bpy.data.objects['Independent anatomical foundation rig']
pattern=bpy.data.objects['Separate fitted sweatshirt control, hood not constructed']
high=bpy.data.objects['Exact selected Hunyuan high-poly PBR donor, display frame only']
# Execute only the frozen pure registration definitions, never its rejected
# mesh mutation/Boolean construction. Dependency SHA is part of this recipe.
definition=registration_recipe.read_text();definition=definition[definition.index('height=.472'):definition.index('lineage=[]')]
exec(compile(definition,str(registration_recipe),'exec'))
high.data.calc_loop_triangles();donortri=[tuple(t.vertices) for t in high.data.loop_triangles]
donorXYZ=np.array([list(v.co) for v in high.data.vertices],dtype=np.float64)
registered=[]
print('REGISTER_SELECTED_HIGH_POLY',len(donorXYZ),flush=True)
for p in donorXYZ:registered.append(register(p)[0])
registered=np.array(registered)
dt=BVHTree.FromPolygons([Vector(p) for p in registered],donortri,all_triangles=True)
body.data.calc_loop_triangles();bodytri=[tuple(t.vertices) for t in body.data.loop_triangles]
bp=[v.co.copy() for v in body.data.vertices];bt=BVHTree.FromPolygons(bp,bodytri,all_triangles=True)
vertices=[list(v.co) for v in pattern.data.vertices];faces=[list(f.vertices) for f in pattern.data.polygons]
assert len(vertices)==1250 and len(faces)==1204
edge_count={}
for face in faces:
 for i,j in zip(face,face[1:]+face[:1]):e=tuple(sorted((i,j)));edge_count[e]=edge_count.get(e,0)+1
neck_edges=[e for e,c in edge_count.items() if c==1 and min(vertices[i][2] for i in e)>1.5]
neck=list({i for e in neck_edges for i in e});assert len(neck)==20
center=np.array([vertices[i] for i in neck]).mean(0)
neck.sort(key=lambda i:math.atan2(vertices[i][1]-center[1],vertices[i][0]-center[0]))
rings=[neck]
# The new hood is a full 20-column sewn pattern, not the rejected90v flat lip.
# Its actual donor-sized mouth/back profile is then sampled against high-poly
# selected geometry. Ring0 shares every real neckline vertex; no neck cap.
for row in range(1,13):
 t=row/12;ring=[]
 for old in neck:
  p=np.array(vertices[old]);theta=math.atan2(p[1]-center[1],p[0]-center[0])
  mouth=np.array([-.03+.10*math.cos(theta),.13*math.sin(theta),1.56-.035*math.cos(theta)])
  q=(1-t)*p+t*mouth;q[0]-=.025*math.sin(math.pi*t)
  ring.append(len(vertices));vertices.append(q.tolist())
 rings.append(ring)
for row in range(12):
 for col in range(20):faces.append([rings[row][col],rings[row+1][col],rings[row+1][(col+1)%20],rings[row][(col+1)%20]])
mesh=bpy.data.meshes.new('Clean sewn selected-donor hoodie exterior');mesh.from_pydata(vertices,[],faces);mesh.update()
garment=bpy.data.objects.new('Selected Hunyuan sewn wearable, unrigged construction',mesh);bpy.context.collection.objects.link(garment)
garment.parent=body.parent;garment.matrix_parent_inverse=body.matrix_parent_inverse.copy();garment.matrix_basis=body.matrix_basis.copy()
for o in bpy.data.objects:o.select_set(False)
garment.select_set(True);bpy.context.view_layer.objects.active=garment
modifier=garment.modifiers.new('One sewn pattern refinement before donor reconstruction','SUBSURF');modifier.levels=1;modifier.render_levels=1
bpy.ops.object.modifier_apply(modifier=modifier.name)
bm=bmesh.new();bm.from_mesh(garment.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(garment.data);bm.free();garment.data.update()
seedcoords=[v.co.copy() for v in garment.data.vertices];seednormals=[n.vector.copy() for n in garment.data.vertex_normals]
lineage=[];unmapped=[];maximum_fit_adjustment=0
print('RECONSTRUCT_DONOR_EXTERIOR',len(seedcoords),flush=True)
for i,(v,p,n) in enumerate(zip(garment.data.vertices,seedcoords,seednormals)):
 # Search the donor exterior along the cage's own fabric normal. Choose the
 # farthest bounded crossing to avoid copying its internal/generated plate.
 origin=p-n*.045;hits=[];travel=0.
 for step in range(12):
  q,normal,tri,distance=dt.ray_cast(origin,n,.16-travel)
  if q is None:break
  travel+=float(distance);hits.append((q.copy(),tri));origin=q+n*1e-5;travel+=1e-5
  if travel>=.16:break
 if hits:q,tri=hits[-1];mode='bounded outermost donor normal-ray crossing'
 else:q,normal,tri,distance=dt.find_nearest(p);mode='nearest donor fallback';unmapped.append(i)
 raw=q.copy();bodypoint,bodynormal,bodyid,gap=bt.find_nearest(q)
 signed=float((q-bodypoint).dot(bodynormal))
 if signed<.008:q=bodypoint+bodynormal*.008
 adjustment=float((q-raw).length);maximum_fit_adjustment=max(maximum_fit_adjustment,adjustment)
 v.co=q
 ids=donortri[tri];pts=registered[list(ids)]
 # Texture lineage follows the exact selected triangle, independently of the
 # measured body-facing fitting adjustment. No stale shirt texture is reused.
 matrix=np.column_stack([pts[1]-pts[0],pts[2]-pts[0]])
 yz=np.linalg.lstsq(matrix,np.array(raw)-pts[0],rcond=None)[0];bary=np.clip([1-sum(yz),yz[0],yz[1]],0,1);bary/=sum(bary)
 donorpoint=bary@donorXYZ[list(ids)]
 lineage.append({'vertex':i,'sourceTriangle':int(tri),'sourceVertices':list(ids),'barycentric':bary.tolist(),
  'donorDisplayXYZ':donorpoint.tolist(),'nativeRestM':list(q),'mode':mode,'fitAdjustmentM':adjustment})
garment.data.update();finalcoords=[v.co.copy() for v in garment.data.vertices]
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1519173,island_margin=.018,area_weight=.25);bpy.ops.object.mode_set(mode='OBJECT')
# Bake in original donor coordinates to the new sewn UV atlas, then restore
# native physical coordinates. Exact source shader/image bytes are untouched.
for v,row in zip(garment.data.vertices,lineage):v.co=row['donorDisplayXYZ']
garment.data.update()
savedbasis=garment.matrix_basis.copy();savedparent=garment.parent;garment.parent=None;garment.matrix_world.identity()
material=bpy.data.materials.new('Selected high-poly Hunyuan PBR on sewn atlas');material.use_nodes=True;garment.data.materials.append(material)
shader=material.node_tree.nodes.get('Principled BSDF');target=material.node_tree.nodes.new('ShaderNodeTexImage')
src=high.data.materials[0];nodes=src.node_tree.nodes;links=src.node_tree.links;principled=nodes.get('Principled BSDF');output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
previous=list(output.inputs['Surface'].links)[0].from_socket
for link in list(output.inputs['Surface'].links):links.remove(link)
emission=nodes.new('ShaderNodeEmission');links.new(emission.outputs[0],output.inputs['Surface'])
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=1;scene.cycles.device='CPU';scene.render.bake.use_selected_to_active=True;scene.render.bake.cage_extrusion=.02;scene.render.bake.max_ray_distance=.06;scene.render.bake.margin=12
high.hide_render=False;high.hide_set(False)
for o in bpy.data.objects:o.select_set(False)
high.select_set(True);garment.select_set(True);bpy.context.view_layer.objects.active=garment
textures={}
for label,socket,data in [('base-color','Base Color',False),('roughness','Roughness',True),('metallic','Metallic',True)]:
 image=bpy.data.images.new('Sewn selected donor '+label,width=2048,height=2048,alpha=False,is_data=data);target.image=image;material.node_tree.nodes.active=target
 for link in list(emission.inputs[0].links):links.remove(link)
 value=principled.inputs[socket]
 if value.links:links.new(value.links[0].from_socket,emission.inputs[0])
 else:emission.inputs[0].default_value=(value.default_value,)*3+(1,) if data else value.default_value
 print('BAKE_SELECTED_SEWN',label,flush=True);bpy.ops.object.bake(type='EMIT')
 path=out/(label+'.png');image.filepath_raw=str(path);image.file_format='PNG';image.save();textures[label]={'path':str(path),'SHA256':sha(path),'pixels':[2048,2048],'colorSpace':image.colorspace_settings.name}
 texture=material.node_tree.nodes.new('ShaderNodeTexImage');texture.image=image;material.node_tree.links.new(texture.outputs[0],shader.inputs[socket])
links.new(previous,output.inputs['Surface']);nodes.remove(emission);high.hide_render=True;high.hide_set(True)
garment.parent=savedparent;garment.matrix_basis=savedbasis
for v,p in zip(garment.data.vertices,finalcoords):v.co=p
garment.data.update();garment.data.calc_loop_triangles()
for f in garment.data.polygons:f.use_smooth=True
gp=[v.co.copy() for v in garment.data.vertices];gf=[tuple(t.vertices) for t in garment.data.loop_triangles]
gt=BVHTree.FromPolygons(gp,gf,all_triangles=True);contacts=gt.overlap(bt);selfpairs=[(i,j) for i,j in gt.overlap(gt) if i<j and not set(gf[i])&set(gf[j])]
bm=bmesh.new();bm.from_mesh(garment.data);bm.verts.ensure_lookup_table();bm.verts.index_update();boundary={e for e in bm.edges if e.is_boundary};openings=[]
while boundary:
 e=boundary.pop();found={e};stack=[e]
 while stack:
  edge=stack.pop()
  for v in edge.verts:
   for other in v.link_edges:
    if other in boundary:boundary.remove(other);found.add(other);stack.append(other)
 ids={v.index for e in found for v in e.verts};p=np.array([list(bm.verts[i].co) for i in ids])
 openings.append({'vertices':sorted(ids),'edges':len(found),'centroidNativeM':p.mean(0).tolist(),'boundsNativeM':[p.min(0).tolist(),p.max(0).tolist()]})
nonboundary=sum(not e.is_manifold and not e.is_boundary for e in bm.edges);bm.free()
for o in bpy.data.objects:
 if o.name in ['Sewn clean hoodie with dropped hood','Separate fitted sweatshirt control, hood not constructed','Protected mustard hood on own rig','Selected hoodie reconstructed surface, openings and fit pending']:o.hide_render=True
garment['accepted']=False;garment['constructionStage']='Selected donor exterior/PBR on clean sewn topology; static fit/self/opening preflight and rig/game/visual acceptance pending'
bpy.ops.wm.save_as_mainfile(filepath=str(out/'sewn.blend'),compress=True)
assert pins=={p:sha(p) for p in pins}
np.savez_compressed(out/'source-correspondence.npz',donorXYZ=np.array([r['donorDisplayXYZ'] for r in lineage]),nativeRestXYZ=np.array(gp),triangles=np.array(gf),sourceTriangle=np.array([r['sourceTriangle'] for r in lineage]),barycentric=np.array([r['barycentric'] for r in lineage]))
report={'status':'UNACCEPTED selected-donor sewn exterior/PBR candidate; preflight determines failures',
 'pins':pins,'recipeSHA256':sha(__file__),'candidateSHA256':sha(out/'sewn.blend'),'correspondenceSHA256':sha(out/'source-correspondence.npz'),
 'sourceDonorSHA256':'800d7a9717757b90b296a78c605cddb698c68d399a96e403aa381103e77d2eba',
 'structuralCage':{'source':pattern.name,'vertices':1250,'polygons':1204,'hoodNew20ColumnRings':12,'subdivisionLevels':1,'purpose':'Topology only; actual selected-donor shape/PBR reconstructed, no old plain-shirt appearance'},
 'vertices':len(gp),'triangles':len(gf),'realBoundaryComponents':openings,'nonBoundaryNonManifoldEdges':nonboundary,
 'bodyTrianglePairs':len(contacts),'nonAdjacentSelfTrianglePairs':len(selfpairs),'nearestDonorFallbackVertices':unmapped,
 'maximumBodyFacingStaticFitAdjustmentM':maximum_fit_adjustment,'textures':textures,
 'axes':'Native rest metres +Xforward/+Zup/-Yleft; original body parent/file+.65 retained once; bake temporarily in exact donor display XYZ then restored',
 'limits':['Bounded donor rays/nearest fallback/8mm body-facing construction are static fitting, not a live collision correction.',
 'All source correspondence/adjustments and failures explicit; clean boundary count/triangle benchmark alone accepts neither fit nor appearance.',
 'New sewn hood mouth and donor silhouette/PBR need moving review; original body/head51bind unchanged, garment unrigged for independent skin/game qualification.',
 'No Boolean sweep, plain-shirt appearance substitute, full-body cloth default, Library duplicate or player promotion. Root alone judges M0–M5.']}
(evidence/'construction.json').write_text(json.dumps(report,indent=2)+'\n')
print('SEWN_SELECTED_DONOR',len(gp),len(gf),len(contacts),len(selfpairs),len(openings),len(unmapped),flush=True)
