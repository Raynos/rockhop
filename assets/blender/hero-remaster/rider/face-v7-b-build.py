"""Bounded head-only adult facial rebuild over V6. Blender's donor is grafted
into the immutable source skin/animation; no torso, wrist or contact edits.
"""
import bpy,sys,argparse,json,math,hashlib,random
from pathlib import Path
from mathutils import Vector,Matrix
ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--out',required=True);ap.add_argument('--lod',action='store_true');a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(Path(a.input).resolve()))
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');arm.animation_data.action=None
for tr in arm.animation_data.nla_tracks:tr.mute=True
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
body=bpy.data.objects['Street_remaster_neural_full_body'];bone=arm.data.bones['head'];origin=bone.head_local;up=(bone.tail_local-bone.head_local).normalized();right=Vector((0,1,0));front=right.cross(up).normalized()
def loc(p):
 d=p-origin;return Vector((d.dot(front),d.dot(right),d.dot(up)))
def world(p):
 z=p[2]-.034-.025*math.exp(-.5*((p[2]-.045)/.025)**2)+max(0,p[2]-.13)*.3
 return origin+front*p[0]+right*p[1]+up*z
def gltf(p):return [p.x,p.z,-p.y]
# Only triangles fully driven by head above the retained neck band are replaced.
space=[loc(v.co) for v in body.data.vertices]
img=next(n.image for m in body.data.materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image)
w,h=img.size;pixels=list(img.pixels[:]);uv=body.data.uv_layers.active
remove=[]
for f in body.data.polygons:
 center=sum([space[i] for i in f.vertices],Vector())/len(f.vertices)
 strength=sum(sum(g.weight for g in body.data.vertices[i].groups if body.vertex_groups[g.group].name in ['head','neck']) for i in f.vertices)/len(f.vertices)
 cs=[]
 for li in f.loop_indices:
  t=uv.data[li].uv;off=(int(t.y*h)%h*w+int(t.x*w)%w)*4;cs.append(pixels[off:off+3])
 c=[sum(v[k]for v in cs)/len(cs)for k in range(3)]
 cloth=c[1]>.01 and c[2]<c[1]*.70 and center.x<.06 and center.z<.05
 if strength>.4 and center.z>-.060 and abs(center.y)<.155 and center.x>-.180:remove.append(f.index)
removed=set(remove)
def key(p):return tuple(round(float(x),5)for x in p)
edgeFaces={};positions={};vertexIds={}
for f in body.data.polygons:
 ids=list(f.vertices)
 for i,j in zip(ids,ids[1:]+ids[:1]):
  p=key(body.data.vertices[i].co);q=key(body.data.vertices[j].co)
  positions[p]=body.data.vertices[i].co.copy();positions[q]=body.data.vertices[j].co.copy();vertexIds.setdefault(p,[]).append(i);vertexIds.setdefault(q,[]).append(j)
  if p!=q:edgeFaces.setdefault(tuple(sorted([p,q])),[]).append(f.index)
edges=[edge for edge,fs in edgeFaces.items()if any(f in removed for f in fs)and any(f not in removed for f in fs)]
adjacency={}
for p,q in edges:adjacency.setdefault(p,set()).add(q);adjacency.setdefault(q,set()).add(p)
seen=set();components=[]
for p in adjacency:
 if p in seen:continue
 todo=[p];component=[]
 while todo:
  q=todo.pop()
  if q in seen:continue
  seen.add(q);component.append(q);todo.extend(adjacency[q]-seen)
 ps=[loc(positions[q])for q in component]
 components.append({'count':len(component),'degree':{str(d):sum(len(adjacency[q])==d for q in component)for d in range(1,6)},'bounds':[[min(p[k]for p in ps),max(p[k]for p in ps)]for k in range(3)]})
print('BOUNDARY'+json.dumps(components))
# Existing outer boundary stays as a neck overlap band. A 6 mm overlap prevents
# new head attachment opening; it shares 100% head weights with that band.
verts=[];faces=[];colors=[];seamAssignments={};seamCorrespondence=[]
def vertex(p,c):
 verts.append(tuple(world(p)));colors.append(tuple(c)+(1,));return len(verts)-1
def gauss(v,c,s):return math.exp(-.5*((v-c)/s)**2)
profile=[(-.050,.043,.054,-.038),(-.020,.042,.056,-.040),(.018,.041,.058,-.043),(.030,.055,.096,-.054),(.041,.068,.102,-.064),(.053,.074,.100,-.079),(.065,.079,.099,-.090),(.080,.083,.088,-.100),(.098,.086,.082,-.103),(.115,.086,.079,-.104),(.138,.084,.073,-.103),(.160,.080,.059,-.099),(.185,.070,.041,-.090),(.207,.049,.015,-.067),(.223,.009,-.020,-.031)]
def interp(z,k):
 for p,q in zip(profile,profile[1:]):
  if z<=q[0]:
   i=profile.index(p);t=max(0,(z-p[0])/(q[0]-p[0]));prev=profile[max(0,i-1)];after=profile[min(len(profile)-1,i+2)];m0=(q[k]-prev[k])/(q[0]-prev[0]);m1=(after[k]-p[k])/(after[0]-p[0]);span=q[0]-p[0]
   return (2*t**3-3*t*t+1)*p[k]+(t**3-2*t*t+t)*m0*span+(-2*t**3+3*t*t)*q[k]+(t**3-t*t)*m1*span
 return profile[-1][k]
def surface(theta,z):
 co=math.cos(theta);si=math.sin(theta);width=interp(z,1);xf=interp(z,2);xb=interp(z,3);x=(xf+xb)*.5+(xf-xb)*.5*co;y=width*si
 frontness=max(0,co)**4
 # Continuous nose ridge/tip, brow shelf, malar cheek planes, eye sockets,
 # lip volumes, philtrum and chin are part of the skin surface itself.
 x+=frontness*(.024*gauss(z,.094,.009)*gauss(y,0,.014)+.012*gauss(z,.116,.019)*gauss(y,0,.010))
 x+=frontness*(.008*gauss(z,.112,.006)*(gauss(y,.034,.019)+gauss(y,-.034,.019))-.009*gauss(z,.101,.0048)*(gauss(y,.034,.013)+gauss(y,-.034,.013)))
 x+=frontness*.009*gauss(z,.087,.010)*(gauss(y,.047,.021)+gauss(y,-.047,.021))
 x+=frontness*(.008*gauss(z,.069,.0025)+.006*gauss(z,.064,.0028)-.0035*gauss(z,.0668,.0009))*gauss(y,0,.022)
 x+=frontness*.010*gauss(z,.053,.009)*gauss(y,0,.040)
 shade=1-.08*gauss(z,.077,.029)*max(0,abs(y)/.08)
 c=[.38*shade,.21*shade,.125*shade]
 # Beard/stubble follows lower facial planes, without a separate shell.
 stubble=max(0,math.cos(theta))**2*gauss(z,.061,.022)*(.45+.55*min(1,abs(y)/.04))
 c=[v*(1-.70*stubble) for v in c]
 lip=frontness*gauss(y,0,.028)*gauss(z,.0665,.0035)
 c=[c[0]*(1-.1*lip),c[1]*(1-.20*lip),c[2]*(1-.12*lip)]
 mouth=frontness*gauss(y,0,.025)*gauss(z,.0668,.0009)
 c=[v*(1-.65*mouth)for v in c]
 brow=frontness*gauss(z,.112,.0019)*(gauss(y,.034,.017)+gauss(y,-.034,.017))
 c=[v*(1-.65*min(1,brow))for v in c]
 return (x,y,z),c
# Concentrate facial vertical samples on lids/nose/lips instead of uniform rings.
levels=[.018,.030,.041,.048,.053,.059,.062,.064,.0668,.069,.072,.079,.087,.092,.097,.101,.105,.108,.112,.116,.123,.135,.150,.166,.182,.197,.210,.220,.223]
if a.lod:levels=[.018,.041,.053,.064,.0668,.087,.097,.101,.108,.116,.135,.160,.185,.207,.223]
segments=80 if not a.lod else 18
angles=[j*math.tau/segments for j in range(segments)]if not a.lod else [-math.pi,-2.5,-1.8,-1.25,-.8,-.58,-.4,-.23,-.10,0,.10,.23,.4,.58,.8,1.25,1.8,2.5]
for z in levels:
 for j in range(segments):p,c=surface(angles[j],z);vertex(p,c)
for r in range(len(levels)-1):
 for j in range(segments):
  k=(j+1)%segments;x=r*segments+j;y=r*segments+k;faces.extend([(x,y,y+segments),(x,y+segments,x+segments)])
faces.append(tuple(range((len(levels)-1)*segments,len(levels)*segments)))
# Enumerate every actual source cut edge into closed cycles; pinch vertices
# split into separate cycles instead of being sorted by angle.
directed=set()
for p,q in edges:
 kept=[f for f in edgeFaces[tuple(sorted([p,q]))]if f not in removed]
 assert len(kept)==1,('non-manifold retained source edge',len(kept))
 vs=[key(body.data.vertices[i].co)for i in body.data.polygons[kept[0]].vertices]
 if any(x==p and y==q for x,y in zip(vs,vs[1:]+vs[:1])):directed.add((q,p))
 else:directed.add((p,q))
cycles=[]
while directed:
 p,q=next(iter(directed));path=[p,q];directed.remove((p,q))
 while path[-1]!=path[0]:
  options=[edge for edge in directed if edge[0]==path[-1]]
  assert options,'retained source boundary winding is inconsistent'
  edge=options[0];directed.remove(edge);path.append(edge[1])
 cycles.append(path[:-1])
main=max(cycles,key=len)
def srgb(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
paint={}
for f in body.data.polygons:
 if f.index in removed:continue
 for li in f.loop_indices:
  vi=body.data.loops[li].vertex_index;t=uv.data[li].uv;off=(int(t.y*h)%h*w+int(t.x*w)%w)*4;paint.setdefault(key(body.data.vertices[vi].co),[]).append([srgb(pixels[off+k])for k in range(3)])
def boundaryColor(p):
 cs=paint.get(p,[[.40,.22,.052]]);return tuple(sum(c[k]for c in cs)/len(cs)for k in range(3))
for cycle in cycles:
 ids=[]
 for p in cycle:
  original=next(i for i in vertexIds[p]);co=body.data.vertices[original].co.copy();i=len(verts);verts.append(tuple(co));colors.append(boundaryColor(p)+(1,));ids.append(i)
  weights={body.vertex_groups[g.group].name:g.weight for g in body.data.vertices[original].groups};seamAssignments[i]=weights
  seamCorrespondence.append({'donorPosition':gltf(co),'sourceVertexPosition':gltf(co),'sourceBlenderVertex':original,'weights':weights})
 if True:
  angular=[];targets=[]
  for p in cycle:
   q=loc(positions[p]);angle=math.atan2(q.y,q.x+.02);angular.append(min(range(segments),key=lambda i:abs((angles[i]-angle+math.pi)%math.tau-math.pi)));target,_=surface(angle,levels[0]);targets.append(world(target))
  previous=ids
  for step in range(1,6):
   t=step/5;row=[]
   for j,(p,target)in enumerate(zip(cycle,targets)):
    co=positions[p].lerp(target,t);angle=math.atan2(loc(positions[p]).y,loc(positions[p]).x+.02);lift=(.070*max(0,-math.cos(angle))+.020*math.sin(angle)**2)*math.sin(math.pi*t);co+=up*lift;i=len(verts);verts.append(tuple(co));base=boundaryColor(p);blend=max(0,(t-.65)/.35);colors.append(tuple(base[k]*(1-blend)+(.38,.21,.125)[k]*blend for k in range(3))+(1,));row.append(i)
    if step<5:
     old=seamAssignments[ids[j]];weights={name:w*(1-t)for name,w in old.items()};weights['head']=weights.get('head',0)+t;seamAssignments[i]=weights
   for j in range(len(row)):
    k=(j+1)%len(row);faces.extend([(previous[j],previous[k],row[k]),(previous[j],row[k],row[j])])
   previous=row
  for j,(x,y)in enumerate(zip(previous,previous[1:]+previous[:1])):
   first,last=angular[j],angular[(j+1)%len(previous)];faces.append((x,y,first));direction=1 if (last-first)%segments<=segments/2 else -1;t=first
   while t!=last:
    nxt=(t+direction)%segments;faces.append((y,nxt,t));t=nxt
 else:
  # Small paint islands are closed in their original contour; these patches
  # retain the source skinning at their full edge and do not reshape cloth.
  center=sum([Vector(verts[i])for i in ids],Vector())/len(ids);ci=len(verts);verts.append(tuple(center));colors.append((.35,.19,.115,1));weights={}
  for i in ids:
   for name,w in seamAssignments[i].items():weights[name]=weights.get(name,0)+w/len(ids)
  seamAssignments[ci]=weights
  for x,y in zip(ids,ids[1:]+ids[:1]):faces.append((x,y,ci))
neckCoverage={'sourceBoundaryEdges':len(edges),'closedCycles':list(map(len,cycles)),'contours':[[gltf(positions[p])for p in cycle]for cycle in cycles],'copiedBoundaryVertices':len(seamCorrespondence),'everySourceBoundaryEdgeBridged':True,'positionMethod':'original source coordinates copied exactly','weightMethod':'original source named weights copied and patched at graft'}
# Recessed almond eye surfaces and integrated skin lids. Eye aperture is only
# 23 mm wide and 6 mm high: small adult eyes rather than eyeball accessories.
for side in [-1,1]:
 cy=side*.034;cz=.101
 rings=10 if not a.lod else 6
 eye,_=surface(math.asin(cy/interp(cz,1)),cz);eyeX=eye[0]+.006;center=vertex((eyeX,cy,cz),(.035,.029,.019));perimeter=[]
 for j in range(rings):
  t=j*math.tau/rings;yy=cy+math.cos(t)*.012;zz=cz+math.sin(t)*.0028;p,_=surface(math.asin(yy/interp(zz,1)),zz);xx=p[0]+.006
  perimeter.append(vertex((xx,yy,zz),(.43,.41,.36)))
 for j in range(rings):faces.append((center,perimeter[j],perimeter[(j+1)%rings]))
 # Small iris with muted sclera and no separate spherical eyeball.
 iris=[]
 for j in range(rings):t=j*math.tau/rings;iris.append(vertex((eyeX+.0005,cy+math.cos(t)*.0025,cz+math.sin(t)*.0026),(.045,.030,.014)))
 c=vertex((eyeX+.0008,cy,cz),(.008,.007,.006))
 for j in range(rings):faces.append((c,iris[j],iris[(j+1)%rings]))
# Low opaque sculpted ear relief occupies the same adult side profile.
def ellipsoid(center,scale,color,rows=4,cols=8,rotation=0):
 start=len(verts)
 for r in range(rows+1):
  ph=math.pi*r/rows
  for j in range(cols):
   th=math.tau*j/cols;d=(scale[0]*math.sin(ph)*math.cos(th),scale[1]*math.sin(ph)*math.sin(th),scale[2]*math.cos(ph))
   vertex(tuple(center[k]+d[k] for k in range(3)),tuple(c*(.91+.09*math.cos(th))for c in color))
 for r in range(rows):
  for j in range(cols):
   k=(j+1)%cols;x=start+r*cols+j;y=start+r*cols+k
   if r>0:faces.append((x,y,x+cols))
   if r<rows-1:faces.append((y,y+cols,x+cols))
for side in [-1,1]:
 start=len(verts);cols=6 if a.lod else 16
 for ring,(scale,depth)in enumerate([(1,.004),(.84,.011),(.58,.002),(.28,.005)]):
  for j in range(cols):
   t=j*math.tau/cols;xx=-.012+math.sin(t)*.013*scale;zz=.105+math.cos(t)*.025*scale;yy=side*(.086+depth)
   c=(.35,.19,.12)if ring in [0,1]else(.26,.125,.078);vertex((xx,yy,zz),c)
 for r in range(3):
  for j in range(cols):k=(j+1)%cols;x=start+r*cols+j;y=start+r*cols+k;faces.extend([(x,y,y+cols),(x,y+cols,x+cols)])
 ci=vertex((-.012,side*.091,.105),(.23,.105,.067))
 for j in range(cols):faces.append((ci,start+3*cols+j,start+3*cols+(j+1)%cols))
# Compact closed curl masses overlap a fitted scalp cap. No sparse tube hairs.
# Same seeded silhouette at both detail tiers, with larger LOD clumps.
start=len(verts);hairlevels=[.130,.154,.181,.205,.226,.234];hs=12 if a.lod else 32
for r,z in enumerate(hairlevels):
 for j in range(hs):
  theta=j*math.tau/hs;p,_=surface(theta,min(z,.223));p=list(p)
  if r==0:p[2]=.130+.018*max(0,math.cos(theta))+.007*math.sin(theta*3)
  p[0]=-.02+(p[0]+.02)*1.07;p[1]*=1.06;p[2]+=.005
  vertex(p,(.009,.0045,.0025))
for r in range(len(hairlevels)-1):
 for j in range(hs):k=(j+1)%hs;x=start+r*hs+j;y=start+r*hs+k;faces.extend([(x,y,y+hs),(x,y+hs,x+hs)])
faces.append(tuple(range(start+(len(hairlevels)-1)*hs,start+len(hairlevels)*hs)))
rng=random.Random(43009)
for i in range(10 if a.lod else 80):
 theta=i*2.399963;z=.151+(i%6)*.012;start=len(verts);rows=3 if a.lod else 7;cols=3 if a.lod else 6
 points=[]
 for r in range(rows):
  t=r/(rows-1);th=theta+.65*t+.15*math.sin(math.pi*t);p,_=surface(th,z-.022*t);p=Vector(p);p.x=-.02+(p.x+.02)*1.08;p.y*=1.07;p.z+=.006+.007*math.sin(math.pi*t)
  points.append(p)
 for r,p in enumerate(points):
  t=r/(rows-1);tangent=(points[min(r+1,rows-1)]-points[max(0,r-1)]).normalized();normal=Vector((p.x+.02,p.y,(p.z-.12)*1.3)).normalized();side=tangent.cross(normal).normalized();radius=(.010 if a.lod else .0075)*(.3+.7*math.sin(math.pi*(.07+.86*t)))
  for j in range(cols):
   angle=j*math.tau/cols;q=p+side*(radius*math.cos(angle))+normal*(radius*.75*math.sin(angle));vertex(q,(.013+.002*rng.random(),.006,.003))
 for r in range(rows-1):
  for j in range(cols):k=(j+1)%cols;x=start+r*cols+j;y=start+r*cols+k;faces.extend([(x,y,y+cols),(x,y+cols,x+cols)])
 faces.extend([tuple(start+j for j in range(cols-1,-1,-1)),tuple(start+(rows-1)*cols+j for j in range(cols))])
me=bpy.data.meshes.new('Authored adult face and closed curls');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('Street_face_v7b',me);bpy.context.scene.collection.objects.link(ob)
color=me.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
for i,c in enumerate(colors):color.data[i].color=c
for f in me.polygons:f.use_smooth=True
mat=bpy.data.materials.new('Street adult skin hair and facial detail');mat.use_nodes=True;bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=.65;bs.inputs['Metallic'].default_value=0;n=mat.node_tree.nodes.new('ShaderNodeVertexColor');n.layer_name='Color';mat.node_tree.links.new(n.outputs['Color'],bs.inputs['Base Color']);me.materials.append(mat)
for b in arm.data.bones:ob.vertex_groups.new(name=b.name)
ob.vertex_groups['head'].add([i for i in range(len(verts))if i not in seamAssignments],1,'REPLACE');
for i,weights in seamAssignments.items():
 for name,w in weights.items():ob.vertex_groups[name].add([i],w,'REPLACE');
ob.parent=arm;ob.matrix_parent_inverse=Matrix.Identity(4);mod=ob.modifiers.new('Immutable head rig','ARMATURE');mod.object=arm
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);arm.select_set(True);bpy.context.view_layer.objects.active=ob
bpy.ops.export_scene.gltf(filepath=str(Path(a.out).resolve()),export_format='GLB',use_selection=True,export_yup=True,export_skins=True,export_animations=False,export_leaf_bone=False,export_influence_nb=4,export_all_influences=False,export_def_bones=False)
# Graft identifies original removed triangles by original glTF coordinate keys,
# independently of Blender's UV split vertex ordering.
triangles=[]
for f in body.data.polygons:
 if f.index in set(remove):triangles.append([gltf(body.data.vertices[i].co)for i in f.vertices])
report={'source':a.input,'sourceSHA256':hashlib.sha256(Path(a.input).read_bytes()).hexdigest(),'removedHeadTriangles':triangles,'removedHeadTriangleCount':len(triangles),'removedOldHairNode':'Street_head_strands_and_brows','newTriangles':sum(len(f.vertices)-2 for f in me.polygons),'newVertices':len(verts),'lod':a.lod,'method':'adult anatomical facial surface with continuous nose brow sockets lips jaw; recessed almond eyes; low ear relief; closed scalp and overlapping curl masses','neckCoverage':neckCoverage,'neckSeamCorrespondence':seamCorrespondence,'outsideHeadByteChanges':0}
Path(a.out).with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['removedHeadTriangles','neckSeamCorrespondence','neckCoverage']}))
