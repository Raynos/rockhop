"""One new drafted raglan/gusset prototype. No source torso geometry or rigging."""
import bpy,bmesh,math,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/drafted-raglan');E=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/drafted-raglan')
bpy.ops.wm.read_factory_settings(use_empty=True)
# Front/back panel coordinates are (lateral Y,height Z). Anatomical landmark source is C19 joint heads.
# Raglan seam = neck .08/1.49 to axilla .19/1.26, not frozen donor shoulder edge.
verts=[];faces=[];panelids=[];lookup={}
def vertex(co):
 key=tuple(round(v,7) for v in co)
 if key not in lookup:lookup[key]=len(verts);verts.append(tuple(co))
 return lookup[key]
def panel(poly,name):
 points=[Vector(p) for p in poly]
 for tri in tessellate_polygon([points]):
  a,b,c=[points[t] if isinstance(t,int) else t for t in tri];n=5;grid={}
  for i in range(n+1):
   for j in range(n+1-i):grid[i,j]=vertex(a+(b-a)*(i/n)+(c-a)*(j/n))
  for i in range(n):
   for j in range(n-i):
    faces.append((grid[i,j],grid[i+1,j],grid[i,j+1]));panelids.append(name)
    if i+j<n-1:faces.append((grid[i+1,j],grid[i+1,j+1],grid[i,j+1]));panelids.append(name)
def depth(y,z,front):
 lateral=abs(y)
 t=max(0,min(1,(z-.96)/.53))
 torso=(.755+.04*t) if front else (.54-.04*t)
 sleeve=(.72) if front else (.555)
 w=max(0,min(1,(lateral-.13)/.14))
 return torso*(1-w)+sleeve*w
def p(y,z,front):return (depth(y,z,front),y,z)
# Explicit central torso panels, each sleeve panel shares raglan seam vertex IDs.
central=[(-.19,.96),(.19,.96),(.19,1.26),(.08,1.49),(0,1.435),(-.08,1.49),(-.19,1.26)]
sleeve=[(.08,1.49),(.245,1.485),(.32,1.20),(.385,.925),(.315,.925),(.26,1.14),(.245,1.28),(.19,1.26)]
for front in (True,False):
 c=central.copy()
 if not front:c[4]=(0,1.49)
 panel([p(y,z,front) for y,z in c],('front' if front else 'back')+' torso')
 for side in (-1,1):panel([p(side*y,z,front) for y,z in sleeve],('front' if front else 'back')+' raglan '+str(side))
# Sew torso side, shoulder/sleeve outer, and sleeve inner strips.
for side in (-1,1):
 strips=[[(.19,.96),(.19,1.26)],[(.08,1.49),(.245,1.485),(.32,1.20),(.385,.925)],[(.315,.925),(.26,1.14),(.245,1.28)]]
 for k,line in enumerate(strips):
  for a,b in zip(line,line[1:]):panel([p(side*a[0],a[1],True),p(side*b[0],b[1],True),p(side*b[0],b[1],False),p(side*a[0],a[1],False)],'sewn side '+str(side)+' '+str(k))
 # Deliberate gusset spans axilla torso and inner raglan corners, sharing all four seam edges.
 # Subdivide center to allow sag without detached overlay.
 A=p(side*.19,1.26,True);B=p(side*.245,1.28,True);C=p(side*.245,1.28,False);D=p(side*.19,1.26,False)
 G=(sum(x[0] for x in [A,B,C,D])/4,side*.2175,1.235)
 for a,b in [(A,B),(B,C),(C,D),(D,A)]:panel([a,b,G],'underarm gusset '+str(side))
me=bpy.data.meshes.new('New drafted raglan sewn topology');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('UNACCEPTED unrigged drafted raglan gusset01',me);bpy.context.collection.objects.link(ob)
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
mat=bpy.data.materials.new('UNBAKED plain warm cloth construction');mat.diffuse_color=(.48,.24,.055,1);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.48,.24,.055,1);bs.inputs['Roughness'].default_value=.86;me.materials.append(mat)
for f in me.polygons:f.use_smooth=True
# Report unsmoothed authored topology. Do not soften failures with cosmetic iterations.
edgecounts={}
for f in faces:
 for a,b in zip(f,f[1:]+f[:1]):edgecounts[tuple(sorted((a,b)))]=edgecounts.get(tuple(sorted((a,b))),0)+1
adj=[set() for _ in verts]
for a,b in edgecounts:adj[a].add(b);adj[b].add(a)
seen=set();components=0
for a in range(len(verts)):
 if a in seen:continue
 components+=1;todo=[a];seen.add(a)
 while todo:
  for b in adj[todo.pop()]:
   if b not in seen:seen.add(b);todo.append(b)
np.savez(R/'drafted-shell01.npz',p=np.array(verts),f=np.array(faces),panel=np.array(panelids))
rep={'status':'UNACCEPTED_ONE_NEUTRAL_UNRIGGED_UNBAKED_PROTOTYPE','method':'Independently drafted central front/back and raglan sleeve panels, explicitly sewn side strips plus depressed diamond underarm gusset. All shell vertices newly authored; no donor torso/cap/strip geometry.','sourceGeometryAncestry':'none; C19 bone heads measured for landmark scale only','vertices':len(verts),'triangles':len(faces),'components':components,'boundaryEdges':sum(n==1 for n in edgecounts.values()),'nonmanifoldEdges':sum(n>2 for n in edgecounts.values()),'panels':{n:panelids.count(n) for n in sorted(set(panelids))},'seamPolicy':'Common rounded coordinate IDs welded before export; raglan seams are physical shared edges, gusset shares four perimeter edges. Neck/hem/two cuffs intentional openings.','limits':['Original hood and cuff joining not physically sewn: separate protected identity reference donors.','Literal shell crossings and donor-shell contacts pending audit; zero counts not assumed.','No rig, skin weights, poses, texture bake, garment detail, mobile or game-ready claim.','Neutral authored rest cannot prove deformation or appearance acceptance.']}
(E/'construction.json').write_text(json.dumps(rep,indent=2))
bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.wm.save_as_mainfile(filepath=str(R/'drafted-shell01.blend'));bpy.ops.export_scene.gltf(filepath=str(R/'shell01.glb'),export_format='GLB',use_selection=True,export_animations=False,export_skins=False)
print(json.dumps(rep))
