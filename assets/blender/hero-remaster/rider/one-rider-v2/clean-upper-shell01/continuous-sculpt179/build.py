"""Single rounded anatomical sculpt volume -> independent voxel quad shell."""
import bpy,bmesh,numpy as np,json,hashlib,math
from pathlib import Path
from mathutils import Vector
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/continuous-sculpt179');E=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/continuous-sculpt179');M=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3/hoodie-repair02/shape-lane/volume-lane/source-embedding23/continuous-shell-source-maps.npz')
bpy.ops.wm.read_factory_settings(use_empty=True);parts=[]
def ellipsoid(name,co,scale,rotation=None):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,location=co);o=bpy.context.object;o.name=name;o.scale=scale
 if rotation is not None:o.rotation_euler=rotation
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);parts.append(o);return o
ellipsoid('New rounded anatomical torso',(.635,0,1.215),(.165,.183,.315))
# One joined volume; arms anatomy uses C19 upperArm/forearm/hand centers, not source garment strips.
for side in [-1,1]:
 shoulder=Vector((.6297,side*.208075,1.46160));elbow=Vector((.624625,side*.289275,1.141875));wrist=Vector((.67538,side*.36027,.88219))
 ellipsoid('New shoulder ease',(.63,side*.17,1.438),(.100,.105,.080))
 for label,a,b,radius in [('upper',shoulder,elbow,.074),('fore',elbow,wrist,.059)]:
  d=b-a;rot=d.to_track_quat('Z','Y').to_euler();ellipsoid('New anatomical '+label,(a+b)/2,(radius,radius,d.length/2+radius*.5),rot)
 ellipsoid('New rounded elbow',elbow,(.073,.073,.077))
 # Wrist shape aligns source-ring center before explicit final cuff boundary mapping.
 ellipsoid('New wrist',(.66855,side*.356,.929),(.054,.048,.078))
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();ob=bpy.context.object;ob.name='UNACCEPTED_UNRIGGED_CONTINUOUS_SCULPT179'
# Apply transforms so authored shell world space matches protected donor coordinates.
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
mod=ob.modifiers.new('One merged voxel sculpt envelope','REMESH');mod.mode='VOXEL';mod.voxel_size=.009;mod.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=mod.name)
sm=ob.modifiers.new('Sculpt surface relaxation','SMOOTH');sm.factor=.45;sm.iterations=3;bpy.ops.object.modifier_apply(modifier=sm.name)
# Literal cuff/hem cuts. Knife plane at hem also divides arms but preserves their complete faces.
bm=bmesh.new();bm.from_mesh(ob.data)
def cut(z,delete=None):
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=(0,0,z),plane_no=(0,0,1),clear_inner=False,clear_outer=False)
 bad=[v for v in bm.verts if v.co.z<z-1e-7 and (delete(v) if delete else True)]
 bmesh.ops.delete(bm,geom=bad,context='VERTS')
cut(.9134999513626099);cut(.95,lambda v:abs(v.co.y)<.25)
bm.to_mesh(ob.data);bm.free()
# Exact boolean neckline carving. The cutter wall/floor is removed to produce an open garment rim.
bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=1,depth=1,location=(.6297,0,1.875));c=bpy.context.object;c.scale=(.079,.069,1);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bpy.context.view_layer.objects.active=ob;mod=ob.modifiers.new('Explicit anatomical neckline knife','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=c;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(c,do_unlink=True)
bm=bmesh.new();bm.from_mesh(ob.data);bad=[]
for f in bm.faces:
 co=f.calc_center_median();rr=((co.x-.6297)/.079)**2+(co.y/.069)**2
 if rr<1.000001 and co.z>1.3749:bad.append(f)
bmesh.ops.delete(bm,geom=bad,context='FACES');bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
# Explicit cuff boundary correspondence: source alias points sorted angularly, never global proximity union.
source=np.load(M);mapping=[]
for side,label in [(-1,'L'),(1,'R')]:
 raw=source['cuffPositions'+label];src=np.column_stack((raw[:,0],-raw[:,2],raw[:,1]));center=src[:,:2].mean(0);ang=np.arctan2(src[:,1]-center[1],src[:,0]-center[0]);order=np.argsort(ang);ang=ang[order];src=src[order]
 boundary=[v for v in ob.data.vertices if abs(v.co.z-.9134999513626099)<1e-6 and v.co.y*side>.25]
 for v in boundary:
  a=math.atan2(v.co.y-center[1],v.co.x-center[0]);i=int(np.searchsorted(ang,a));lo=(i-1)%len(src);hi=i%len(src);a0=float(ang[lo]);a1=float(ang[hi]);aa=a
  if hi==0:a1+=2*math.pi
  if aa<a0:aa+=2*math.pi
  t=(aa-a0)/(a1-a0);target=src[lo]*(1-t)+src[hi]*t;before=list(v.co);v.co=target
  mapping.append({'newVertex':v.index,'side':label,'sourceOrderedAliasRows':[int(order[lo]),int(order[hi])],'barycentric':[1-t,t],'before':before,'target':target.tolist()})
# All geometry is new. Unused post-cut source vertices removed only within this new sculpt.
bm=bmesh.new();bm.from_mesh(ob.data);isolated=[v for v in bm.verts if not v.link_faces];bmesh.ops.delete(bm,geom=isolated,context='VERTS');bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();ob.data.update();ob.data.calc_loop_triangles()
p=np.array([list(v.co) for v in ob.data.vertices]);f=np.array([list(t.vertices) for t in ob.data.loop_triangles]);np.savez(R/'sculpt-shell01.npz',p=p,f=f,polygon=np.array([t.polygon_index for t in ob.data.loop_triangles]));(R/'cuff-correspondence-private.json').write_text(json.dumps(mapping,indent=2))
mat=bpy.data.materials.new('UNBAKED warm cloth neutral construction');mat.diffuse_color=(.48,.24,.055,1);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.48,.24,.055,1);bs.inputs['Roughness'].default_value=.86;ob.data.materials.append(mat)
for q in ob.data.polygons:q.use_smooth=True
rep={'status':'ONE_NEUTRAL_SCULPT_UNRIGGED_UNBAKED_UNACCEPTED','method':'New rounded ellipsoid/capsule anatomy joined and voxel remeshed as single garment envelope; .009mvoxel,3smoothiterations,explicitneck/hem/cuffknives. No frozen source cap, planar panel or transported tube.','vertices':len(p),'polygons':len(ob.data.polygons),'triangles':len(f),'sourceGeometryAncestry':'none; C19 joint landmarks and actual source cuff aliases only','sourceMapsSHA256':hashlib.sha256(M.read_bytes()).hexdigest(),'newCuffVerticesMapped':len(mapping),'cuffCorrespondence':'Angular source alias row interpolation (explicit two source rows plus barycentric weights per new rim vertex), no arbitrary donor proximity weld; private raw map.','boundaries':'HemZ.95; cuffsZ.913499951; neckline ellipticalknifeXcenter.6297,rx.079,ry.069; intended4boundarycycles. Actualcounts pending.','donorJoinLimits':'Cuff geometry lies on explicit donor polyline; different topology remains physically unsewn to source. Hood/hem separate retained identity reference boundaries. No socket/wrist contact claim.','topology':'Voxel-derived quad sculpt surface with knife boundary ngons, triangulated for literal/exportaudit; not deliberate animation retopology.','limits':'No rig,weights,bake,cosmetics,animation,appearance score or game-ready claim.'}
(E/'construction.json').write_text(json.dumps(rep,indent=2));bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.wm.save_as_mainfile(filepath=str(R/'sculpt-shell01.blend'));bpy.ops.export_scene.gltf(filepath=str(R/'shell01.glb'),export_format='GLB',use_selection=True,export_animations=False,export_skins=False);print(json.dumps(rep))
