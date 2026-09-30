"""Retopologize terminal forearms between measured body/glove open contours.
No contact vertex moves; source data outside the two local joins stays intact.
"""
import bpy,sys,json,math,argparse,hashlib,struct
from pathlib import Path
from collections import Counter,defaultdict
from mathutils import Vector,Matrix
import numpy as np
ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--out',required=True);ap.add_argument('--lod',action='store_true');a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(Path(a.input).resolve()))
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');arm.animation_data.action=None
for tr in arm.animation_data.nla_tracks:tr.mute=True
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
body=next(o for o in bpy.data.objects if o.type=='MESH' and 'neural' in o.name);contact=bpy.data.objects['Authored_grips_and_soles']
# Blender's coordinate conversion can shift a float by an ulp at the weld
# rounding boundary. Recover exact source positions before topology mapping.
from mathutils.kdtree import KDTree
raw=Path(a.input).read_bytes();jn=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+jn]);binary=raw[28+jn:]
for o in [body,contact]:
 node=next(n for n in doc['nodes'] if n.get('name')==o.name);pr=doc['meshes'][node['mesh']]['primitives'][0];ac=doc['accessors'][pr['attributes']['POSITION']];bv=doc['bufferViews'][ac['bufferView']];offset=bv.get('byteOffset',0)+ac.get('byteOffset',0);stride=bv.get('byteStride',12);ps=[];kd=KDTree(ac['count'])
 for i in range(ac['count']):
  x,y,z=struct.unpack_from('<3f',binary,offset+i*stride);p=Vector((x,-z,y));ps.append(p);kd.insert(p,i)
 kd.balance()
 for v in o.data.vertices:
  _,i,dist=kd.find(v.co);assert dist<.000003,(o.name,dist);v.co=ps[i]
 o.data.update()
def key(p):return tuple(round(v,5) for v in p)
def gltf(p):return [p.x,p.z,-p.y]
def weights(o,i):return {o.vertex_groups[g.group].name:g.weight for g in o.data.vertices[i].groups if g.weight>1e-7}
def mergews(ws):
 r=defaultdict(float)
 for w in ws:
  for n,x in w.items():r[n]+=x/len(ws)
 s=sum(r.values());return {n:x/s for n,x in r.items()}
def weld(o):
 ix={};ps=[];orig=defaultdict(list);vix=[]
 for v in o.data.vertices:
  k=key(v.co)
  if k not in ix:ix[k]=len(ps);ps.append(v.co.copy())
  j=ix[k];vix.append(j);orig[j].append(v.index)
 return ps,vix,orig
def boundaries(o,deleted):
 ps,ix,orig=weld(o);edges=Counter();seenfaces=set()
 for f in o.data.polygons:
  if f.index in deleted:continue
  vs=[ix[i] for i in f.vertices]
  if len(set(vs))<3:continue
  fk=tuple(sorted(vs))
  if fk in seenfaces:continue
  seenfaces.add(fk)
  if (ps[vs[1]]-ps[vs[0]]).cross(ps[vs[2]]-ps[vs[0]]).length<1e-10:continue
  for i,j in zip(vs,vs[1:]+vs[:1]):
   if i!=j:edges[tuple(sorted((i,j)))]+=1
 adj=defaultdict(set)
 for (i,j),n in edges.items():
  if n==1:adj[i].add(j);adj[j].add(i)
 seen=set();out=[]
 for i in adj:
  if i in seen:continue
  todo=[i];seen.add(i);comp=[]
  while todo:
   j=todo.pop();comp.append(j)
   for k in adj[j]:
    if k not in seen:seen.add(k);todo.append(k)
  if len(comp)>=3:out.append({'ids':comp,'centre':sum((ps[j] for j in comp),Vector())/len(comp),'degree':Counter(len(adj[j]) for j in comp),'ps':ps,'orig':orig,'adj':adj})
 return out
image=next(n.image for ma in body.data.materials if ma and ma.use_nodes for n in ma.node_tree.nodes if n.type=='TEX_IMAGE' and n.image);w,h=image.size;pix=np.empty(w*h*4,np.float32);image.pixels.foreach_get(pix);pix=pix.reshape(h,w,4)
colour_samples=defaultdict(list)
for f in body.data.polygons:
 for li in f.loop_indices:
  i=body.data.loops[li].vertex_index;uv=body.data.uv_layers.active.data[li].uv;c=pix[min(h-1,max(0,int(uv.y*h))),min(w-1,max(0,int(uv.x*w))),:3]
  # Image texels are sRGB; glTF vertex colours are linear.
  c=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4);colour_samples[i].append(c)
verts=[];faces=[];skin=[];colours=[];deleted=set();boundarypatch=[];sides=[];seams=[]
def ordered(loop,basisA,basisB):
 c=loop['centre'];angle=lambda i:math.atan2((loop['ps'][i]-c).dot(basisB),(loop['ps'][i]-c).dot(basisA))
 first=min(loop['ids'],key=angle);neighbors=list(loop['adj'][first]);second=min(neighbors,key=lambda i:(angle(i)-angle(first))%math.tau)
 ids=[first,second]
 while True:
  nxt=next(i for i in loop['adj'][ids[-1]] if i!=ids[-2])
  if nxt==first:break
  assert nxt not in ids,'closed contour self-revisit';ids.append(nxt)
 assert len(ids)==len(loop['ids']),'complete closed actual edge cycle'
 return ids
def orient_boundary(o,deleted,loop,ids,opposite):
 # Read the actual source triangle winding. A zipper has a forward first-row
 # edge and a backward final-row edge; orient complete rows, never individual
 # faces, so every internal zipper edge is shared with opposite directions.
 ps,ix,_=weld(o);directions=defaultdict(list)
 for f in o.data.polygons:
  if f.index in deleted:continue
  vs=[ix[i] for i in f.vertices]
  for i,j in zip(vs,vs[1:]+vs[:1]):
   if i!=j:directions[tuple(sorted((i,j)))].append(1 if i<j else -1)
 signs=[]
 for i,j in zip(ids,ids[1:]+ids[:1]):
  ds=directions[tuple(sorted((i,j)))];assert len(ds)==1,(o.name,i,j,ds)
  signs.append(ds[0]*(1 if i<j else -1))
 assert len(set(signs))==1,(o.name,'source boundary winding',Counter(signs))
 if (signs[0]>0)==opposite:ids=[ids[0]]+list(reversed(ids[1:]))
 return ids
for side in ['L','R']:
 b=arm.data.bones['forearm.'+side];elbow=b.head_local;wrist=b.tail_local;axis=(wrist-elbow).normalized();cut=-.10
 doomed=set()
 for f in body.data.polygons:
  p=f.center;rel=p-wrist;u=rel.dot(axis);rad=(rel-axis*u).length
  amount=sum(sum(g.weight for g in body.data.vertices[i].groups if body.vertex_groups[g.group].name in ['forearm.'+side,'hand.'+side]) for i in f.vertices)/len(f.vertices)
  if amount>.60 and u>cut and rad<.105:doomed.add(f.index)
 deleted.update(doomed)
 bs=boundaries(body,doomed);start=min((l for l in bs if (l['centre']-wrist).length<.18 and len(l['ids'])>=3),key=lambda l:abs((l['centre']-wrist).dot(axis)-cut));assert dict(start['degree'])=={2:len(start['ids'])},start['degree']
 gs=boundaries(contact,set());end=min((l for l in gs if (l['centre']-wrist).length<.08 and max(l['ps'][i].x for i in l['ids'])-min(l['ps'][i].x for i in l['ids'])<.0001),key=lambda l:(l['centre']-wrist).length);assert dict(end['degree'])=={2:len(end['ids'])},end['degree']
 A=Vector((0,1,0));A=(A-axis*A.dot(axis)).normalized();B=axis.cross(A).normalized();EA=Vector((0,1,0));EB=Vector((0,0,1))
 startids=orient_boundary(body,doomed,start,ordered(start,A,B),True);endids=orient_boundary(contact,set(),end,ordered(end,EA,EB),False)
 rows=[];startws=[];startcs=[];endws=[]
 for l,ids,targetws in [(start,startids,startws),(end,endids,endws)]:
  for i in ids:
   o=body if l is start else contact;ids0=l['orig'][i];ws=mergews([weights(o,j) for j in ids0]);targetws.append(ws)
   if l is start:
    colour=sum((np.mean(colour_samples[j],axis=0) for j in ids0))/len(ids0);startcs.append(tuple(float(x) for x in colour))
    boundarypatch.append({'position':gltf(l['ps'][i]),'weights':ws})
 def addrow(points,ws,cs):
  row=[]
  for p,ww,c in zip(points,ws,cs):row.append(len(verts));verts.append(tuple(p));skin.append(ww);colours.append(tuple(c)+(1,))
  rows.append(row)
 addrow([start['ps'][i] for i in startids],startws,startcs)
 # One cross-section only in full; LOD uses the same actual endpoint contours.
 if not a.lod:
  N=32;points=[];ws=[];cs=[];t=.55;c0=start['centre'];c3=end['centre'];length=(c3-c0).length;c1=c0+axis*length*.4;c2=c3-Vector((1,0,0))*length*.18
  centre=c0*(1-t)**3+c1*(3*(1-t)**2*t)+c2*(3*(1-t)*t*t)+c3*t**3
  tangent=((c1-c0)*3*(1-t)**2+(c2-c1)*6*(1-t)*t+(c3-c2)*3*t*t).normalized();MA=(EA-tangent*EA.dot(tangent)).normalized();MB=tangent.cross(MA).normalized()
  for j in range(N):
   theta=-math.pi+j*math.tau/N;si=min(range(len(startids)),key=lambda k:abs(math.atan2(math.sin(math.atan2((start['ps'][startids[k]]-c0).dot(B),(start['ps'][startids[k]]-c0).dot(A))-theta),math.cos(math.atan2((start['ps'][startids[k]]-c0).dot(B),(start['ps'][startids[k]]-c0).dot(A))-theta))))
   ei=min(range(len(endids)),key=lambda k:abs(math.atan2(math.sin(math.atan2((end['ps'][endids[k]]-c3).dot(EB),(end['ps'][endids[k]]-c3).dot(EA))-theta),math.cos(math.atan2((end['ps'][endids[k]]-c3).dot(EB),(end['ps'][endids[k]]-c3).dot(EA))-theta))))
   sp=start['ps'][startids[si]]-c0;ep=end['ps'][endids[ei]]-c3;ra=(abs(sp.dot(A)) if abs(math.cos(theta))>.3 else .03)*(1-t)+(abs(ep.dot(EA)) if abs(math.cos(theta))>.3 else .037)*t;rb=.027*(1-t)+.013*t
   # Bounded anatomical wrist taper, measured from the two contours.
   radius0=sp.length;radius1=ep.length;radius=radius0*(1-t)+radius1*t
   points.append(centre+(MA*math.cos(theta)+MB*math.sin(theta))*radius)
   ww=defaultdict(float)
   for n,x in startws[si].items():ww[n]+=x*(1-t)
   for n,x in endws[ei].items():ww[n]+=x*t
   ws.append(dict(ww));cs.append(startcs[si])
  addrow(points,ws,cs)
 endcols=[startcs[min(range(len(startids)),key=lambda k:abs(k/len(startids)-j/len(endids)))] for j in range(len(endids))]
 addrow([end['ps'][i] for i in endids],endws,endcols)
 # Zipper triangulation joins every endpoint, with no nearest-point snap.
 for ra,rb in zip(rows,rows[1:]):
  i=j=0
  while i<len(ra) or j<len(rb):
   ia=ra[i%len(ra)];ib=rb[j%len(rb)]
   if j==len(rb) or (i<len(ra) and (i+1)/len(ra)<=(j+1)/len(rb)):
    faces.append((ia,ra[(i+1)%len(ra)],ib));i+=1
   else:faces.append((ia,rb[(j+1)%len(rb)],ib));j+=1
 seams.append({'side':side,'body':{'sourceVertices':[start['orig'][i] for i in startids],'sourcePositions':[gltf(start['ps'][i]) for i in startids],'bridgeVertices':rows[0]},'glove':{'sourceVertices':[end['orig'][i] for i in endids],'sourcePositions':[gltf(end['ps'][i]) for i in endids],'bridgeVertices':rows[-1]}})
 sides.append({'side':side,'cutAxisMetres':cut,'bodyContourVertices':len(startids),'gloveContourVertices':len(endids),'removedTriangles':len(doomed),'startCentre':gltf(start['centre']),'gloveCentre':gltf(end['centre']),'endpointSpanMetres':(end['centre']-start['centre']).length})
# Row winding is coherent and matches both directed original boundaries.
me=bpy.data.meshes.new('Measured anatomical wrist retopology');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('Street_continuous_wrists',me);bpy.context.scene.collection.objects.link(ob)
for f in me.polygons:f.use_smooth=True
ca=me.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
for i,c in enumerate(colours):ca.data[i].color=c
ma=bpy.data.materials.new('Wrist skin matched to existing forearm');ma.use_nodes=True;bs=ma.node_tree.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=.78;bs.inputs['Metallic'].default_value=0;n=ma.node_tree.nodes.new('ShaderNodeVertexColor');n.layer_name='Color';ma.node_tree.links.new(n.outputs['Color'],bs.inputs['Base Color']);me.materials.append(ma)
for b in arm.data.bones:ob.vertex_groups.new(name=b.name)
for i,ws in enumerate(skin):
 ws=dict(sorted(ws.items(),key=lambda x:-x[1])[:4]);total=sum(ws.values())
 for name,x in ws.items():ob.vertex_groups[name].add([i],x/total,'REPLACE')
ob.parent=arm;ob.matrix_parent_inverse=Matrix.Identity(4);mod=ob.modifiers.new('Same original19joint skin','ARMATURE');mod.object=arm
bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);arm.select_set(True);bpy.context.view_layer.objects.active=ob
bpy.ops.export_scene.gltf(filepath=str(Path(a.out).resolve()),export_format='GLB',use_selection=True,export_yup=True,export_skins=True,export_animations=False,export_leaf_bone=False,export_influence_nb=4,export_all_influences=False,export_def_bones=False)
removed=[sorted([gltf(body.data.vertices[i].co) for i in f.vertices]) for f in body.data.polygons if f.index in deleted]
report={'source':str(Path(a.input).resolve()),'sourceSHA256':hashlib.sha256(Path(a.input).read_bytes()).hexdigest(),'removedTrianglePositions':removed,'bodyBoundaryWeightPatches':boundarypatch,'extraTriangles':len(faces),'sides':sides,'seams':seams,'method':'Actual closed body/glove boundary contour zipper retopology; body seam weights averaged across UV duplicates, glove endpoint weights copied, anatomical interpolation; no contact positions changed.'}
Path(a.out).with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['removedTrianglePositions','bodyBoundaryWeightPatches','seams']}))
