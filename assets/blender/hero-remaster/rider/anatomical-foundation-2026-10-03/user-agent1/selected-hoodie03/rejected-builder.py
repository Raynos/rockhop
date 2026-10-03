"""Register selected-source shape to the own-bind body and construct a wearer cavity.

Native rest geometry is fixed. This unrigged construction candidate must pass
source fit/topology checks before independent rig/game tests; no player promotion.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for name in ['source','out','evidence']:ap.add_argument('--'+name,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,out,evidence=[Path(getattr(a,n)).resolve() for n in ['source','out','evidence']]
out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True)
assert not (out/'construction.blend').exists(),'Frozen candidate exists'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source_sha=sha(source);assert source_sha=='b644e21722cc71f51713fd12c5122702d4d527d10bd118fc7088a5f854b2a643'
bpy.ops.wm.open_mainfile(filepath=str(source))
body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];rig=bpy.data.objects['Independent anatomical foundation rig']
original=bpy.data.objects['Selected hoodie reconstructed surface, openings and fit pending']
garment=original.copy();garment.data=original.data.copy();bpy.context.collection.objects.link(garment)
garment.name='Selected Hunyuan wearable construction, unrigged and unaccepted'
original.hide_render=True;original.hide_set(True)
garment.parent=body.parent;garment.matrix_parent_inverse=body.matrix_parent_inverse.copy()
garment.matrix_basis=body.matrix_basis.copy();garment.hide_set(False);garment.hide_render=False
bm=bmesh.new();bm.from_mesh(garment.data)
holes=[];boundary={e for e in bm.edges if e.is_boundary}
while boundary:
 edge=boundary.pop();found={edge};stack=[edge]
 while stack:
  e=stack.pop()
  for v in e.verts:
   for neighbor in v.link_edges:
    if neighbor in boundary:boundary.remove(neighbor);found.add(neighbor);stack.append(neighbor)
 assert len(found)==3,'Only the frozen eight triangular remesh defects may be capped'
 holes.append({'edges':len(found),'positionsDisplayDonorUnits':[list(v.co) for v in {v for e in found for v in e.verts}]})
 bmesh.ops.holes_fill(bm,edges=list(found),sides=3)
assert len(holes)==8
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(garment.data);bm.free();garment.data.update()
donorcoords=np.array([list(v.co) for v in garment.data.vertices],dtype=np.float64)
# Frame: imported donor (X,-Z,Y) -> anatomical (forward,-left,up).
# Torso anchors are explicit construction choices, not measured source units.
height=.4722222222222222;depth=.50;lateral=.52;up=1.2266666666666666
torso_matrix=np.array([[0,-depth,0,0],[lateral,0,0,.007],[0,0,height,up],[0,0,0,1]],dtype=np.float64)
source_anchors={};target_anchors={}
for side,sign in [('R',1),('L',-1)]:
 source_anchors[side]=np.array([[sign*.43,-.015,.55],[sign*.68,-.085,.11],[sign*.94,-.10,-.265]])
 target_anchors[side]=np.array([list(rig.data.bones['upperArm.'+side].head_local),list(rig.data.bones['upperArm.'+side].tail_local),list(rig.data.bones['forearm.'+side].tail_local)])
def register(p):
 torso=(torso_matrix@np.r_[p,1])[:3];side='R' if p[0]>=0 else 'L';s=source_anchors[side];t=target_anchors[side]
 choices=[]
 for seg in [0,1]:
  axis=s[seg+1]-s[seg];u=np.clip(np.dot(p-s[seg],axis)/np.dot(axis,axis),0,1);center=s[seg]+u*axis
  choices.append((np.linalg.norm(p-center),seg,u,center))
 _,seg,u,center=min(choices,key=lambda r:r[0]);a=Vector(s[seg+1]-s[seg]);b=Vector(t[seg+1]-t[seg])
 rotation=np.array(a.rotation_difference(b).to_matrix(),dtype=np.float64)
 arm=t[seg]+u*(t[seg+1]-t[seg])+rotation@(p-center)*.50
 # Smooth seam blend only inside the proximal shoulder; the long sleeve follows
 # the two explicit body segments rather than global stretching toward a hand.
 distance=(abs(p[0])-.36)+max(.46-p[2],0)*.22
 alpha=float(np.clip(distance/.15,0,1));alpha=alpha*alpha*(3-2*alpha)
 return (1-alpha)*torso+alpha*arm,side,seg,float(u),alpha
lineage=[]
for i,(v,p) in enumerate(zip(garment.data.vertices,donorcoords)):
 position,side,seg,u,alpha=register(p);v.co=position
 lineage.append({'vertex':i,'donorDisplayXYZ':p.tolist(),'nativeRestM':position.tolist(),
  'armSide':side,'nearestSourceSegment':seg,'segmentFraction':u,'armBlend':alpha})
garment.data.update()
attr=garment.data.attributes.new('donor_display_xyz',type='FLOAT_VECTOR',domain='POINT')
for item,p in zip(attr.data,donorcoords):item.vector=p
# Cap-patch UVs are explicitly inherited from their boundary's existing local
# atlas, with the original PBR image bytes unchanged. Future art review owns any
# seam/miss rejection; do not claim these patches reproduce missing donor detail.
bm=bmesh.new();bm.from_mesh(garment.data);uv=bm.loops.layers.uv.active
for face in bm.faces:
 if len(face.verts)==3 and all(tuple(loop[uv].uv)==(0.,0.) for loop in face.loops):
  for loop in face.loops:
   candidates=[other[uv].uv.copy() for other in loop.vert.link_loops if other.face!=face and other[uv].uv.length>0]
   if candidates:loop[uv].uv=candidates[0]
bm.to_mesh(garment.data);bm.free();garment.data.update()
# Build the cavity from a NEW outward-offset copy of actual native-rest body.
# No collider/body/rig source changes, no independent generated anatomy.
cutter=bpy.data.objects.new('Canonical wearer cavity cutter, derivative only',body.data.copy());bpy.context.collection.objects.link(cutter)
cutter.parent=body.parent;cutter.matrix_parent_inverse=body.matrix_parent_inverse.copy();cutter.matrix_basis=body.matrix_basis.copy()
for v,n in zip(cutter.data.vertices,cutter.data.vertex_normals):v.co+=n.vector*.003
cutter.data.update()
lining=bpy.data.materials.new('Selected donor derived inner cotton lining, uniform prototype');lining.use_nodes=True
shader=lining.node_tree.nodes.get('Principled BSDF')
image=next(n.image for n in garment.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image and 'base-color' in n.image.name)
pixels=np.empty(len(image.pixels),dtype=np.float32);image.pixels.foreach_get(pixels);pixels=pixels.reshape(-1,4)
eligible=pixels[np.max(pixels[:,:3],axis=1)>.08,:3];mean=eligible.mean(0)
shader.inputs['Base Color'].default_value=(*[float(x*.72) for x in mean],1)
shader.inputs['Roughness'].default_value=.9;shader.inputs['Metallic'].default_value=0
cutter.data.materials.clear();cutter.data.materials.append(lining)
for o in bpy.data.objects:o.select_set(False)
garment.select_set(True);bpy.context.view_layer.objects.active=garment
boolean=garment.modifiers.new('Actual 3mm body-derived wearer cavity and openings','BOOLEAN');boolean.operation='DIFFERENCE';boolean.solver='EXACT';boolean.object=cutter
if hasattr(boolean,'material_mode'):boolean.material_mode='TRANSFER'
print('CAVITY_BOOLEAN_START',flush=True);bpy.ops.object.modifier_apply(modifier=boolean.name)
cutter.hide_render=True;cutter.hide_set(True)
garment.data.calc_loop_triangles();body.data.calc_loop_triangles()
gp=[v.co.copy() for v in garment.data.vertices];bp=[v.co.copy() for v in body.data.vertices]
gf=[tuple(t.vertices) for t in garment.data.loop_triangles];bf=[tuple(t.vertices) for t in body.data.loop_triangles]
gt=BVHTree.FromPolygons(gp,gf,all_triangles=True);bt=BVHTree.FromPolygons(bp,bf,all_triangles=True)
contacts=gt.overlap(bt);selfpairs=[(i,j) for i,j in gt.overlap(gt) if i<j and not set(gf[i])&set(gf[j])]
coverage=[]
for v,n in zip(body.data.vertices,body.data.vertex_normals):
 weights={body.vertex_groups[g.group].name:g.weight for g in v.groups}
 arm=sum(w for name,w in weights.items() if name.startswith(('upperArm.','forearm.')))
 torso=sum(weights.get(name,0) for name in ['spine','chest','pelvis'])
 if (arm>.8 or torso>.8) and v.co.z>1.04:
  point,normal,tri,distance=gt.ray_cast(v.co+n.vector*1e-6,n.vector,.20)
  coverage.append({'bodyVertex':v.index,'hit':point is not None,'distanceM':float(distance) if point is not None else None})
bm=bmesh.new();bm.from_mesh(garment.data);topology={'vertices':len(bm.verts),'polygons':len(bm.faces),'triangles':len(gf),
 'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges)};bm.free()
garment['accepted']=False;garment['constructionStage']='Registered native-rest/cavity prototype; weight/collision/game/art acceptance pending'
for o in bpy.data.objects:
 if o.name.startswith('Separate fitted sweatshirt') or o.name.startswith('Sewn'):o.hide_render=True
bpy.ops.wm.save_as_mainfile(filepath=str(out/'construction.blend'),compress=True)
assert sha(source)==source_sha
np.savez_compressed(out/'registration.npz',donorXYZ=donorcoords,nativeRestXYZ=np.array([r['nativeRestM'] for r in lineage]),
 bodyVertices=np.array(bp),bodyTriangles=np.array(bf))
report={'status':'UNACCEPTED physical native-rest garment construction; mechanical preflight only',
 'sourceSHA256':source_sha,'candidateSHA256':sha(out/'construction.blend'),'recipeSHA256':sha(__file__),
 'registrationSHA256':sha(out/'registration.npz'),'sourceDonorSHA256':'800d7a9717757b90b296a78c605cddb698c68d399a96e403aa381103e77d2eba',
 'repairedTriangularRemeshHoles':holes,'torsoDonorDisplayToNativeRestRows':torso_matrix.tolist(),
 'armSourceDisplayAnchors':{k:v.tolist() for k,v in source_anchors.items()},'armNativeRestAnchors':{k:v.tolist() for k,v in target_anchors.items()},
 'axes':'Stored native rest metres +Xforward/+Zup/-Yleft; parent/body frame keeps file+.65X once; no additional runtime offset baked',
 'pose':'Original51bind native rest; unrigged static garment, all original body/head/rig controls retained',
 'cavity':'Exact Boolean difference using actual canonical native-rest body derivative offset3mm along body vertex normals; not an unused collision descriptor',
 'innerLining':{'sourceEligibleBakedLinearBaseMean':mean.tolist(),'factor':.72,'roughness':.9,'metallic':0,'status':'Uniform derived lining prototype; no texture-detail acceptance'},
 'topology':topology,'bodyTrianglePairs':len(contacts),'nonAdjacentSelfTrianglePairs':len(selfpairs),
 'coverageRays':coverage,'coverageMisses':sum(not r['hit'] for r in coverage),
 'limits':['Body Boolean can remove exterior fabric where registration fails; body intersection0 alone is not coverage or wearable acceptance.',
 'Outward-offset cavity is static construction, not a live collision response or arbitrary-pose guarantee.',
 'Added inner lining/Boolean topology/opening semantics/UV patches require inspection; triangle benchmark is not mobile approval.',
 'Independent source fit/topology checks, rig weights, actual supported game poses and root played art review still required. No player promotion.']}
(evidence/'construction.json').write_text(json.dumps(report,indent=2)+'\n')
print('SELECTED_WEARABLE_CONSTRUCTION',json.dumps(topology),len(contacts),len(selfpairs),report['coverageMisses'],flush=True)
