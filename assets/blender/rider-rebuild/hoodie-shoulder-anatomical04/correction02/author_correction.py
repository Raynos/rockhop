"""ONE pinned local panel reparameterization + genuine original-PBR transfer.
Parent checkpoints and supplies serial CPU2 lease. Never edits original files.
"""
import hashlib,json,os,runpy,sys
from pathlib import Path
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import bpy,numpy as np
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[5]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def pin(row):
 p=ROOT/row['path'];assert sha(p)==row['sha256'],('Changed input',row['path']);return p
def curve(points):
 points=np.asarray(points,float);lengths=np.linalg.norm(np.diff(points,axis=0),axis=1)
 assert np.all(lengths>1e-9);knots=np.r_[0,np.cumsum(lengths)];knots/=knots[-1]
 def sample(t):
  i=min(len(points)-2,max(0,int(np.searchsorted(knots,t,side='right')-1)))
  u=(t-knots[i])/(knots[i+1]-knots[i]);return points[i]*(1-u)+points[i+1]*u
 return knots,sample
def panel_parameters(mesh,faceids,boundary,cornerids):
 adjacency={}
 for fi in faceids:
  ids=list(mesh.polygons[fi].vertices)
  for a,b in zip(ids,ids[1:]+ids[:1]):adjacency.setdefault(a,set()).add(b);adjacency.setdefault(b,set()).add(a)
 start=boundary.index(cornerids[0]);boundary=boundary[start:]+boundary[:start]
 offsets=[boundary.index(i)for i in cornerids]+[len(boundary)]
 assert offsets==sorted(offsets) and offsets[0]==0
 arcs=[boundary[offsets[k]:offsets[k+1]]+[boundary[offsets[k+1]%len(boundary)]]for k in range(4)]
 p=np.asarray([v.co[:]for v in mesh.vertices]);params={}
 square=np.array([[0,0],[1,0],[1,1],[0,1]],float)
 for k,arc in enumerate(arcs):
  knots,_=curve(p[arc])
  for i,t in zip(arc,knots):params[i]=square[k]*(1-t)+square[(k+1)%4]*t
 interior=sorted(set(adjacency)-set(boundary));index={v:i for i,v in enumerate(interior)}
 matrix=np.zeros((len(interior),len(interior)));rhs=np.zeros((len(interior),2))
 for v,i in index.items():
  matrix[i,i]=len(adjacency[v])
  for w in adjacency[v]:
   if w in index:matrix[i,index[w]]-=1
   else:rhs[i]+=params[w]
 solved=np.linalg.solve(matrix,rhs)
 for v,st in zip(interior,solved):params[v]=st
 assert np.all(solved>0)and np.all(solved<1)
 return params,arcs,interior
def ruled_surface(values,arcs):
 # Opposite torso/inner-sleeve U-curves define the concave underarm cloth.
 # Existing front/rear shoulder bridges remain exact at the perimeter and
 # influence their nearby support strips, rather than bulging across the void.
 _,torso=curve(values[arcs[0]]);_,sleeve=curve(values[arcs[2][::-1]])
 _,rear=curve(values[arcs[1]]);_,front=curve(values[arcs[3][::-1]])
 a,b,c,d=(values[arc[0]]for arc in arcs)
 def sample(s,t):
  base=(1-t)*torso(s)+t*sleeve(s)
  front_extra=front(t)-((1-t)*a+t*d)
  rear_extra=rear(t)-((1-t)*b+t*c)
  return base+(1-s)**4*front_extra+s**4*rear_extra
 return sample

def packed_images(obj):
 result={}
 for material in obj.data.materials:
  for node in material.node_tree.nodes:
   if node.type=='TEX_IMAGE'and node.image:
    image=node.image;assert image.packed_file
    result[sha_bytes(image.packed_file.data)]=image
 return result
def sha_bytes(data):return hashlib.sha256(data).hexdigest()

def transfer_atlas(mesh,panels,source,c,out,source_images,chart_helper):
 size=c['atlasSize'];assert size==1024
 images={k:np.asarray(img.pixels[:],dtype=np.float32).reshape(img.size[1],img.size[0],4)for k,img in source_images.items()}
 target={k:np.zeros((size,size,4),np.float32)for k in images}
 owner=np.full((size,size),-1,np.int32);sourceface=np.full_like(owner,-1)
 baryfield=np.zeros((size,size,3),np.float32);cornerfield=np.full((size,size,3),-1,np.int32)
 sourceuv=np.zeros((size,size,2),np.float32);raw=np.asarray([v.vector[:]for v in mesh.attributes['actual_donor_display_xyz'].data])
 uv=mesh.uv_layers.active;lookups={};source_dict=np.load(pin(c['selectedIntake']))
 for pi,panel in enumerate(panels):
  col,row=pi%2,pi//2
  for fi in panel['faces']:
   for lid in mesh.polygons[fi].loop_indices:
    st=panel['params'][mesh.loops[lid].vertex_index]
    uv.data[lid].uv=((col+.02+.96*st[0])/2,(row+.02+.96*st[1])/2)
  lookups[pi]=chart_helper(source_dict,panel['sourceComponent'],Matrix(c['selectedToWearerRows']))
 mesh.calc_loop_triangles()
 facepanel={fi:pi for pi,panel in enumerate(panels)for fi in panel['faces']}
 for triangle in mesh.loop_triangles:
  if triangle.polygon_index not in facepanel:continue
  pi=facepanel[triangle.polygon_index];coords=np.asarray([uv.data[lid].uv[:]for lid in triangle.loops])*size
  a,b,cc=coords;den=(b[1]-cc[1])*(a[0]-cc[0])+(cc[0]-b[0])*(a[1]-cc[1]);assert abs(den)>1e-8,'Folded/collapsed atlas triangle'
  lo=np.maximum(np.floor(coords.min(0)).astype(int),0);hi=np.minimum(np.ceil(coords.max(0)).astype(int),size-1)
  xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));x,y=xx+.5,yy+.5
  u=((b[1]-cc[1])*(x-cc[0])+(cc[0]-b[0])*(y-cc[1]))/den
  v=((cc[1]-a[1])*(x-cc[0])+(a[0]-cc[0])*(y-cc[1]))/den;w=1-u-v
  mask=(u>=-1e-8)&(v>=-1e-8)&(w>=-1e-8);xs,ys=xx[mask],yy[mask]
  weights=np.c_[u[mask],v[mask],w[mask]];identities=weights@raw[list(triangle.vertices)]
  lookup=lookups[pi]
  for px,py,identity in zip(xs,ys,identities):
   mapped,fi,bary,corners,distance=lookup(identity)
   owner[py,px]=pi;sourceface[py,px]=fi;baryfield[py,px]=bary;cornerfield[py,px]=corners;sourceuv[py,px]=mapped
 valid=owner>=0;assert valid.sum()>size*size*.85
 uvs=np.clip(sourceuv[valid],0,1)
 for key,pixels in images.items():
  h,w=pixels.shape[:2];x=uvs[:,0]*w-.5;y=uvs[:,1]*h-.5
  ix=np.floor(x).astype(int);iy=np.floor(y).astype(int);tx=(x-ix)[:,None];ty=(y-iy)[:,None]
  x0=ix%w;y0=iy%h;x1=(ix+1)%w;y1=(iy+1)%h
  target[key][valid]=(1-ty)*((1-tx)*pixels[y0,x0]+tx*pixels[y0,x1])+ty*((1-tx)*pixels[y1,x0]+tx*pixels[y1,x1])
 # Two-pixel nearest neighbor dilation protects each real chart's boundary.
 for unused in range(3):
  expanded=valid.copy()
  for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
   incoming=np.roll(valid,(dy,dx),(0,1))&~expanded
   for key in target:target[key][incoming]=np.roll(target[key],(dy,dx),(0,1))[incoming]
   for ancestry in (owner,sourceface,baryfield,cornerfield,sourceuv):ancestry[incoming]=np.roll(ancestry,(dy,dx),(0,1))[incoming]
   expanded|=incoming
  valid=expanded
 derivative={};reports=[]
 for number,(key,pixels)in enumerate(target.items()):
  original=source_images[key];image=bpy.data.images.new('ActualSelectedHoodiePanelTransfer04_'+str(number),width=size,height=size,alpha=True,float_buffer=False)
  image.colorspace_settings.name=original.colorspace_settings.name;image.pixels.foreach_set(pixels.ravel())
  image.filepath_raw=str(out/('selected-panel-map-'+str(number)+'.png'));image.file_format='PNG';image.save();image.pack()
  derivative[key]=image;reports.append({'sourcePackedSHA256':key,'sourceImage':original.name,'sourceSize':list(original.size),'derivative':image.name,'size':[size,size],'PNG_SHA256':sha(image.filepath_raw),'colorSpace':image.colorspace_settings.name})
 original_material=mesh.materials[0];material=original_material.copy();material.name='ActualSelectedHoodiePanelTransfer04_PBR'
 for node in material.node_tree.nodes:
  if node.type=='TEX_IMAGE'and node.image:
   key=sha_bytes(node.image.packed_file.data);assert key in derivative;node.image=derivative[key]
 slot=len(mesh.materials);mesh.materials.append(material)
 for panel in panels:
  for fi in panel['faces']:mesh.polygons[fi].material_index=slot
 np.savez_compressed(out/'actual-panel-texel-source-ancestry.npz',panel=owner,selectedFace=sourceface,selectedTriangleCorners=cornerfield,barycentric=baryfield,originalUV=sourceuv)
 return reports

def actual_components(mesh,faceids):
 edgefaces={}
 for fi in faceids:
  vs=list(mesh.polygons[fi].vertices)
  for a,b in zip(vs,vs[1:]+vs[:1]):edgefaces.setdefault(tuple(sorted((a,b))),[]).append(fi)
 graph={fi:set()for fi in faceids}
 for fs in edgefaces.values():
  for fi in fs:graph[fi].update(fs)
 remaining=set(faceids);result=[]
 while remaining:
  group=set();stack=[min(remaining)]
  while stack:
   fi=stack.pop()
   if fi in group:continue
   group.add(fi);stack.extend(graph[fi]-group)
  remaining-=group;result.append(sorted(group))
 return result

def main():
 args=sys.argv[sys.argv.index('--')+1:];assert len(args)==2
 cp,out=(Path(x).resolve()for x in args);c=json.loads(cp.read_text())
 assert not out.exists()and out.is_relative_to(ROOT/'harness/out/rider-rebuild/hoodie-shoulder-anatomical04')
 pins=[v for v in c.values()if isinstance(v,dict)and'path'in v and'sha256'in v]
 for row in pins:pin(row)
 previous=json.loads(pin(c['incomingAuthorReceipt']).read_text())
 dump=np.load(pin(c['savedPanelsIntake']));source_controls=json.loads(pin(c['originalPanelControls']).read_text())
 bpy.ops.wm.open_mainfile(filepath=str(pin(c['incomingNative'])))
 obj=bpy.data.objects['Hoodie__RiderHoodie'];mesh=obj.data;body=bpy.data.objects['RiderBody'];rig=bpy.data.objects['RiderSkeleton']
 helpers=runpy.run_path(str(pin(c['baseAuthorHelpers'])));prior_helpers=runpy.run_path(str(pin(c['previousAuthor'])))
 before_body=helpers['signature'](body,rig);assert before_body==previous['bodyAnd75RigSignature']
 assert np.array_equal(np.asarray([v.co[:]for v in mesh.vertices]),dump['vertices'])
 original_ids=np.asarray([v.value for v in mesh.attributes['_panel04_original_vertex_id'].data]);byold={int(old):i for i,old in enumerate(original_ids)if old>=0}
 faces=np.asarray([v.value for v in mesh.attributes['_panel04_original_face_id'].data]);newfaces=np.flatnonzero(faces==-1).tolist()
 groups=actual_components(mesh,newfaces);assert len(groups)==4 and len(newfaces)==1547
 old_uv=np.asarray([v.uv[:]for v in mesh.uv_layers.active.data]);old_materials=[p.material_index for p in mesh.polygons]
 old_fields=[[tuple((g.group,g.weight))for g in v.groups]for v in mesh.vertices]
 old_topology=[tuple(p.vertices)for p in mesh.polygons];old_positions=np.asarray([v.co[:]for v in mesh.vertices])
 raw=np.asarray([v.vector[:]for v in mesh.attributes['actual_donor_display_xyz'].data]);original_raw=raw.copy()
 source_images=packed_images(obj);assert len(source_images)==2
 assert all(list(image.size)==[4096,4096]for image in source_images.values())
 assert all(node.extension=='REPEAT'and node.interpolation=='Linear'for mat in mesh.materials for node in mat.node_tree.nodes if node.type=='TEX_IMAGE')
 dense=bpy.data.objects['Hoodie__ActualOriginalDensePBR_FrozenFitContext'];assert set(source_images)==set(packed_images(dense))
 panels=[];changed=[]
 for controls in c['panels']:
  spec=next(x for x in source_controls['components']if x['label']==controls['component'])
  boundary=[byold[i]for i in spec['boundaryVertexIds']];boundaryset=set(boundary)
  candidates=[fs for fs in groups if boundaryset<=set(v for fi in fs for v in mesh.polygons[fi].vertices)]
  assert len(candidates)==1;faceids=candidates[0]
  corners=[byold[i]for i in controls['anatomicalCornerOriginalVertexIds']]
  params,arcs,interior=panel_parameters(mesh,faceids,boundary,corners)
  shape=ruled_surface(old_positions,arcs);identity=ruled_surface(original_raw,arcs)
  for vi in interior:
   assert original_ids[vi]==-1,'Retained garment points cannot enter this interior solve'
   s,t=params[vi];new=shape(float(s),float(t));mesh.vertices[vi].co=new
   raw[vi]=identity(float(s),float(t));mesh.attributes['actual_donor_display_xyz'].data[vi].vector=raw[vi]
   changed.append({'vertex':vi,'component':controls['component'],'before':old_positions[vi].tolist(),'after':new.tolist(),'panelCoordinates':params[vi].tolist()})
  panels.append({'label':controls['component'],'faces':faceids,'params':params,'sourceComponent':spec,'corners':controls['anatomicalCornerOriginalVertexIds'],'newInteriorVertexIds':interior})
 mesh.update()
 assert len(changed)==1423 and len({r['vertex']for r in changed})==1423
 assert [tuple(p.vertices)for p in mesh.polygons]==old_topology
 assert [[tuple((g.group,g.weight))for g in v.groups]for v in mesh.vertices]==old_fields
 assert np.array_equal(np.asarray([v.co[:]for v in mesh.vertices])[original_ids>=0],old_positions[original_ids>=0])
 assert np.array_equal(np.asarray([v.vector[:]for v in mesh.attributes['actual_donor_display_xyz'].data])[original_ids>=0],original_raw[original_ids>=0])
 assert helpers['signature'](body,rig)==before_body
 out.mkdir(parents=True)
 shape_native=out/'authored-panel-shape-before-transfer.blend';bpy.ops.wm.save_as_mainfile(filepath=str(shape_native),compress=True)
 # Recoverable real geometry saved before texture work. Prior UVs are still
 # explicitly invalid here; only the final transferred native is for PBR review.
 mapreports=transfer_atlas(mesh,panels,None,c,out,source_images,prior_helpers['source_chart'])
 for name in ('_panel04_selected_face_id','_panel04_selected_barycentric','_panel04_selected_corner_0','_panel04_selected_corner_1','_panel04_selected_corner_2'):
  mesh.attributes[name].name=name.replace('_panel04_','_panel04_prior_')
 newface_set=set(newfaces)
 for fi,p in enumerate(mesh.polygons):
  if fi not in newface_set:
   assert p.material_index==old_materials[fi]
   for lid in p.loop_indices:assert np.array_equal(np.asarray(mesh.uv_layers.active.data[lid].uv),old_uv[lid])
 assert helpers['signature'](body,rig)==before_body
 assert set(source_images)<set(packed_images(obj))
 assert not body.hide_render and not body.hide_get()and not obj.hide_render
 visible=sorted(o.name for o in bpy.context.scene.objects if o.type=='MESH'and not o.hide_render)
 assert visible==previous['visibleMeshes'] and len(visible)==7
 obj['contextStatus']='ONE_ANATOMICAL_PANEL_REPARAMETERIZATION_AND_ACTUAL_PBR_TRANSFER_UNREVIEWED'
 obj['panelCorrectionRecipeSHA256']=sha(__file__);obj['panelCorrectionControlsSHA256']=sha(cp);obj['acceptedArt']=False
 native=out/'selected-panel-outfit.blend';bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
 (out/'changed-panel-vertices.json').write_text(json.dumps(changed,indent=2)+'\n')
 receipt={'accepted':False,'stage':'ACTUAL_ANATOMICAL_PANEL_AND_ORIGINAL_PBR_TRANSFER_SAVED','native':{'path':str(native.relative_to(ROOT)),'sha256':sha(native)},'recipeSHA256':sha(__file__),'controlsSHA256':sha(cp),'geometryBeforeTransfer':{'path':str(shape_native.relative_to(ROOT)),'sha256':sha(shape_native)},'incomingNative':c['incomingNative'],'bodyAnd75RigSignature':before_body,'bodyAnd75RigUnchanged':True,'visibleMeshes':visible,'targetObject':obj.name,'changedInteriorClothVertices':len(changed),'allRetainedClothPositionsUnchanged':True,'quadConnectivityAndFullFieldsUnchanged':True,'originalUVsAndMaterialsOutsidePanelsExact':True,'actualSourceTransferMaps':mapreports,'panels':[{'label':p['label'],'actualFaces':p['faces'],'anatomicalCornerOriginalVertexIds':p['corners'],'actualInteriorVertexIds':p['newInteriorVertexIds']}for p in panels],'limits':['Construction is a single local anatomical seam solve, not proven ease or clearance; parent judges actual clothed views.','Small genuine derivative original-PBR transfer atlas is for first review; same ancestry supports later increased resolution.','No body projection, mean-inset retry, fold-gain sweep, weight conditioning, motion acceptance or player export. All R0–R5 open.']}
 (out/'author.json').write_text(json.dumps(receipt,indent=2)+'\n')
 for row in pins:pin(row)
 print('ACTUAL_ANATOMICAL_PANEL_AND_SOURCE_PBR_TRANSFER_SAVED',flush=True)
if __name__=='__main__':main()
